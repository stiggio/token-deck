import { heartbeat, jpegChunk, refresh, withReportId, batHeader, PAYLOAD } from './protocol'

export type QueueWriter = (packet: Buffer) => Promise<void>

export type PaintRequest = {
  tiles: Map<number, Buffer>
  force: boolean
}

/**
 * One item at a time, and an item is a whole frame group.
 * At most one pending paint: a newer JPEG replaces a key that has not started.
 */
export class FrameQueue {
  private tail: Promise<void> = Promise.resolve()
  private lastSent = new Map<number, Buffer>()
  private pending: {
    tiles: Map<number, Buffer>
    force: boolean
    started: boolean
    promise: Promise<void>
    resolve: () => void
    reject: (e: unknown) => void
  } | null = null

  constructor(private readonly write: QueueWriter) {}

  clearLastSent(): void {
    this.lastSent.clear()
  }

  submit<T>(task: () => Promise<T>): Promise<T> {
    const run = this.tail.then(task, task)
    this.tail = run.then(
      () => undefined,
      () => undefined
    )
    return run
  }

  command(payload: Buffer): Promise<void> {
    return this.submit(async () => {
      await this.write(withReportId(payload))
    })
  }

  heartbeat(): Promise<void> {
    return this.command(heartbeat())
  }

  /** Changed tiles plus one STP. `force` resends even when the bytes match. */
  paint(tiles: Map<number, Buffer>, force = false): Promise<void> {
    if (this.pending && !this.pending.started) {
      for (const [key, jpeg] of tiles) this.pending.tiles.set(key, jpeg)
      if (force) this.pending.force = true
      return this.pending.promise
    }
    let resolve!: () => void
    let reject!: (e: unknown) => void
    const promise = new Promise<void>((res, rej) => {
      resolve = res
      reject = rej
    })
    const job = {
      tiles: new Map(tiles),
      force,
      started: false,
      promise,
      resolve,
      reject
    }
    this.pending = job
    void this.submit(async () => {
      job.started = true
      if (this.pending === job) this.pending = null
      try {
        await this.writePaint(job.tiles, job.force)
        job.resolve()
      } catch (err) {
        job.reject(err)
        throw err
      }
    })
    return promise
  }

  /** Key 1 again, even when unchanged, then STP. */
  keepalive(jpeg: Buffer | null): Promise<void> {
    if (!jpeg) return Promise.resolve()
    return this.paint(new Map([[1, jpeg]]), true)
  }

  private async writePaint(tiles: Map<number, Buffer>, force: boolean): Promise<void> {
    let sent = false
    const keys = [...tiles.keys()].sort((a, b) => a - b)
    for (const key of keys) {
      const jpeg = tiles.get(key)
      if (!jpeg) continue
      const prev = this.lastSent.get(key)
      if (!force && prev && prev.equals(jpeg)) continue
      await this.writeTile(key, jpeg)
      this.lastSent.set(key, Buffer.from(jpeg))
      sent = true
    }
    if (sent) await this.write(withReportId(refresh()))
  }

  private async writeTile(key: number, jpeg: Buffer): Promise<void> {
    await this.write(withReportId(batHeader(jpeg.length, key)))
    for (let off = 0; off < jpeg.length; off += PAYLOAD) {
      await this.write(withReportId(jpegChunk(jpeg, off)))
    }
  }
}

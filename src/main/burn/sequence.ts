import { batHeader, brightness, heartbeat, jpegChunk, logHeader, PAYLOAD, qucmd, refresh, wake, withReportId } from '../deck/protocol'
import { jpegInfo } from '../deck/jpeg'

export const MAX_WELCOME_BYTES = 22307

export function validateWelcome(jpeg: Buffer): void {
  if (jpeg.length > MAX_WELCOME_BYTES) throw new Error(`welcome JPEG is ${jpeg.length} bytes`)
  const info = jpegInfo(jpeg)
  if (!info.baseline) throw new Error('welcome JPEG must be baseline')
  if (info.width !== 240 || info.height !== 320) {
    throw new Error(`welcome JPEG is ${info.width}×${info.height}`)
  }
}

export type BurnDriver = {
  write(packet: Buffer): Promise<void>
  sleep(ms: number): Promise<void>
  waitForLogReport(timeoutMs: number): Promise<boolean>
}

export type BurnResult = 'ok' | 'failed'

/**
 * Section 9 step 4, from the handshake through the hold.
 * The caller opens a fresh handle and waits the 8 s settle.
 * A missing write report sends no refresh.
 */
export async function executeBurn(
  driver: BurnDriver,
  args: { brightness: number; tiles: Buffer[]; welcome: Buffer; repaint?: Buffer[]; holdMs?: number }
): Promise<BurnResult> {
  if (args.tiles.length !== 6) throw new Error('burn needs six tiles')
  validateWelcome(args.welcome)
  const write = (payload: Buffer) => driver.write(withReportId(payload))
  await write(wake())
  await write(brightness(args.brightness))
  await write(qucmd())
  await write(brightness(args.brightness))
  await driver.sleep(500)
  for (let i = 0; i < 6; i++) {
    const jpeg = args.tiles[i]!
    await write(batHeader(jpeg.length, i + 1))
    for (let off = 0; off < jpeg.length; off += PAYLOAD) await write(jpegChunk(jpeg, off))
  }
  await write(refresh())
  await driver.sleep(1000)
  await write(logHeader(args.welcome.length))
  for (let off = 0; off < args.welcome.length; off += PAYLOAD) await write(jpegChunk(args.welcome, off))
  const ok = await driver.waitForLogReport(10000)
  if (!ok) return 'failed'
  await write(refresh())
  await driver.sleep(1000)
  const after = args.repaint ?? args.tiles
  for (let i = 0; i < 6; i++) {
    const jpeg = after[i]!
    await write(batHeader(jpeg.length, i + 1))
    for (let off = 0; off < jpeg.length; off += PAYLOAD) await write(jpegChunk(jpeg, off))
  }
  await write(refresh())
  const hold = args.holdMs ?? 10000
  await write(heartbeat())
  let elapsed = 0
  while (elapsed < hold) {
    const slice = Math.min(10000, hold - elapsed)
    await driver.sleep(slice)
    elapsed += slice
    if (elapsed < hold) await write(heartbeat())
  }
  return 'ok'
}

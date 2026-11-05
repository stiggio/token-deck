import fs from 'fs'
import path from 'path'
import { resource } from '../paths'
import { WELCOME_HASH } from '../deck/geometry'

export type BurnRecord = { serial: string; imageHash: string; at: string }

export const IMAGE_HASH = WELCOME_HASH

export function readJsonRecords(file: string): BurnRecord[] {
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter((row): row is BurnRecord => !!row && typeof row.serial === 'string' && row.serial.length > 0)
  } catch {
    return []
  }
}

export function shippedRecords(): BurnRecord[] {
  return readJsonRecords(resource('preburned.json'))
}

export function localBatchFile(): string {
  return path.join(process.env.HOME || process.env.USERPROFILE || '', '.tokendeck', 'preburned.json')
}

export function localBatchRecords(): BurnRecord[] {
  return readJsonRecords(localBatchFile())
}

export function appendLocalBatch(record: BurnRecord): void {
  const file = localBatchFile()
  fs.mkdirSync(path.dirname(file), { recursive: true })
  const rows = readJsonRecords(file)
  rows.push(record)
  fs.writeFileSync(file, JSON.stringify(rows, null, 2))
}

export function isRecorded(serial: string, store: BurnRecord[]): boolean {
  if (!serial) return false
  return (
    store.some((r) => r.serial === serial) ||
    shippedRecords().some((r) => r.serial === serial) ||
    localBatchRecords().some((r) => r.serial === serial)
  )
}

/** One automatic write per deck. An empty serial is never automatic. Two failures stop the automatic path. */
export function shouldAutoBurn(serial: string, store: BurnRecord[], failures: number, enabled: boolean): boolean {
  if (!enabled || !serial || failures >= 2) return false
  return !isRecorded(serial, store)
}

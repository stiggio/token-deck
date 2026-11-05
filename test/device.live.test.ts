import { spawn } from 'child_process'
import { devicesAsync, HIDAsync } from 'node-hid'
import { describe, expect, it } from 'vitest'
import { renderTile } from '../src/main/deck/render'
import { handshake, parseFirmware, withReportId, clearKey, refresh, jpegChunk, batHeader, PAYLOAD } from '../src/main/deck/protocol'
import { matchDevice } from '../src/main/deck/transport'

const live = process.env.TOKENDECK_DEVICE === '1'

describe.skipIf(!live)('deck on this Mac', () => {
  it('handshakes, paints a q100 tile, and refuses a second exclusive open', async () => {
    const found = (await devicesAsync()).filter(matchDevice)
    expect(found.length).toBeGreaterThan(0)
    const device = found[0]!
    expect(device.path).toBeTruthy()
    const handle = await HIDAsync.open(device.path!)
    const reports: string[] = []
    handle.on('data', (data: Buffer) => {
      reports.push(Buffer.from(data).subarray(0, 16).toString('hex'))
    })
    let firmware = 'n/a'
    try {
      firmware = parseFirmware(Buffer.from(await handle.getFeatureReport(1, 20))) || firmware
    } catch {
      /* try the other report */
    }
    try {
      firmware = parseFirmware(Buffer.from(await handle.getFeatureReport(0, 513))) || firmware
    } catch {
      /* node-hid may not support this read */
    }
    console.log(`identity ${device.manufacturer} ${device.product} serial=${device.serialNumber} release=${device.release} firmware=${firmware}`)
    for (const frame of handshake(70)) await handle.write(withReportId(frame))
    const jpeg = await renderTile({ kind: 'test' }, 1)
    console.log(`test tile ${jpeg.length} bytes`)
    for (let key = 1; key <= 6; key++) {
      await handle.write(withReportId(batHeader(jpeg.length, key)))
      for (let off = 0; off < jpeg.length; off += PAYLOAD) await handle.write(withReportId(jpegChunk(jpeg, off)))
    }
    await handle.write(withReportId(refresh()))
    const second = await new Promise<string>((resolve) => {
      const child = spawn(process.execPath, ['-e', "const {HIDAsync}=require('node-hid'); HIDAsync.open(process.env.DECK_PATH).then(()=>{console.log('OPENED'); process.exit(0)}).catch(e=>{console.log(String(e&&e.message||e)); process.exit(1)})"], {
        cwd: process.cwd(),
        env: { ...process.env, DECK_PATH: device.path }
      })
      let out = ''
      child.stdout.on('data', (chunk) => { out += chunk })
      child.stderr.on('data', (chunk) => { out += chunk })
      child.on('exit', () => resolve(out))
    })
    console.log(`second open: ${second.trim()}`)
    expect(second.includes('0xE00002C5') || /exclusive/i.test(second)).toBe(true)
    await handle.write(withReportId(clearKey(1)))
    await handle.write(withReportId(refresh()))
    await handle.write(withReportId(batHeader(jpeg.length, 1)))
    for (let off = 0; off < jpeg.length; off += PAYLOAD) await handle.write(withReportId(jpegChunk(jpeg, off)))
    await handle.write(withReportId(refresh()))
    await new Promise((resolve) => setTimeout(resolve, 1500))
    console.log(`reports after handshake ${reports.length}`)
    await handle.close()
  }, 30000)
})

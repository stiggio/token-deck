import fs from 'fs'
import { devicesAsync, HIDAsync } from 'node-hid'
import { executeBurn } from './burn/sequence'
import { appendLocalBatch, IMAGE_HASH, isRecorded, localBatchRecords } from './burn/records'
import { matchDevice, vendorRunning } from './deck/transport'
import { parseFirmware } from './deck/protocol'
import { resource } from './paths'

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function probe(): Promise<void> {
  const list = (await devicesAsync()).filter(matchDevice)
  if (!list.length) {
    console.log('no Stream Dock vendor interface found')
    return
  }
  for (const device of list) {
    console.log(`${device.manufacturer || ''} ${device.product || ''} serial=${device.serialNumber || ''} release=${device.release} path=${device.path}`)
    if (!device.path) continue
    try {
      const handle = await HIDAsync.open(device.path)
      let firmware = 'n/a'
      if (process.platform === 'darwin') {
        try {
          firmware = parseFirmware(Buffer.from(await handle.getFeatureReport(0, 513))) || firmware
        } catch {
          /* node-hid often cannot read the vendor string */
        }
      }
      console.log(`firmware ${firmware}`)
      await handle.close()
    } catch (err) {
      console.log(`open failed ${err}`)
    }
  }
}

export async function burnWatch(): Promise<void> {
  if (vendorRunning()) {
    console.log('Quit the StreamDock or VSD Craft app to use Token Deck.')
    return
  }
  console.log('burn --watch. Unplug a deck when it says so. Ctrl-C prints the summary.')
  const burned: string[] = []
  const failed: string[] = []
  let stop = false
  process.on('SIGINT', () => {
    stop = true
    console.log(`summary burned ${burned.join(',') || 'none'} failed ${failed.join(',') || 'none'}`)
    process.exit(0)
  })
  let blockedSerial = ''
  while (!stop) {
    const list = (await devicesAsync()).filter(matchDevice)
    const device = list[0]
    if (!device) {
      blockedSerial = ''
      await sleep(2000)
      continue
    }
    const serial = device.serialNumber || ''
    const identity = `${device.manufacturer || ''} ${device.product || ''} serial=${serial || 'none'} release=${device.release}`
    if (!serial) {
      console.log(`${identity} no serial`)
      await waitUntilGone()
      continue
    }
    if (blockedSerial && blockedSerial !== serial) {
      await sleep(500)
      continue
    }
    const seen = localBatchRecords().filter((row) => row.serial === serial)
    if (seen.length > 1) console.log(`\x1b[31mduplicate serial ${serial}\x1b[0m`)
    if (isRecorded(serial, [])) {
      console.log(`${identity} already burned, unplug`)
      await waitUntilGone()
      continue
    }
    console.log(`${identity} waiting 8s`)
    await sleep(8000)
    const again = (await devicesAsync()).filter(matchDevice)[0]
    if (!again?.path || (again.serialNumber || '') !== serial) continue
    const handle = await HIDAsync.open(again.path)
    let firmware = 'n/a'
    if (process.platform === 'darwin') {
      try {
        firmware = parseFirmware(Buffer.from(await handle.getFeatureReport(0, 513))) || 'n/a'
      } catch {
        firmware = 'n/a'
      }
    }
    console.log(`firmware ${firmware}`)
    const tiles = [1, 2, 3, 4, 5, 6].map((key) => fs.readFileSync(resource('welcome-tiles', `key${key}.jpg`)))
    const welcome = fs.readFileSync(resource('welcome-sent.jpg'))
    let report: (() => void) | null = null
    handle.on('data', (data: Buffer) => {
      const buf = Buffer.from(data)
      if (buf[0] === 0x41 && buf[9] === 0x00) report?.()
    })
    const result = await executeBurn(
      {
        write: async (packet) => {
          await handle.write(packet)
        },
        sleep,
        waitForLogReport: (ms) =>
          new Promise((resolve) => {
            const timer = setTimeout(() => resolve(false), ms)
            report = () => {
              clearTimeout(timer)
              resolve(true)
            }
          })
      },
      { brightness: 70, tiles, welcome, repaint: tiles, holdMs: 10000 }
    )
    await handle.close()
    if (result === 'ok') {
      const row = { serial, imageHash: IMAGE_HASH, at: new Date().toISOString() }
      appendLocalBatch(row)
      burned.push(serial)
      blockedSerial = ''
      console.log(`${identity} done, unplug and plug the next`)
    } else {
      failed.push(serial)
      blockedSerial = serial
      console.log('\x1b[31mFAILED: this deck may now start black. Unplug it and plug it back in to retry.\x1b[0m')
    }
    await waitUntilGone()
  }
}

async function waitUntilGone(): Promise<void> {
  for (;;) {
    const list = (await devicesAsync()).filter(matchDevice)
    if (!list.length) return
    await sleep(500)
  }
}

export async function calibrate(): Promise<void> {
  console.log('This replaces the welcome screen until calibration ends')
  console.log('Calibration is a CLI for a deck with other firmware. It is not run on the development unit from the app.')
  console.log(`Ruler bytes: ${resource('calib-ruler-240x320.jpg')}`)
}

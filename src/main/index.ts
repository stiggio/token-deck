import { app, BrowserWindow, Menu, Tray, dialog, ipcMain, nativeImage, powerMonitor, shell } from 'electron'
import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { autoUpdater } from 'electron-updater'
import { createCanvas } from '@napi-rs/canvas'
import { getHidapiVersion } from 'node-hid'
import { WELCOME_HASH } from './deck/geometry'
import { resource } from './paths'
import { burnWatch, calibrate, probe } from './cli'
import { Log } from './log'
import { openStore } from './settings/store'
import { DeckTransport } from './deck/transport'
import { HookServer } from './hooks/server'
import { ClaudeCode } from './integrations/claude-code'
import { CodexIntegration, restoreCodex } from './integrations/codex'
import { OpenCodeIntegration } from './integrations/opencode'
import { LaunchOnly } from './integrations/launch'
import { Controller } from './modes/controller'
import { MODE_EXAMPLE, watchModes } from './modes/custom'
import { shouldAutoBurn, shippedRecords } from './burn/records'
import { accessibilityTrusted, askAutomation } from './system/focus'
import type { AgentId } from '../shared/model'
import type { IpcCall, Snapshot } from '../shared/ipc'

const smoke = process.argv.includes('--smoke')
const cli = ['burn', 'probe', 'calibrate'].find((arg) => process.argv.includes(arg))

if (smoke) {
  void app.whenReady().then(async () => {
    try {
      console.log(getHidapiVersion())
      const canvas = createCanvas(64, 64)
      await canvas.encode('jpeg', { quality: 100 })
      for (const file of [
        'welcome-320x240.png',
        'welcome-sent.jpg',
        'welcome-tiles/key1.jpg',
        'welcome-tiles/key2.jpg',
        'welcome-tiles/key3.jpg',
        'welcome-tiles/key4.jpg',
        'welcome-tiles/key5.jpg',
        'welcome-tiles/key6.jpg',
        'panel-geometry.json',
        'preburned.json'
      ]) {
        if (!fs.existsSync(resource(file))) throw new Error(`missing ${file}`)
      }
      const hash = crypto.createHash('sha256').update(fs.readFileSync(resource('welcome-sent.jpg'))).digest('hex')
      if (hash !== WELCOME_HASH) throw new Error(`welcome hash ${hash}`)
      app.exit(0)
    } catch (err) {
      console.error(err)
      app.exit(2)
    }
  })
} else if (cli) {
  void app.whenReady().then(async () => {
    if (!app.requestSingleInstanceLock()) {
      console.log('Quit Token Deck first: the tray app owns the deck.')
      app.exit(1)
      return
    }
    try {
      if (cli === 'probe') await probe()
      else if (cli === 'calibrate') await calibrate()
      else await burnWatch()
      app.exit(0)
    } catch (err) {
      console.error(err)
      app.exit(1)
    }
  })
} else {
  const locked = app.requestSingleInstanceLock()
  if (!locked) app.quit()
  else void app.whenReady().then(start)
}

async function start(): Promise<void> {
  app.dock?.hide()
  app.setAppUserModelId('io.stigg.tokendeck')
  const log = new Log()
  const store = openStore()
  const claude = new ClaudeCode(store, (line) => log.write(line))
  const codex = new CodexIntegration(store, (line) => log.write(line))
  const opencode = new OpenCodeIntegration(store)
  const launch = {
    cursor: new LaunchOnly('cursor', 'Cursor'),
    amp: new LaunchOnly('amp', 'Visual Studio Code'),
    devin: new LaunchOnly('devin', 'Devin', 'https://app.devin.ai')
  }
  await Promise.all([claude.detect(), codex.detect(), opencode.detect(), launch.cursor.detect(), launch.amp.detect(), launch.devin.detect()])
  let window: BrowserWindow | null = null
  let tray: Tray | null = null
  let lastTiles: Buffer[] = []
  let updateVersion: string | null = null
  let quitting = false
  let shutdownCap = 3000
  let wizardOpen = !store.get('wizardDone')
  const transport = new DeckTransport()
  transport.brightness = store.get('brightness')
  transport.keepalive = store.get('repaintKeepalive')
  transport.log = (line) => log.write(line)
  transport.setKnobMap(store.get('knobMap'))
  transport.shouldBurn = (serial) => shouldAutoBurn(serial, store.get('burnedSerials'), store.get('burnFailures')[serial] || 0, store.get('autoBurn'))
  transport.onBurned = (serial) => {
    const rows = store.get('burnedSerials').filter((row) => row.serial !== serial)
    rows.push({ serial, imageHash: WELCOME_HASH, at: new Date().toISOString() })
    store.set('burnedSerials', rows)
    const failures = { ...store.get('burnFailures') }
    delete failures[serial]
    store.set('burnFailures', failures)
    void dialog.showMessageBox({ message: 'Welcome screen written to the deck.', buttons: ['OK'] })
    broadcast()
  }
  transport.onBurnFailed = (serial) => {
    if (!serial) return
    const failures = { ...store.get('burnFailures') }
    failures[serial] = (failures[serial] || 0) + 1
    store.set('burnFailures', failures)
    void dialog.showMessageBox({ message: 'The welcome screen was not written. Unplug the deck and plug it back in.', buttons: ['OK'] })
    broadcast()
  }
  const controller = new Controller(
    store,
    claude,
    codex,
    opencode,
    launch,
    async (frames, force) => {
      lastTiles = frames.map((frame) => frame || Buffer.alloc(0))
      await transport.paint(frames, force)
      broadcast()
    },
    (line) => log.write(line),
    async () => {
      const result = await dialog.showMessageBox({
        type: 'question',
        message: 'Allow full access on the next session?',
        buttons: ['Cancel', 'Allow full access'],
        defaultId: 0,
        cancelId: 0
      })
      return result.response === 1
    }
  )
  controller.onConnect = () => openWindow()
  transport.onInput = (event) => void controller.handle(event)
  transport.onState = () => {
    void controller.render(true)
    broadcast()
  }
  transport.currentTiles = () => lastTiles.filter((buf) => buf.length > 0)
  claude.onChange = () => void controller.render(false)
  codex.onChange = () => void controller.render(false)
  opencode.onChange = () => void controller.render(false)
  const hooks = new HookServer(store, (event) => {
    if (event.source === 'claude' || event.source === 'statusline') claude.ingest(event)
  }, (line) => log.write(line))
  await hooks.start()
  claude.start()
  if (codex.bin) void codex.start()
  opencode.start()
  watchModes(() => void controller.render(true))
  app.setLoginItemSettings({ openAtLogin: store.get('startAtLogin') })

  const welcomePng = `data:image/png;base64,${fs.readFileSync(resource('welcome-320x240.png')).toString('base64')}`

  function openWindow(): void {
    if (window && !window.isDestroyed()) {
      window.show()
      return
    }
    window = new BrowserWindow({
      width: 960,
      height: 640,
      show: false,
      backgroundColor: '#131512',
      title: 'Token Deck',
      webPreferences: {
        preload: path.join(__dirname, '../preload/index.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true
      }
    })
    window.on('close', (event) => {
      if (quitting) return
      event.preventDefault()
      window?.hide()
    })
    const devUrl = process.env.ELECTRON_RENDERER_URL
    if (devUrl) void window.loadURL(devUrl)
    else void window.loadFile(path.join(__dirname, '../renderer/index.html'))
    window.once('ready-to-show', () => window?.show())
  }

  function snapshot(): Snapshot {
    const device = transport.snapshot()
    const serial = device.info?.serial || ''
    const failures = serial ? store.get('burnFailures')[serial] || 0 : 0
    return {
      version: app.getVersion(),
      device: {
        phase: device.phase,
        message: device.message,
        manufacturer: device.info?.manufacturer || '',
        product: device.info?.product || '',
        serial,
        release: device.info ? String(device.info.release) : '',
        firmware: device.info?.firmware || transport.firmware,
        burnFailed: device.burnFailed
      },
      mode: controller.mode,
      brightness: store.get('brightness'),
      keepalive: store.get('repaintKeepalive'),
      autoBurn: store.get('autoBurn'),
      startAtLogin: store.get('startAtLogin'),
      agents: [
        row('claude-code', !!claude.bin, claude.signedIn, claude.hooksInstalled, claude.statusChained, true, claude.version),
        row('codex', !!codex.bin, codex.signedIn, false, false, !!codex.bin, codex.signedIn ? 'app-server' : 'TUI visibility not checked this launch'),
        row('opencode', !!opencode.bin, false, false, false, opencode.reachable, opencode.version),
        row('cursor', launch.cursor.installed, false, false, false, false, ''),
        row('amp', launch.amp.installed, false, false, false, false, ''),
        row('devin', true, false, false, false, false, 'app.devin.ai')
      ],
      favorites: store.get('favorites'),
      efforts: { 'claude-code': ['low', 'medium', 'high', 'xhigh'], codex: codex.models[0]?.efforts || [], opencode: [] },
      modes: controller.modes().map((mode) => ({ name: mode.name, file: mode.file, errors: mode.errors })),
      example: JSON.stringify(MODE_EXAMPLE, null, 2),
      burned: store.get('burnedSerials'),
      preburned: shippedRecords().some((record) => record.serial === serial),
      burnMessage: failures >= 2 ? 'Token Deck could not write the welcome screen to this deck.' : '',
      welcomePng,
      tiles: lastTiles.map((buf) => (buf.length ? `data:image/jpeg;base64,${buf.toString('base64')}` : '')),
      wizard: wizardOpen ? { step: store.get('wizardStep'), open: true, notes: [] } : null,
      knobsCalibrated: store.get('knobsCalibrated'),
      accessibility: accessibilityTrusted(false),
      updateVersion,
      log: log.tail(),
      modelNamesUpper: store.get('modelNamesUpper')
    }
  }

  function broadcast(): void {
    window?.webContents.send('td-state', snapshot())
    rebuildTray()
  }

  function rebuildTray(): void {
    if (!tray) return
    const mode = controller.mode === 'models' ? 'Models & Usage' : controller.mode === 'sessions' ? 'Sessions' : controller.mode === 'agents' ? 'Agents' : 'Agents'
    tray.setContextMenu(Menu.buildFromTemplate([
      { label: 'Token Deck', click: openWindow },
      { label: `Mode: ${mode}`, enabled: false },
      { label: 'Open settings…', click: openWindow },
      { label: 'Check for updates', click: () => void checkUpdates(true) },
      { type: 'separator' },
      { label: 'Quit', click: () => app.quit() }
    ]))
  }

  const icon = trayImage()
  tray = new Tray(icon)
  tray.setToolTip('Token Deck')
  rebuildTray()
  tray.on('click', openWindow)

  ipcMain.handle('td', async (_event, call: IpcCall) => {
    await dispatch(call)
    broadcast()
    return snapshot()
  })

  async function dispatch(call: IpcCall): Promise<void> {
    if (call.method === 'brightness') {
      store.set('brightness', call.value)
      await transport.setBrightness(call.value)
    } else if (call.method === 'keepalive') {
      store.set('repaintKeepalive', call.value)
      transport.keepalive = call.value
    } else if (call.method === 'autoBurn') store.set('autoBurn', call.value)
    else if (call.method === 'login') {
      store.set('startAtLogin', call.value)
      app.setLoginItemSettings({ openAtLogin: call.value })
    } else if (call.method === 'testPattern') {
      const jpeg = await (await import('./deck/render')).renderTile({ kind: 'test' }, 1)
      await transport.paint([jpeg, jpeg, jpeg, jpeg, jpeg, jpeg], true)
    } else if (call.method === 'connect') await connectAgent(call.id)
    else if (call.method === 'disconnect') disconnect(call.id)
    else if (call.method === 'restore') {
      if (call.id === 'claude-code') claude.restore()
      if (call.id === 'codex') restoreCodex()
      await claude.detect()
    } else if (call.method === 'favorites') {
      const favorites = store.get('favorites')
      favorites[call.agent] = call.models.slice(0, 6)
      store.set('favorites', favorites)
      await controller.render(true)
    } else if (call.method === 'reloadModes') await controller.render(true)
    else if (call.method === 'openModes') {
      const { modesDir } = await import('./modes/custom')
      await shell.openPath(modesDir())
    } else if (call.method === 'burn') {
      const confirm = await dialog.showMessageBox({
        message: 'Write the welcome screen to this deck again?',
        buttons: ['Cancel', 'Write welcome screen to deck'],
        defaultId: 0,
        cancelId: 0
      })
      if (confirm.response === 1) await transport.rewrite()
    } else if (call.method === 'exportWelcome') {
      const target = await dialog.showSaveDialog({ defaultPath: 'token-deck-welcome.jpg' })
      if (!target.canceled && target.filePath) {
        const { loadImage, createCanvas } = await import('@napi-rs/canvas')
        const image = await loadImage(resource('welcome-320x240.png'))
        const canvas = createCanvas(320, 240)
        const ctx = canvas.getContext('2d')
        ctx.drawImage(image, 0, 0, 320, 240)
        fs.writeFileSync(target.filePath, Buffer.from(await canvas.encode('jpeg', { quality: 97 })))
      }
    } else if (call.method === 'checkUpdates') await checkUpdates(true)
    else if (call.method === 'updateNow') await installUpdate()
    else if (call.method === 'showLog') await shell.openPath(log.file)
    else if (call.method === 'wizard') {
      if (call.skip) store.set('wizardStep', Math.min(6, call.step + 1))
      else store.set('wizardStep', call.step)
      if (store.get('wizardStep') >= 6) {
        store.set('wizardDone', true)
        wizardOpen = false
      }
    } else if (call.method === 'wizardAsk') await askAutomation()
    else if (call.method === 'simulator') {
      const event = call.event
      if (event.type === 'key' && event.key) await controller.handle({ type: 'key', key: event.key as 1 | 2 | 3 | 4 | 5 | 6 })
      if (event.type === 'metal' && event.which) await controller.handle({ type: 'metal', which: event.which as 'left' | 'middle' | 'right', pressed: !!event.pressed })
      if (event.type === 'knob' && event.which && event.action) {
        await controller.handle({ type: 'knob', which: event.which as 'main' | 'left' | 'right', action: event.action as 'cw' | 'ccw' | 'click' })
      }
    }
  }

  async function connectAgent(id: AgentId): Promise<void> {
    if (id === 'claude-code') {
      const notes = await claude.install()
      log.write(notes.join(' '))
      if (controller.mode === 'idle') controller.mode = store.get('mode')
    } else if (id === 'codex') await codex.start()
    else if (id === 'opencode') opencode.start()
    else if (id === 'cursor' || id === 'amp' || id === 'devin') await launch[id].launch()
    await controller.render(true)
  }

  function disconnect(id: AgentId): void {
    if (id === 'codex') codex.stop()
    if (id === 'opencode') opencode.stop()
  }

  async function checkUpdates(manual: boolean): Promise<void> {
    if (process.platform !== 'darwin' || __SIGNED__) {
      try {
        await autoUpdater.checkForUpdates()
      } catch (err) {
        log.write(`updater ${err}`)
      }
      return
    }
    try {
      const response = await fetch('https://github.com/stiggio/token-deck/releases/latest/download/latest-mac.yml')
      if (!response.ok) return
      const text = await response.text()
      const version = text.match(/^version:\s*(\S+)/m)?.[1]
      if (version && version !== app.getVersion()) {
        updateVersion = version
        if (manual) {
          const result = await dialog.showMessageBox({
            message: `Token Deck ${version} is available.`,
            buttons: ['Later', 'Update now'],
            defaultId: 1,
            cancelId: 0
          })
          if (result.response === 1) await installUpdate()
        }
      }
    } catch (err) {
      log.write(`update check ${err}`)
    }
  }

  async function installUpdate(): Promise<void> {
    if (process.platform === 'darwin' && !__SIGNED__) {
      const child = await import('child_process')
      const proc = child.spawn('/bin/bash', ['-c', 'curl -fsSL https://usage.stigg.io/install.sh | /bin/bash'], {
        detached: true,
        stdio: 'ignore'
      })
      proc.unref()
      return
    }
    autoUpdater.quitAndInstall()
  }

  autoUpdater.autoDownload = true
  autoUpdater.autoInstallOnAppQuit = false
  autoUpdater.on('update-available', (info) => {
    updateVersion = info.version
    broadcast()
  })
  autoUpdater.on('update-downloaded', (info) => {
    updateVersion = info.version
    void dialog.showMessageBox({ message: `Token Deck ${info.version} is available.`, buttons: ['Later', 'Update now'] }).then((result) => {
      if (result.response === 1) autoUpdater.quitAndInstall()
    })
  })

  powerMonitor.on('resume', () => {
    void transport.reconnect()
  })
  powerMonitor.on('shutdown', () => {
    shutdownCap = 1000
  })
  app.on('before-quit', (event) => {
    if (quitting) return
    event.preventDefault()
    quitting = true
    void (async () => {
      const crops = [1, 2, 3, 4, 5, 6].map((key) => fs.readFileSync(resource('welcome-tiles', `key${key}.jpg`)))
      await transport.prepareQuit({ paint: transport.burnFailed ? null : crops, capMs: shutdownCap })
      await hooks.stop()
      app.exit(0)
    })()
  })
  app.on('window-all-closed', () => undefined)
  app.on('second-instance', () => openWindow())

  transport.start()
  await controller.render(true)
  if (wizardOpen) openWindow()
  void checkUpdates(false)
  setInterval(() => broadcast(), 2000)
  log.write('Token Deck ready')
}

function row(id: AgentId, installed: boolean, signedIn: boolean, hooks: boolean, statusLine: boolean, reachable: boolean, detail: string) {
  return { id, installed, signedIn, hooks, statusLine, reachable, detail }
}

function trayImage() {
  const file = resource('trayTemplate.png')
  if (fs.existsSync(file)) return nativeImage.createFromPath(file)
  return nativeImage.createEmpty()
}

import fs from 'fs'
import path from 'path'

export function resourcesRoot(): string {
  if (process.env.TOKENDECK_RESOURCES) return process.env.TOKENDECK_RESOURCES
  try {
    if (!process.versions.electron) throw new Error('not-electron')
    const electron = require('electron') as { app?: { isPackaged: boolean; getAppPath: () => string } }
    const app = electron.app
    if (app?.isPackaged) return path.join(process.resourcesPath, 'resources')
    if (app?.getAppPath) {
      const candidate = path.join(app.getAppPath(), 'resources')
      if (fs.existsSync(candidate)) return candidate
    }
  } catch {
    /* not in electron */
  }
  const fromHere = path.resolve(__dirname, '../../resources')
  if (fs.existsSync(fromHere)) return fromHere
  const fromOut = path.resolve(__dirname, '../../../resources')
  if (fs.existsSync(fromOut)) return fromOut
  return path.resolve(process.cwd(), 'resources')
}

export function resource(...parts: string[]): string {
  return path.join(resourcesRoot(), ...parts)
}

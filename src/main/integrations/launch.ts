import fs from 'fs'
import { execFile } from 'child_process'
import { focusSession, launchInTerminal, openApp, openUrl } from '../system/focus'
import { which } from '../system/which'
import type { AgentId } from '../../shared/model'

export class LaunchOnly {
  installed = false
  constructor(readonly id: AgentId, private readonly app: string, private readonly url?: string) {}

  capabilities() {
    return { launch: true, sessions: false, context: false, usage: false, model: false, effort: false, permission: false, ultracode: false }
  }

  async detect(): Promise<void> {
    if (this.id === 'devin') {
      this.installed = true
      return
    }
    if (process.platform === 'darwin') {
      const name = this.id === 'cursor' ? 'Cursor.app' : 'Visual Studio Code.app'
      this.installed = fs.existsSync(`/Applications/${name}`) || fs.existsSync(`${process.env.HOME}/Applications/${name}`)
      if (!this.installed) this.installed = !!(await which(this.id === 'cursor' ? 'cursor' : 'code'))
      return
    }
    this.installed = true
  }

  async launch(): Promise<void> {
    if (this.url) {
      await openUrl(this.url)
      return
    }
    if (this.id === 'amp') {
      const code = await which('code')
      if (code) {
        await new Promise<void>((resolve) => execFile(code, ['--reuse-window'], () => resolve()))
        return
      }
    }
    try {
      await openApp(this.app)
    } catch {
      await launchInTerminal(this.id === 'cursor' ? 'cursor' : 'code')
    }
  }

  async focus(): Promise<void> {
    await this.launch()
    await focusSession({ app: this.app, bundleId: this.id === 'cursor' ? 'com.todesktop.230313mzl4w4u92' : 'com.microsoft.VSCode' })
  }
}

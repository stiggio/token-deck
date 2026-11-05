import type { IpcCall, Snapshot } from '../shared/ipc'

declare global {
  interface Window {
    tokenDeck: {
      invoke: (call: IpcCall) => Promise<Snapshot | string | boolean | null>
      onState: (listener: (snapshot: Snapshot) => void) => () => void
    }
  }
}

export {}

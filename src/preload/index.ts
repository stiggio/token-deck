import { contextBridge, ipcRenderer } from 'electron'
import type { IpcCall, Snapshot } from '../shared/ipc'

contextBridge.exposeInMainWorld('tokenDeck', {
  invoke: (call: IpcCall) => ipcRenderer.invoke('td', call),
  onState: (listener: (snapshot: Snapshot) => void) => {
    const wrapped = (_event: unknown, snapshot: Snapshot) => listener(snapshot)
    ipcRenderer.on('td-state', wrapped)
    return () => ipcRenderer.removeListener('td-state', wrapped)
  }
})

/**
 * Preload script - exposes safe APIs to renderer
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
    setClickThrough: (clickThrough) => ipcRenderer.invoke('set-click-through', clickThrough)
});

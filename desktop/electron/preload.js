/**
 * Preload script - exposes safe APIs to renderer
 * 
 * Provides IPC bridge for:
 * - Settings management
 * - Window controls
 * - Mouse/cursor tracking
 * - Maid switching
 * - Expressions and actions
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Window
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
    setClickThrough: (clickThrough) => ipcRenderer.invoke('set-click-through', clickThrough),
    
    // Settings
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    
    // Cursor tracking
    getCursorPosition: () => ipcRenderer.invoke('get-cursor-position'),
    getScreenSize: () => ipcRenderer.invoke('get-screen-size'),
    
    // Event listeners from main process
    onSettingsLoaded: (callback) => {
        ipcRenderer.on('settings-loaded', (event, settings) => callback(settings));
    },
    onSwitchMaid: (callback) => {
        ipcRenderer.on('switch-maid', (event, maidId) => callback(maidId));
    },
    onSetZoom: (callback) => {
        ipcRenderer.on('set-zoom', (event, zoom) => callback(zoom));
    },
    onSetMovementMode: (callback) => {
        ipcRenderer.on('set-movement-mode', (event, mode) => callback(mode));
    },
    onAutoHideChanged: (callback) => {
        ipcRenderer.on('auto-hide-changed', (event, autoHide) => callback(autoHide));
    },
    onTriggerExpression: (callback) => {
        ipcRenderer.on('trigger-expression', (event, expression) => callback(expression));
    },
    onTriggerAction: (callback) => {
        ipcRenderer.on('trigger-action', (event, action) => callback(action));
    }
});

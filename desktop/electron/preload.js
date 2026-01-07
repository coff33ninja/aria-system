/**
 * Preload script - exposes safe APIs to renderer
 * 
 * Provides IPC bridge for:
 * - Settings management
 * - Window controls
 * - Mouse/cursor tracking
 * - Maid switching
 * - Expressions and actions
 * - Multi-monitor support
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Window
    getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
    setClickThrough: (clickThrough) => ipcRenderer.invoke('set-click-through', clickThrough),
    
    // Settings
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    resetSettings: () => ipcRenderer.invoke('reset-settings'),
    getSettingsPath: () => ipcRenderer.invoke('get-settings-path'),
    openSettingsFolder: () => ipcRenderer.invoke('open-settings-folder'),
    exportSettings: () => ipcRenderer.invoke('export-settings'),
    importSettings: () => ipcRenderer.invoke('import-settings'),
    
    // Cursor tracking
    getCursorPosition: () => ipcRenderer.invoke('get-cursor-position'),
    getScreenSize: () => ipcRenderer.invoke('get-screen-size'),
    
    // Multi-monitor
    getMonitors: () => ipcRenderer.invoke('get-monitors'),
    moveToMonitor: (index) => ipcRenderer.invoke('move-to-monitor', index),
    
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
    },
    
    // Debug Panel event listeners
    onDebugParameterUpdate: (callback) => {
        ipcRenderer.on('debug-parameter-update', (event, data) => callback(data));
    },
    onDebugViewportUpdate: (callback) => {
        ipcRenderer.on('debug-viewport-update', (event, data) => callback(data));
    },
    onDebugAnimationCommand: (callback) => {
        ipcRenderer.on('debug-animation-command', (event, data) => callback(data));
    },
    onDebugGridUpdate: (callback) => {
        ipcRenderer.on('debug-grid-update', (event, data) => callback(data));
    },
    
    // Debug Panel
    send: (channel, data) => {
        // Whitelist of allowed channels
        const validChannels = [
            'debug-panel-dock',
            'debug-parameter-update',
            'debug-viewport-update',
            'debug-animation-command',
            'debug-grid-update'
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },
    on: (channel, callback) => {
        // Whitelist of allowed channels
        const validChannels = [
            'model-loaded',
            'parameter-changed',
            'debug-parameter-update',
            'debug-viewport-update',
            'debug-animation-command',
            'debug-grid-update'
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (event, data) => callback(data));
        }
    }
});

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
    // Model paths - handled via IPC to main process instead
    getAbsoluteModelPath: (maidId, modelFile) => ipcRenderer.invoke('get-model-path', maidId, modelFile),
    
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
    
    // Real-time settings changes
    changeSettings: (changedSettings) => ipcRenderer.send('settings-changed', changedSettings),
    
    // Cursor tracking
    getCursorPosition: () => ipcRenderer.invoke('get-cursor-position'),
    getScreenSize: () => ipcRenderer.invoke('get-screen-size'),
    
    // Multi-monitor
    getMonitors: () => ipcRenderer.invoke('get-monitors'),
    moveToMonitor: (index) => ipcRenderer.invoke('move-to-monitor', index),
    
    // Window resize
    resizeWindow: (width, height) => ipcRenderer.invoke('resize-window', width, height),
    
    // Window move (for modifier-key drag)
    moveWindow: (x, y) => ipcRenderer.invoke('move-window', x, y),
    
    // Model scale from renderer (for modifier-key scroll)
    setModelScaleFromRenderer: (scale) => ipcRenderer.invoke('set-model-scale-from-renderer', scale),
    
    // Movement mode notification to main process
    notifyMovementModeChanged: (mode) => ipcRenderer.send('movement-mode-changed', mode),
    
    // System notifications
    sendSystemNotification: (data) => ipcRenderer.send('system-notification', data),
    
    // Event listeners from main process
    onSettingsLoaded: (callback) => {
        ipcRenderer.on('settings-loaded', (event, settings) => callback(settings));
    },
    onSettingsUpdated: (callback) => {
        ipcRenderer.on('settings-updated', (event, settings) => callback(settings));
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
    onSetModelScale: (callback) => {
        ipcRenderer.on('set-model-scale', (event, scale) => callback(scale));
    },
    onSetFocusMode: (callback) => {
        ipcRenderer.on('set-focus-mode', (event, mode) => callback(mode));
    },
    onSetModelOffset: (callback) => {
        ipcRenderer.on('set-model-offset', (event, offset) => callback(offset));
    },
    onWindowResized: (callback) => {
        ipcRenderer.on('window-resized', () => callback());
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
    onNotificationReaction: (callback) => {
        ipcRenderer.on('notification-reaction', (event, data) => callback(data));
    }
});

/**
 * Aria Desktop Avatar - Electron Main Process
 * 
 * Features:
 * - Transparent, frameless window with Live2D avatar
 * - System tray with full controls
 * - Maid switcher
 * - Zoom controls
 * - Movement mode selection
 * - Auto-hide options
 * - Settings persistence
 */

const { app, BrowserWindow, ipcMain, screen, Tray, Menu, globalShortcut, nativeImage, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let settingsWindow = null;
let debugPanelWindow = null;
let tray = null;
let settings = null;

// Settings file path
const SETTINGS_PATH = path.join(app.getPath('userData'), 'settings.json');

// Default settings
const DEFAULT_SETTINGS = {
    window: {
        width: 400,
        height: 500,
        x: null, // null = auto position
        y: null,
        zoom: 1.0,
        opacity: 1.0,
        alwaysOnTop: true,
        startMinimized: false
    },
    avatar: {
        currentMaid: 'aria',
        movementMode: 'idle', // static, idle, mouse, camera
        trackingSpeed: 0.5,
        idleIntensity: 0.5
    },
    autoHide: {
        enabled: false,
        inactivityMinutes: 5,
        hideInFullscreen: false
    },
    debug: {
        enabled: false,
        panelDocked: false
    }
};

// Available maids
const MAIDS = {
    aria: { name: 'Aria', role: 'Head Maid', hasModel: true },
    sophia: { name: 'Sophia', role: 'Research', hasModel: false },
    luna: { name: 'Luna', role: 'Entertainment', hasModel: true },
    rose: { name: 'Rose', role: 'Scheduling', hasModel: false },
    mei: { name: 'Mei', role: 'Smart Home', hasModel: false },
    clara: { name: 'Clara', role: 'Communication', hasModel: false }
};

// Load settings
function loadSettings() {
    try {
        if (fs.existsSync(SETTINGS_PATH)) {
            const data = fs.readFileSync(SETTINGS_PATH, 'utf8');
            settings = { ...DEFAULT_SETTINGS, ...JSON.parse(data) };
        } else {
            settings = { ...DEFAULT_SETTINGS };
        }
    } catch (e) {
        console.error('Failed to load settings:', e);
        settings = { ...DEFAULT_SETTINGS };
    }
    return settings;
}

// Save settings
function saveSettings() {
    try {
        fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2));
    } catch (e) {
        console.error('Failed to save settings:', e);
    }
}

// Calculate window position
function getWindowPosition() {
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
    
    if (settings.window.x !== null && settings.window.y !== null) {
        return { x: settings.window.x, y: settings.window.y };
    }
    
    // Default: bottom-right
    return {
        x: screenWidth - settings.window.width - 20,
        y: screenHeight - settings.window.height - 20
    };
}

function createWindow() {
    const pos = getWindowPosition();
    
    mainWindow = new BrowserWindow({
        width: settings.window.width,
        height: settings.window.height,
        x: pos.x,
        y: pos.y,
        transparent: true,
        frame: false,
        alwaysOnTop: settings.window.alwaysOnTop,
        skipTaskbar: true, // Hide from taskbar, show in tray only
        resizable: true,
        hasShadow: false,
        opacity: settings.window.opacity,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'avatar.html'));

    // Send initial settings to renderer
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.send('settings-loaded', settings);
    });

    // Save position on move
    mainWindow.on('moved', () => {
        const bounds = mainWindow.getBounds();
        settings.window.x = bounds.x;
        settings.window.y = bounds.y;
        saveSettings();
    });

    // Save size on resize
    mainWindow.on('resized', () => {
        const bounds = mainWindow.getBounds();
        settings.window.width = bounds.width;
        settings.window.height = bounds.height;
        saveSettings();
    });

    // Minimize to tray instead of closing
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });

    // Dev tools
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
}

// Create tray icon (with fallback if no icon file)
function createTrayIcon() {
    const iconPath = path.join(__dirname, 'icon.png');
    
    if (fs.existsSync(iconPath)) {
        return nativeImage.createFromPath(iconPath);
    }
    
    // Create a simple colored square as fallback
    const size = 16;
    const canvas = Buffer.alloc(size * size * 4);
    
    // Pink color (#ff6b9d)
    for (let i = 0; i < size * size; i++) {
        canvas[i * 4] = 255;     // R
        canvas[i * 4 + 1] = 107; // G
        canvas[i * 4 + 2] = 157; // B
        canvas[i * 4 + 3] = 255; // A
    }
    
    return nativeImage.createFromBuffer(canvas, { width: size, height: size });
}

function createTray() {
    const icon = createTrayIcon();
    tray = new Tray(icon);
    tray.setToolTip('Aria Desktop Avatar');
    
    // Double-click to show/hide
    tray.on('double-click', () => {
        if (mainWindow.isVisible()) {
            mainWindow.hide();
        } else {
            mainWindow.show();
            mainWindow.focus();
        }
    });
    
    updateTrayMenu();
}

function updateTrayMenu() {
    const currentMaid = MAIDS[settings.avatar.currentMaid];
    
    const contextMenu = Menu.buildFromTemplate([
        {
            label: `🎭 ${currentMaid?.name || 'Aria'} (${currentMaid?.role || 'Head Maid'})`,
            enabled: false
        },
        { type: 'separator' },
        
        // Show/Hide
        {
            label: mainWindow?.isVisible() ? '👁️ Hide Avatar' : '👁️ Show Avatar',
            click: () => {
                if (mainWindow.isVisible()) {
                    mainWindow.hide();
                } else {
                    mainWindow.show();
                    mainWindow.focus();
                }
                updateTrayMenu();
            }
        },
        
        { type: 'separator' },
        
        // Maid Switcher
        {
            label: '🎀 Switch Maid',
            submenu: Object.entries(MAIDS).map(([id, maid]) => ({
                label: `${maid.name} (${maid.role})${!maid.hasModel ? ' [No Avatar]' : ''}`,
                type: 'radio',
                checked: settings.avatar.currentMaid === id,
                enabled: maid.hasModel,
                click: () => {
                    settings.avatar.currentMaid = id;
                    saveSettings();
                    mainWindow.webContents.send('switch-maid', id);
                    updateTrayMenu();
                }
            }))
        },
        
        { type: 'separator' },
        
        // Zoom
        {
            label: '🔍 Zoom',
            submenu: [
                { label: '50%', type: 'radio', checked: settings.window.zoom === 0.5, click: () => setZoom(0.5) },
                { label: '75%', type: 'radio', checked: settings.window.zoom === 0.75, click: () => setZoom(0.75) },
                { label: '100%', type: 'radio', checked: settings.window.zoom === 1.0, click: () => setZoom(1.0) },
                { label: '125%', type: 'radio', checked: settings.window.zoom === 1.25, click: () => setZoom(1.25) },
                { label: '150%', type: 'radio', checked: settings.window.zoom === 1.5, click: () => setZoom(1.5) },
                { label: '200%', type: 'radio', checked: settings.window.zoom === 2.0, click: () => setZoom(2.0) }
            ]
        },
        
        // Movement Mode
        {
            label: '🎬 Movement',
            submenu: [
                { 
                    label: 'Static', 
                    type: 'radio', 
                    checked: settings.avatar.movementMode === 'static',
                    click: () => setMovementMode('static')
                },
                { 
                    label: 'Idle Animation', 
                    type: 'radio', 
                    checked: settings.avatar.movementMode === 'idle',
                    click: () => setMovementMode('idle')
                },
                { 
                    label: 'Mouse Tracking', 
                    type: 'radio', 
                    checked: settings.avatar.movementMode === 'mouse',
                    click: () => setMovementMode('mouse')
                },
                { 
                    label: 'Camera Tracking', 
                    type: 'radio', 
                    checked: settings.avatar.movementMode === 'camera',
                    click: () => setMovementMode('camera')
                },
                { 
                    label: 'Random Wander', 
                    type: 'radio', 
                    checked: settings.avatar.movementMode === 'wander',
                    click: () => setMovementMode('wander')
                }
            ]
        },
        
        { type: 'separator' },
        
        // Expressions
        {
            label: '😊 Expressions',
            submenu: [
                { label: 'Default', click: () => triggerExpression('default') },
                { label: 'Happy', click: () => triggerExpression('happy') },
                { label: 'Thinking', click: () => triggerExpression('thinking') },
                { type: 'separator' },
                { label: 'Sassy (Aria)', click: () => triggerExpression('sassy') },
                { label: 'Heart Eyes', click: () => triggerExpression('heart_eyes') },
                { label: 'Blush', click: () => triggerExpression('blush') },
                { type: 'separator' },
                { label: 'Wave 👋', click: () => mainWindow.webContents.send('trigger-action', 'wave') },
                { label: 'Blink', click: () => mainWindow.webContents.send('trigger-action', 'blink') }
            ]
        },
        
        { type: 'separator' },
        
        // Window Options
        {
            label: '⚙️ Options',
            submenu: [
                {
                    label: 'Always on Top',
                    type: 'checkbox',
                    checked: settings.window.alwaysOnTop,
                    click: (menuItem) => {
                        settings.window.alwaysOnTop = menuItem.checked;
                        mainWindow.setAlwaysOnTop(menuItem.checked);
                        saveSettings();
                    }
                },
                {
                    label: 'Start Minimized',
                    type: 'checkbox',
                    checked: settings.window.startMinimized,
                    click: (menuItem) => {
                        settings.window.startMinimized = menuItem.checked;
                        saveSettings();
                    }
                },
                { type: 'separator' },
                {
                    label: 'Auto-Hide',
                    submenu: [
                        {
                            label: 'Disabled',
                            type: 'radio',
                            checked: !settings.autoHide.enabled,
                            click: () => {
                                settings.autoHide.enabled = false;
                                saveSettings();
                                mainWindow.webContents.send('auto-hide-changed', settings.autoHide);
                            }
                        },
                        {
                            label: 'After 5 min inactive',
                            type: 'radio',
                            checked: settings.autoHide.enabled && settings.autoHide.inactivityMinutes === 5,
                            click: () => {
                                settings.autoHide.enabled = true;
                                settings.autoHide.inactivityMinutes = 5;
                                saveSettings();
                                mainWindow.webContents.send('auto-hide-changed', settings.autoHide);
                            }
                        },
                        {
                            label: 'After 15 min inactive',
                            type: 'radio',
                            checked: settings.autoHide.enabled && settings.autoHide.inactivityMinutes === 15,
                            click: () => {
                                settings.autoHide.enabled = true;
                                settings.autoHide.inactivityMinutes = 15;
                                saveSettings();
                                mainWindow.webContents.send('auto-hide-changed', settings.autoHide);
                            }
                        },
                        { type: 'separator' },
                        {
                            label: 'Hide in Fullscreen Apps',
                            type: 'checkbox',
                            checked: settings.autoHide.hideInFullscreen,
                            click: (menuItem) => {
                                settings.autoHide.hideInFullscreen = menuItem.checked;
                                saveSettings();
                                mainWindow.webContents.send('auto-hide-changed', settings.autoHide);
                            }
                        }
                    ]
                },
                { type: 'separator' },
                {
                    label: 'Reset Position',
                    click: () => {
                        settings.window.x = null;
                        settings.window.y = null;
                        const pos = getWindowPosition();
                        mainWindow.setPosition(pos.x, pos.y);
                        saveSettings();
                    }
                },
                {
                    label: 'Reset All Settings',
                    click: () => {
                        settings = { ...DEFAULT_SETTINGS };
                        saveSettings();
                        mainWindow.webContents.send('settings-loaded', settings);
                        updateTrayMenu();
                    }
                }
            ]
        },
        
        { type: 'separator' },
        
        // Settings
        {
            label: '⚙️ Settings...',
            click: () => createSettingsWindow()
        },
        
        // Debug Panel
        {
            label: settings.debug.enabled ? '🔧 Hide Debug Panel' : '🔧 Show Debug Panel',
            click: () => {
                if (debugPanelWindow) {
                    debugPanelWindow.close();
                } else {
                    createDebugPanelWindow();
                }
            }
        },
        
        { type: 'separator' },
        
        {
            label: '❌ Quit Aria',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        }
    ]);
    
    tray.setContextMenu(contextMenu);
}

function setZoom(zoom) {
    settings.window.zoom = zoom;
    saveSettings();
    mainWindow.webContents.send('set-zoom', zoom);
    updateTrayMenu();
}

function setMovementMode(mode) {
    settings.avatar.movementMode = mode;
    saveSettings();
    mainWindow.webContents.send('set-movement-mode', mode);
    updateTrayMenu();
}

function triggerExpression(expression) {
    mainWindow.webContents.send('trigger-expression', expression);
}

// Settings window
function createSettingsWindow() {
    if (settingsWindow) {
        settingsWindow.focus();
        return;
    }
    
    settingsWindow = new BrowserWindow({
        width: 600,
        height: 700,
        parent: mainWindow,
        modal: false,
        resizable: true,
        minimizable: false,
        maximizable: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    
    settingsWindow.loadFile(path.join(__dirname, 'settings.html'));
    settingsWindow.setMenuBarVisibility(false);
    
    settingsWindow.on('closed', () => {
        settingsWindow = null;
    });
}

// Debug panel window
function createDebugPanelWindow() {
    if (debugPanelWindow) {
        debugPanelWindow.focus();
        return;
    }
    
    const mainBounds = mainWindow.getBounds();
    
    debugPanelWindow = new BrowserWindow({
        width: 400,
        height: 600,
        x: mainBounds.x + mainBounds.width + 10,
        y: mainBounds.y,
        resizable: true,
        minimizable: true,
        maximizable: false,
        alwaysOnTop: settings.window.alwaysOnTop,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    
    debugPanelWindow.loadFile(path.join(__dirname, 'debug-panel.html'));
    debugPanelWindow.setMenuBarVisibility(false);
    
    // Keep panel with main window if docked
    if (settings.debug.panelDocked) {
        mainWindow.on('move', updateDebugPanelPosition);
    }
    
    debugPanelWindow.on('closed', () => {
        debugPanelWindow = null;
        mainWindow.removeListener('move', updateDebugPanelPosition);
        settings.debug.enabled = false;
        saveSettings();
        updateTrayMenu();
    });
    
    settings.debug.enabled = true;
    saveSettings();
    updateTrayMenu();
}

function updateDebugPanelPosition() {
    if (debugPanelWindow && settings.debug.panelDocked) {
        const mainBounds = mainWindow.getBounds();
        debugPanelWindow.setPosition(mainBounds.x + mainBounds.width + 10, mainBounds.y);
    }
}

// Multi-monitor support
function getAllMonitors() {
    return screen.getAllDisplays().map((display, index) => ({
        id: display.id,
        bounds: display.bounds,
        workArea: display.workAreaSize,
        primary: display.id === screen.getPrimaryDisplay().id,
        index: index
    }));
}

function moveToMonitor(monitorIndex) {
    const displays = screen.getAllDisplays();
    if (monitorIndex >= 0 && monitorIndex < displays.length) {
        const display = displays[monitorIndex];
        const bounds = display.workArea;
        
        // Position in bottom-right of target monitor
        const x = bounds.x + bounds.width - settings.window.width - 20;
        const y = bounds.y + bounds.height - settings.window.height - 20;
        
        mainWindow.setPosition(x, y);
        settings.window.x = x;
        settings.window.y = y;
        settings.window.monitorIndex = monitorIndex;
        saveSettings();
    }
}

// Register global hotkeys
function registerHotkeys() {
    // Toggle visibility
    globalShortcut.register('Ctrl+Shift+A', () => {
        if (mainWindow.isVisible()) {
            mainWindow.hide();
        } else {
            mainWindow.show();
            mainWindow.focus();
        }
        updateTrayMenu();
    });
    
    // Zoom in
    globalShortcut.register('Ctrl+Shift+Plus', () => {
        const zooms = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
        const idx = zooms.indexOf(settings.window.zoom);
        if (idx < zooms.length - 1) {
            setZoom(zooms[idx + 1]);
        }
    });
    
    // Zoom out
    globalShortcut.register('Ctrl+Shift+-', () => {
        const zooms = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
        const idx = zooms.indexOf(settings.window.zoom);
        if (idx > 0) {
            setZoom(zooms[idx - 1]);
        }
    });
    
    // Cycle maids
    globalShortcut.register('Ctrl+Shift+M', () => {
        const maidIds = Object.keys(MAIDS).filter(id => MAIDS[id].hasModel);
        const idx = maidIds.indexOf(settings.avatar.currentMaid);
        const nextIdx = (idx + 1) % maidIds.length;
        const nextMaid = maidIds[nextIdx];
        
        settings.avatar.currentMaid = nextMaid;
        saveSettings();
        mainWindow.webContents.send('switch-maid', nextMaid);
        updateTrayMenu();
    });
}

// IPC handlers
ipcMain.handle('get-window-bounds', () => mainWindow.getBounds());
ipcMain.handle('get-settings', () => settings);
ipcMain.handle('save-settings', (event, newSettings) => {
    settings = { ...settings, ...newSettings };
    saveSettings();
    // Apply settings to main window
    if (mainWindow) {
        mainWindow.setAlwaysOnTop(settings.window.alwaysOnTop);
        mainWindow.setOpacity(settings.window.opacity);
        mainWindow.webContents.send('settings-loaded', settings);
    }
    updateTrayMenu();
    return settings;
});

ipcMain.handle('reset-settings', () => {
    settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    saveSettings();
    if (mainWindow) {
        mainWindow.webContents.send('settings-loaded', settings);
    }
    updateTrayMenu();
    return settings;
});

ipcMain.handle('set-click-through', (event, clickThrough) => {
    mainWindow.setIgnoreMouseEvents(clickThrough, { forward: true });
});

ipcMain.handle('get-cursor-position', () => {
    return screen.getCursorScreenPoint();
});

ipcMain.handle('get-screen-size', () => {
    return screen.getPrimaryDisplay().workAreaSize;
});

// Multi-monitor IPC
ipcMain.handle('get-monitors', () => getAllMonitors());

ipcMain.handle('move-to-monitor', (event, index) => {
    moveToMonitor(index);
});

// Settings file operations
ipcMain.handle('get-settings-path', () => SETTINGS_PATH);

ipcMain.handle('open-settings-folder', () => {
    shell.showItemInFolder(SETTINGS_PATH);
});

ipcMain.handle('export-settings', async () => {
    const result = await dialog.showSaveDialog({
        title: 'Export Settings',
        defaultPath: 'aria-settings.json',
        filters: [{ name: 'JSON', extensions: ['json'] }]
    });
    
    if (!result.canceled && result.filePath) {
        fs.writeFileSync(result.filePath, JSON.stringify(settings, null, 2));
        return true;
    }
    return false;
});

ipcMain.handle('import-settings', async () => {
    const result = await dialog.showOpenDialog({
        title: 'Import Settings',
        filters: [{ name: 'JSON', extensions: ['json'] }],
        properties: ['openFile']
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
        try {
            const data = fs.readFileSync(result.filePaths[0], 'utf8');
            const imported = JSON.parse(data);
            settings = { ...DEFAULT_SETTINGS, ...imported };
            saveSettings();
            if (mainWindow) {
                mainWindow.webContents.send('settings-loaded', settings);
            }
            updateTrayMenu();
            return settings;
        } catch (e) {
            console.error('Failed to import settings:', e);
            return null;
        }
    }
    return null;
});

// Debug Panel IPC handlers
ipcMain.on('debug-panel-dock', (event, docked) => {
    settings.debug.panelDocked = docked;
    saveSettings();
    
    if (docked) {
        mainWindow.on('move', updateDebugPanelPosition);
        updateDebugPanelPosition();
    } else {
        mainWindow.removeListener('move', updateDebugPanelPosition);
    }
});

ipcMain.on('debug-parameter-update', (event, data) => {
    // Forward to main window
    if (mainWindow) {
        mainWindow.webContents.send('debug-parameter-update', data);
    }
});

ipcMain.on('debug-viewport-update', (event, data) => {
    // Forward to main window
    if (mainWindow) {
        mainWindow.webContents.send('debug-viewport-update', data);
    }
});

ipcMain.on('debug-animation-command', (event, data) => {
    // Forward to main window
    if (mainWindow) {
        mainWindow.webContents.send('debug-animation-command', data);
    }
});

ipcMain.on('debug-grid-update', (event, data) => {
    // Forward to main window
    if (mainWindow) {
        mainWindow.webContents.send('debug-grid-update', data);
    }
});

// App lifecycle
app.whenReady().then(() => {
    loadSettings();
    createWindow();
    createTray();
    registerHotkeys();
    
    // Start minimized if configured
    if (settings.window.startMinimized) {
        mainWindow.hide();
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    globalShortcut.unregisterAll();
});

app.on('before-quit', () => {
    app.isQuitting = true;
});

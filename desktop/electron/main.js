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
let tray = null;
let settings = null;

// Active window tracking
let activeWindowInterval = null;
let lastActiveWindowBounds = null;

// Settings file path
const SETTINGS_PATH = path.join(app.getPath('userData'), 'settings.json');

// Default settings
const DEFAULT_SETTINGS = {
    window: {
        width: 400,
        height: 500,
        x: null, // null = auto position
        y: null,
        opacity: 1.0,
        alwaysOnTop: true,
        startMinimized: false
    },
    avatar: {
        currentMaid: 'aria',
        movementMode: 'idle', // static, idle, mouse, camera, wander, follow
        trackingSpeed: 0.5,
        idleIntensity: 0.5,
        useMediaPipe: false,
        // Display settings
        modelScale: 1.0,      // Character size (0.5 - 2.0)
        modelOffsetY: 0,      // Vertical position (-1 to 1, negative = up)
        focusMode: 'upper'    // full, upper, face
    },
    autoHide: {
        enabled: false,
        inactivityMinutes: 5,
        hideInFullscreen: false
    },
    notifications: {
        enabled: false,
        reactToAll: true,
        appWhitelist: []
    },
    audio: {
        showWaveform: true,
        waveformColor: '#ff6b9d'
    },
    controls: {
        modifierDragEnabled: true,  // Ctrl+drag to move, Ctrl+scroll to scale
        autoResizeWindow: true      // Auto-adjust window size to match character scale
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
            preload: path.join(__dirname, 'preload.js'),
            zoomFactor: 1.0,
            // Allow loading local files when HTTP server isn't running
            webSecurity: false,
            // Enable file protocol for local model loading
            allowRunningInsecureContent: true
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'avatar.html'));
    
    // Disable Ctrl+scroll zoom so we can use it for character scaling
    mainWindow.webContents.setVisualZoomLevelLimits(1, 1);
    mainWindow.webContents.on('before-input-event', (event, input) => {
        // Block Ctrl+Plus/Minus/0 for zoom
        if (input.control && (input.key === '+' || input.key === '-' || input.key === '=' || input.key === '0')) {
            // Don't block - let our global shortcuts handle it
        }
    });

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
                // Auto-update menu after visibility change
                setTimeout(updateTrayMenu, 100);
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
                    // Broadcast settings update
                    broadcastSettingsUpdate();
                    updateTrayMenu();
                }
            }))
        },
        
        { type: 'separator' },
        
        // Zoom
        {
            label: '🔍 Display',
            submenu: [
                {
                    label: 'Window Size',
                    submenu: [
                        { label: 'Small (300x400)', click: () => resizeWindow(300, 400) },
                        { label: 'Medium (400x500)', click: () => resizeWindow(400, 500) },
                        { label: 'Large (500x650)', click: () => resizeWindow(500, 650) },
                        { label: 'XL (600x800)', click: () => resizeWindow(600, 800) }
                    ]
                },
                {
                    label: 'Character Size',
                    submenu: [
                        { label: '50%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 0.5) < 0.01, click: () => setModelScale(0.5) },
                        { label: '60%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 0.6) < 0.01, click: () => setModelScale(0.6) },
                        { label: '70%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 0.7) < 0.01, click: () => setModelScale(0.7) },
                        { label: '80%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 0.8) < 0.01, click: () => setModelScale(0.8) },
                        { label: '90%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 0.9) < 0.01, click: () => setModelScale(0.9) },
                        { label: '100%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.0) < 0.01, click: () => setModelScale(1.0) },
                        { label: '110%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.1) < 0.01, click: () => setModelScale(1.1) },
                        { label: '120%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.2) < 0.01, click: () => setModelScale(1.2) },
                        { label: '130%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.3) < 0.01, click: () => setModelScale(1.3) },
                        { label: '140%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.4) < 0.01, click: () => setModelScale(1.4) },
                        { label: '150%', type: 'radio', checked: Math.abs((settings.avatar.modelScale || 1.0) - 1.5) < 0.01, click: () => setModelScale(1.5) },
                        { type: 'separator' },
                        { label: 'Quick Presets', enabled: false },
                        { label: '75%', click: () => setModelScale(0.75) },
                        { label: '125%', click: () => setModelScale(1.25) },
                        { label: '175%', click: () => setModelScale(1.75) },
                        { label: '200%', click: () => setModelScale(2.0) }
                    ]
                },
                {
                    label: 'Focus',
                    submenu: [
                        { label: 'Full Body', type: 'radio', checked: (settings.avatar.focusMode || 'upper') === 'full', click: () => setFocusMode('full') },
                        { label: 'Upper Body', type: 'radio', checked: (settings.avatar.focusMode || 'upper') === 'upper', click: () => setFocusMode('upper') },
                        { label: 'Face', type: 'radio', checked: (settings.avatar.focusMode || 'upper') === 'face', click: () => setFocusMode('face') }
                    ]
                },
                { type: 'separator' },
                {
                    label: 'Move Up',
                    click: () => adjustModelOffset(-0.1)
                },
                {
                    label: 'Move Down',
                    click: () => adjustModelOffset(0.1)
                },
                {
                    label: 'Center',
                    click: () => setModelOffset(0)
                }
            ]
        },
        
        // Movement Mode
        {
            label: '🎬 Movement',
            submenu: [
                { 
                    label: 'Static', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'static',
                    click: () => setMovementMode('static')
                },
                { 
                    label: 'Idle Animation', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'idle',
                    click: () => setMovementMode('idle')
                },
                { 
                    label: 'Mouse Tracking', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'mouse',
                    click: () => setMovementMode('mouse')
                },
                { 
                    label: 'Camera Tracking', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'camera',
                    click: () => setMovementMode('camera')
                },
                { 
                    label: 'Random Wander', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'wander',
                    click: () => setMovementMode('wander')
                },
                { 
                    label: 'Follow Active Window', 
                    type: 'radio', 
                    checked: (settings.avatar.movementMode || 'idle') === 'follow',
                    click: () => setMovementMode('follow')
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
                        broadcastSettingsUpdate();
                    }
                },
                {
                    label: 'Start Minimized',
                    type: 'checkbox',
                    checked: settings.window.startMinimized,
                    click: (menuItem) => {
                        settings.window.startMinimized = menuItem.checked;
                        saveSettings();
                        broadcastSettingsUpdate();
                    }
                },
                {
                    label: 'Auto-Resize Window',
                    type: 'checkbox',
                    checked: settings.controls?.autoResizeWindow !== false,
                    click: (menuItem) => {
                        if (!settings.controls) settings.controls = {};
                        settings.controls.autoResizeWindow = menuItem.checked;
                        saveSettings();
                        broadcastSettingsUpdate();
                        
                        if (menuItem.checked) {
                            // Trigger immediate resize if enabled
                            autoAdjustWindowSize(settings.avatar.modelScale || 1.0, settings.avatar.focusMode || 'upper');
                        }
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
                                broadcastSettingsUpdate();
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
                                broadcastSettingsUpdate();
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
                                broadcastSettingsUpdate();
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
                                broadcastSettingsUpdate();
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
                        broadcastSettingsUpdate();
                    }
                },
                {
                    label: 'Reset All Settings',
                    click: () => {
                        settings = { ...DEFAULT_SETTINGS };
                        saveSettings();
                        mainWindow.webContents.send('settings-loaded', settings);
                        broadcastSettingsUpdate();
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

// Legacy zoom function - kept for backwards compatibility
// New code should use setModelScale() instead
function setZoom(zoom) {
    // Map zoom to model scale for backwards compatibility
    setModelScale(zoom);
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

// Display control functions
function resizeWindow(width, height) {
    settings.window.width = width;
    settings.window.height = height;
    mainWindow.setSize(width, height);
    saveSettings();
    mainWindow.webContents.send('window-resized');
    updateTrayMenu();
}

function setModelScale(scale) {
    settings.avatar.modelScale = scale;
    saveSettings();
    
    // Auto-adjust window size based on character scale and focus mode
    autoAdjustWindowSize(scale, settings.avatar.focusMode);
    
    mainWindow.webContents.send('set-model-scale', scale);
    updateTrayMenu();
    // Broadcast settings update to all windows including settings dialog
    broadcastSettingsUpdate();
}

function autoAdjustWindowSize(modelScale, focusMode) {
    // Check if auto-resize is enabled
    if (!settings.controls?.autoResizeWindow) {
        return;
    }
    
    // Base window dimensions that work well for each focus mode at 100% scale
    const baseDimensions = {
        'face': { width: 300, height: 350 },
        'upper': { width: 400, height: 500 },
        'full': { width: 500, height:650 }
    };
    
    const base = baseDimensions[focusMode] || baseDimensions['upper'];
    
    // Calculate new dimensions based on scale
    // Use square root scaling for window size to avoid excessive window growth
    const scaleFactor = Math.sqrt(modelScale);
    const newWidth = Math.round(base.width * scaleFactor);
    const newHeight = Math.round(base.height * scaleFactor);
    
    // Clamp to reasonable limits
    const minWidth = 250;
    const maxWidth = 800;
    const minHeight = 300;
    const maxHeight = 900;
    
    const clampedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
    const clampedHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
    
    // Only resize if the change is significant (avoid constant tiny adjustments)
    const currentBounds = mainWindow.getBounds();
    const widthDiff = Math.abs(currentBounds.width - clampedWidth);
    const heightDiff = Math.abs(currentBounds.height - clampedHeight);
    
    if (widthDiff > 10 || heightDiff > 10) {
        console.log(`📐 Auto-adjusting window: ${currentBounds.width}x${currentBounds.height} → ${clampedWidth}x${clampedHeight} (scale: ${modelScale}, focus: ${focusMode})`);
        
        // Get current position to maintain center point
        const centerX = currentBounds.x + currentBounds.width / 2;
        const centerY = currentBounds.y + currentBounds.height / 2;
        
        // Calculate new position to keep window centered
        const newX = Math.round(centerX - clampedWidth / 2);
        const newY = Math.round(centerY - clampedHeight / 2);
        
        // Ensure window stays on screen
        const display = screen.getDisplayNearestPoint({ x: centerX, y: centerY });
        const safeX = Math.max(display.bounds.x, Math.min(newX, display.bounds.x + display.bounds.width - clampedWidth));
        const safeY = Math.max(display.bounds.y, Math.min(newY, display.bounds.y + display.bounds.height - clampedHeight));
        
        // Apply new size and position
        mainWindow.setBounds({
            x: safeX,
            y: safeY,
            width: clampedWidth,
            height: clampedHeight
        });
        
        // Update settings
        settings.window.width = clampedWidth;
        settings.window.height = clampedHeight;
        settings.window.x = safeX;
        settings.window.y = safeY;
        saveSettings();
        
        // Notify renderer of window change
        mainWindow.webContents.send('window-resized');
    }
}

function setFocusMode(mode) {
    settings.avatar.focusMode = mode;
    saveSettings();
    
    // Auto-adjust window size for new focus mode
    autoAdjustWindowSize(settings.avatar.modelScale || 1.0, mode);
    
    mainWindow.webContents.send('set-focus-mode', mode);
    updateTrayMenu();
}

function setModelOffset(offset) {
    settings.avatar.modelOffsetY = Math.max(-1, Math.min(1, offset));
    saveSettings();
    mainWindow.webContents.send('set-model-offset', settings.avatar.modelOffsetY);
    updateTrayMenu();
}

function adjustModelOffset(delta) {
    const newOffset = (settings.avatar.modelOffsetY || 0) + delta;
    setModelOffset(newOffset);
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
    
    // Scale up (character size) - smooth 5% increments
    globalShortcut.register('Ctrl+Shift+Plus', () => {
        const currentScale = settings.avatar.modelScale || 1.0;
        const newScale = Math.min(2.0, Math.round((currentScale + 0.05) * 100) / 100);
        setModelScale(newScale);
    });
    
    // Scale down (character size) - smooth 5% decrements
    globalShortcut.register('Ctrl+Shift+-', () => {
        const currentScale = settings.avatar.modelScale || 1.0;
        const newScale = Math.max(0.5, Math.round((currentScale - 0.05) * 100) / 100);
        setModelScale(newScale);
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

// Re-register hotkeys with custom bindings from settings
function reregisterHotkeys() {
    globalShortcut.unregisterAll();
    
    const hotkeys = settings.hotkeys || {};
    
    // Toggle visibility
    const toggleKey = hotkeys.toggleVisibility || 'Ctrl+Shift+A';
    try {
        globalShortcut.register(toggleKey, () => {
            if (mainWindow.isVisible()) {
                mainWindow.hide();
            } else {
                mainWindow.show();
                mainWindow.focus();
            }
            updateTrayMenu();
        });
    } catch (e) {
        console.error(`Failed to register toggle hotkey (${toggleKey}):`, e.message);
    }
    
    // Scale up - smooth 5% increments
    const scaleUpKey = hotkeys.zoomIn || 'Ctrl+Shift+Plus';
    try {
        globalShortcut.register(scaleUpKey, () => {
            const currentScale = settings.avatar.modelScale || 1.0;
            const newScale = Math.min(2.0, Math.round((currentScale + 0.05) * 100) / 100);
            setModelScale(newScale);
        });
    } catch (e) {
        console.error(`Failed to register scale up hotkey (${scaleUpKey}):`, e.message);
    }
    
    // Scale down - smooth 5% decrements
    const scaleDownKey = hotkeys.zoomOut || 'Ctrl+Shift+-';
    try {
        globalShortcut.register(scaleDownKey, () => {
            const currentScale = settings.avatar.modelScale || 1.0;
            const newScale = Math.max(0.5, Math.round((currentScale - 0.05) * 100) / 100);
            setModelScale(newScale);
        });
    } catch (e) {
        console.error(`Failed to register scale down hotkey (${scaleDownKey}):`, e.message);
    }
    
    // Cycle maids
    const cycleMaidKey = hotkeys.cycleMaid || 'Ctrl+Shift+M';
    try {
        globalShortcut.register(cycleMaidKey, () => {
            const maidIds = Object.keys(MAIDS).filter(id => MAIDS[id].hasModel);
            const idx = maidIds.indexOf(settings.avatar.currentMaid);
            const nextIdx = (idx + 1) % maidIds.length;
            const nextMaid = maidIds[nextIdx];
            
            settings.avatar.currentMaid = nextMaid;
            saveSettings();
            mainWindow.webContents.send('switch-maid', nextMaid);
            updateTrayMenu();
        });
    } catch (e) {
        console.error(`Failed to register cycle maid hotkey (${cycleMaidKey}):`, e.message);
    }
}

// IPC handlers
ipcMain.handle('get-window-bounds', () => mainWindow.getBounds());
ipcMain.handle('get-settings', () => settings);

// Model path handler for local file loading
ipcMain.handle('get-model-path', (event, maidId, modelFile) => {
    const modelPath = path.join(__dirname, '..', '..', 'live2d', 'models', maidId, modelFile);
    // Convert to file:// URL
    return `file:///${modelPath.replace(/\\/g, '/')}`;
});

// Enhanced save-settings with proper synchronization
ipcMain.handle('save-settings', (event, newSettings) => {
    // Check if hotkeys changed
    const hotkeysChanged = JSON.stringify(settings.hotkeys) !== JSON.stringify(newSettings.hotkeys);
    
    settings = { ...settings, ...newSettings };
    saveSettings();
    
    // Apply settings to main window
    if (mainWindow) {
        mainWindow.setAlwaysOnTop(settings.window.alwaysOnTop);
        mainWindow.setOpacity(settings.window.opacity);
        mainWindow.webContents.send('settings-loaded', settings);
    }
    
    // Re-register hotkeys if they changed
    if (hotkeysChanged && settings.hotkeys) {
        reregisterHotkeys();
    }
    
    // Update tray menu to reflect changes
    updateTrayMenu();
    
    // Broadcast settings update to all windows
    broadcastSettingsUpdate();
    
    return settings;
});

// New IPC handler for real-time settings changes
ipcMain.on('settings-changed', (event, changedSettings) => {
    // Merge changed settings
    settings = mergeDeep(settings, changedSettings);
    saveSettings();
    
    // Apply immediate changes to main window
    if (mainWindow && changedSettings.window) {
        if (changedSettings.window.alwaysOnTop !== undefined) {
            mainWindow.setAlwaysOnTop(changedSettings.window.alwaysOnTop);
        }
        if (changedSettings.window.opacity !== undefined) {
            mainWindow.setOpacity(changedSettings.window.opacity);
        }
    }
    
    // Update tray menu
    updateTrayMenu();
    
    // Broadcast to all windows except sender
    broadcastSettingsUpdate(event.sender);
});

// Helper function for deep merging objects
function mergeDeep(target, source) {
    const result = { ...target };
    for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            result[key] = mergeDeep(result[key] || {}, source[key]);
        } else {
            result[key] = source[key];
        }
    }
    return result;
}

// Helper function to broadcast settings updates
function broadcastSettingsUpdate(excludeSender = null) {
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(win => {
        if (win.webContents !== excludeSender) {
            win.webContents.send('settings-updated', settings);
        }
    });
}

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

// Dynamic click-through for desktop mascot mode (from Live2DController)
ipcMain.on('set-mouse-through', (_event, ignore) => {
    if (mainWindow) {
        mainWindow.setIgnoreMouseEvents(ignore, { forward: true });
    }
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

// Window resize IPC
ipcMain.handle('resize-window', (event, width, height) => {
    resizeWindow(width, height);
    return { width, height };
});

// Window move IPC (for modifier-key drag)
ipcMain.handle('move-window', (event, x, y) => {
    if (mainWindow) {
        mainWindow.setPosition(Math.round(x), Math.round(y));
        settings.window.x = Math.round(x);
        settings.window.y = Math.round(y);
        saveSettings();
    }
    return { x, y };
});

// Model scale from renderer (for modifier-key scroll)
ipcMain.handle('set-model-scale-from-renderer', (event, scale) => {
    setModelScale(scale);
    return scale;
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

// ============ Follow Active Window ============

function startFollowActiveWindow() {
    if (activeWindowInterval) {
        clearInterval(activeWindowInterval);
    }
    
    // Use PowerShell to get active window info on Windows
    const { exec } = require('child_process');
    
    activeWindowInterval = setInterval(() => {
        if (settings.avatar.movementMode !== 'follow') {
            stopFollowActiveWindow();
            return;
        }
        
        // PowerShell command to get active window bounds
        const psCommand = `
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")]
                public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                [StructLayout(LayoutKind.Sequential)]
                public struct RECT { public int Left, Top, Right, Bottom; }
            }
"@
            $hwnd = [Win32]::GetForegroundWindow()
            $rect = New-Object Win32+RECT
            [Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
            "$($rect.Left),$($rect.Top),$($rect.Right),$($rect.Bottom)"
        `;
        
        exec(`powershell -Command "${psCommand.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`, (error, stdout) => {
            if (error || !stdout.trim()) return;
            
            const parts = stdout.trim().split(',').map(Number);
            if (parts.length !== 4 || parts.some(isNaN)) return;
            
            const [left, top, right, bottom] = parts;
            const windowBounds = { x: left, y: top, width: right - left, height: bottom - top };
            
            // Skip if it's our own window or too small (likely taskbar)
            const myBounds = mainWindow.getBounds();
            if (Math.abs(windowBounds.x - myBounds.x) < 10 && Math.abs(windowBounds.y - myBounds.y) < 10) return;
            if (windowBounds.width < 200 || windowBounds.height < 100) return;
            
            // Position avatar at bottom-right of active window
            const newX = windowBounds.x + windowBounds.width - settings.window.width - 10;
            const newY = windowBounds.y + windowBounds.height - settings.window.height - 10;
            
            // Only move if position changed significantly
            if (!lastActiveWindowBounds || 
                Math.abs(newX - lastActiveWindowBounds.x) > 20 || 
                Math.abs(newY - lastActiveWindowBounds.y) > 20) {
                
                // Keep within screen bounds
                const display = screen.getDisplayNearestPoint({ x: newX, y: newY });
                const safeX = Math.max(display.bounds.x, Math.min(newX, display.bounds.x + display.bounds.width - settings.window.width));
                const safeY = Math.max(display.bounds.y, Math.min(newY, display.bounds.y + display.bounds.height - settings.window.height));
                
                mainWindow.setPosition(Math.round(safeX), Math.round(safeY));
                lastActiveWindowBounds = { x: safeX, y: safeY };
            }
        });
    }, 500); // Check every 500ms
}

function stopFollowActiveWindow() {
    if (activeWindowInterval) {
        clearInterval(activeWindowInterval);
        activeWindowInterval = null;
    }
    lastActiveWindowBounds = null;
}

// ============ Notification Reactions ============

let notificationWatcher = null;

function startNotificationWatcher() {
    if (!settings.notifications?.enabled) return;
    
    // Use PowerShell to watch for toast notifications on Windows
    const { exec } = require('child_process');
    
    // Poll for new notifications (Windows doesn't have a direct API for this in Electron)
    // This is a simplified approach - checks notification center state
    notificationWatcher = setInterval(() => {
        if (!settings.notifications?.enabled) {
            stopNotificationWatcher();
            return;
        }
        
        // Check if notification center has new items via registry/PowerShell
        // For now, we'll trigger reactions via IPC from the renderer when audio events occur
    }, 5000);
}

function stopNotificationWatcher() {
    if (notificationWatcher) {
        clearInterval(notificationWatcher);
        notificationWatcher = null;
    }
}

// IPC for notification reactions
ipcMain.on('system-notification', (event, data) => {
    if (settings.notifications?.enabled && mainWindow) {
        mainWindow.webContents.send('notification-reaction', {
            type: data.type || 'generic',
            app: data.app || 'unknown'
        });
    }
});

// IPC for movement mode changes that need main process handling
ipcMain.on('movement-mode-changed', (event, mode) => {
    if (mode === 'follow') {
        startFollowActiveWindow();
    } else {
        stopFollowActiveWindow();
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
    
    // Start follow mode if configured
    if (settings.avatar.movementMode === 'follow') {
        startFollowActiveWindow();
    }
    
    // Start notification watcher if enabled
    if (settings.notifications?.enabled) {
        startNotificationWatcher();
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

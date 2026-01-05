/**
 * Aria Desktop Avatar - Electron Main Process
 * 
 * Creates a transparent, frameless window with the Live2D avatar
 * that floats on the desktop. Connects to the Python backend via WebSocket.
 */

const { app, BrowserWindow, ipcMain, screen, Tray, Menu } = require('electron');
const path = require('path');

let mainWindow = null;
let tray = null;

// Window configuration
const DEFAULT_WIDTH = 400;
const DEFAULT_HEIGHT = 500;
const DEFAULT_POSITION = 'bottom-right'; // bottom-right, bottom-left, top-right, top-left

function createWindow() {
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
    
    // Calculate position
    let x, y;
    switch (DEFAULT_POSITION) {
        case 'bottom-right':
            x = screenWidth - DEFAULT_WIDTH - 20;
            y = screenHeight - DEFAULT_HEIGHT - 20;
            break;
        case 'bottom-left':
            x = 20;
            y = screenHeight - DEFAULT_HEIGHT - 20;
            break;
        case 'top-right':
            x = screenWidth - DEFAULT_WIDTH - 20;
            y = 20;
            break;
        case 'top-left':
            x = 20;
            y = 20;
            break;
        default:
            x = screenWidth - DEFAULT_WIDTH - 20;
            y = screenHeight - DEFAULT_HEIGHT - 20;
    }

    mainWindow = new BrowserWindow({
        width: DEFAULT_WIDTH,
        height: DEFAULT_HEIGHT,
        x: x,
        y: y,
        transparent: true,
        frame: false,
        alwaysOnTop: true,
        skipTaskbar: false,
        resizable: true,
        hasShadow: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // Load the avatar HTML
    mainWindow.loadFile(path.join(__dirname, 'avatar.html'));

    // Make window click-through except for the avatar
    // This is handled in the renderer via CSS pointer-events
    
    // Dev tools in dev mode
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function createTray() {
    // Create system tray icon for controls
    // Using a simple icon path - you can replace with a proper icon
    try {
        tray = new Tray(path.join(__dirname, 'icon.png'));
    } catch (e) {
        // No icon file, skip tray
        console.log('No tray icon found, skipping tray creation');
        return;
    }
    
    const contextMenu = Menu.buildFromTemplate([
        { 
            label: 'Show/Hide Avatar', 
            click: () => {
                if (mainWindow.isVisible()) {
                    mainWindow.hide();
                } else {
                    mainWindow.show();
                }
            }
        },
        { 
            label: 'Always on Top', 
            type: 'checkbox', 
            checked: true,
            click: (menuItem) => {
                mainWindow.setAlwaysOnTop(menuItem.checked);
            }
        },
        { type: 'separator' },
        { 
            label: 'Reset Position', 
            click: () => {
                const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
                mainWindow.setPosition(screenWidth - DEFAULT_WIDTH - 20, screenHeight - DEFAULT_HEIGHT - 20);
            }
        },
        { type: 'separator' },
        { 
            label: 'Quit', 
            click: () => {
                app.quit();
            }
        }
    ]);
    
    tray.setToolTip('Aria Desktop Avatar');
    tray.setContextMenu(contextMenu);
}

// IPC handlers
ipcMain.handle('get-window-bounds', () => {
    return mainWindow.getBounds();
});

ipcMain.handle('set-click-through', (event, clickThrough) => {
    mainWindow.setIgnoreMouseEvents(clickThrough, { forward: true });
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    createTray();
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

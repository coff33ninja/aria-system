/**
 * Aria Desktop Settings UI
 */

let settings = null;
let monitors = [];

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Load settings from main process
async function loadSettings() {
    settings = await window.electronAPI.getSettings();
    monitors = await window.electronAPI.getMonitors();
    renderAllTabs();
}

function renderAllTabs() {
    renderGeneralTab();
    renderDisplayTab();
    renderMovementTab();
    renderHotkeysTab();
    renderAdvancedTab();
}

function renderGeneralTab() {
    const container = document.getElementById('general');
    container.innerHTML = `
        <div class="section">
            <h3>🎀 Maid Selection</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Default Maid</span>
                    <small>Which maid appears on startup</small>
                </div>
                <select id="default-maid">
                    <option value="aria" ${settings.avatar.currentMaid === 'aria' ? 'selected' : ''}>Aria (Head Maid)</option>
                    <option value="luna" ${settings.avatar.currentMaid === 'luna' ? 'selected' : ''}>Luna (Entertainment)</option>
                </select>
            </div>
        </div>
        <div class="section">
            <h3>🚀 Startup</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Start Minimized</span>
                    <small>Start in system tray instead of showing avatar</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="start-minimized" ${settings.window.startMinimized ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Always on Top</span>
                    <small>Keep avatar above other windows</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="always-on-top" ${settings.window.alwaysOnTop ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
    `;
}


function renderDisplayTab() {
    const container = document.getElementById('display');
    container.innerHTML = `
        <div class="section">
            <h3>📐 Window Size</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Window Preset</span>
                    <small>Quick size presets</small>
                </div>
                <select id="window-preset" onchange="applyWindowPreset(this.value)">
                    <option value="">Custom</option>
                    <option value="300,400">Small (300×400)</option>
                    <option value="400,500">Medium (400×500)</option>
                    <option value="500,650">Large (500×650)</option>
                    <option value="600,800">XL (600×800)</option>
                </select>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Window Opacity</span>
                    <small>Transparency level</small>
                </div>
                <input type="range" id="opacity" min="30" max="100" value="${settings.window.opacity * 100}">
                <span>${Math.round(settings.window.opacity * 100)}%</span>
            </div>
        </div>
        <div class="section">
            <h3>👤 Character Display</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Character Size</span>
                    <small>Scale: ${Math.round((settings.avatar?.modelScale || 1) * 100)}%</small>
                </div>
                <input type="range" id="model-scale" min="50" max="200" value="${(settings.avatar?.modelScale || 1) * 100}" 
                    oninput="document.querySelector('#model-scale + span').textContent = this.value + '%'">
                <span>${Math.round((settings.avatar?.modelScale || 1) * 100)}%</span>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Focus Mode</span>
                    <small>What part of character to show</small>
                </div>
                <select id="focus-mode">
                    <option value="full" ${settings.avatar?.focusMode === 'full' ? 'selected' : ''}>Full Body</option>
                    <option value="upper" ${settings.avatar?.focusMode === 'upper' ? 'selected' : ''}>Upper Body</option>
                    <option value="face" ${settings.avatar?.focusMode === 'face' ? 'selected' : ''}>Face</option>
                </select>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Vertical Position</span>
                    <small>Move character up/down</small>
                </div>
                <input type="range" id="model-offset" min="-100" max="100" value="${(settings.avatar?.modelOffsetY || 0) * 100}">
                <span>${settings.avatar?.modelOffsetY > 0 ? 'Down' : settings.avatar?.modelOffsetY < 0 ? 'Up' : 'Center'}</span>
            </div>
        </div>
        <div class="section">
            <h3>🖥️ Monitor Selection</h3>
            <div class="monitor-list" id="monitor-list"></div>
        </div>
    `;
    renderMonitorList();
}

function renderMonitorList() {
    const list = document.getElementById('monitor-list');
    if (!monitors || monitors.length === 0) {
        list.innerHTML = '<p style="color:#888">Loading monitors...</p>';
        return;
    }
    list.innerHTML = monitors.map((m, i) => `
        <div class="monitor-item">
            <div class="monitor-preview">${i + 1}</div>
            <div class="setting-label">
                <span>Monitor ${i + 1}${m.primary ? ' (Primary)' : ''}</span>
                <small>${m.bounds.width}x${m.bounds.height}</small>
            </div>
            <button class="btn btn-secondary" onclick="moveToMonitor(${i})">Move Here</button>
        </div>
    `).join('');
}

function renderMovementTab() {
    const container = document.getElementById('movement');
    const modes = ['static', 'idle', 'mouse', 'camera', 'wander', 'follow'];
    container.innerHTML = `
        <div class="section">
            <h3>🎬 Movement Mode</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Default Mode</span>
                    <small>How the avatar moves when idle</small>
                </div>
                <select id="movement-mode">
                    ${modes.map(m => `<option value="${m}" ${settings.avatar.movementMode === m ? 'selected' : ''}>${m === 'follow' ? 'Follow Active Window' : m.charAt(0).toUpperCase() + m.slice(1)}</option>`).join('')}
                </select>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Tracking Speed</span>
                    <small>How fast avatar follows mouse/camera</small>
                </div>
                <input type="range" id="tracking-speed" min="10" max="100" value="${settings.avatar.trackingSpeed * 100}">
            </div>
        </div>
        <div class="section">
            <h3>👁️ Auto-Hide</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Enable Auto-Hide</span>
                    <small>Hide avatar after inactivity</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="auto-hide-enabled" ${settings.autoHide.enabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Inactivity Timeout</span>
                    <small>Minutes before hiding</small>
                </div>
                <input type="number" id="auto-hide-minutes" min="1" max="60" value="${settings.autoHide.inactivityMinutes}" style="width:80px">
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Hide in Fullscreen</span>
                    <small>Auto-hide when apps go fullscreen</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="hide-fullscreen" ${settings.autoHide.hideInFullscreen ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
    `;
}


function renderHotkeysTab() {
    const container = document.getElementById('hotkeys');
    const hotkeys = settings.hotkeys || {
        toggleVisibility: 'Ctrl+Shift+A',
        cycleMaid: 'Ctrl+Shift+M',
        zoomIn: 'Ctrl+Shift+Plus',
        zoomOut: 'Ctrl+Shift+-'
    };
    container.innerHTML = `
        <div class="section">
            <h3>⌨️ Global Hotkeys</h3>
            <p style="color:#888;margin-bottom:16px;font-size:12px">These work even when Aria is not focused</p>
            <div class="setting-row">
                <div class="setting-label"><span>Toggle Visibility</span></div>
                <div class="hotkey-input">
                    <input type="text" id="hk-toggle" value="${hotkeys.toggleVisibility}" readonly>
                    <button class="btn btn-secondary" onclick="recordHotkey('hk-toggle')">Record</button>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-label"><span>Cycle Maids</span></div>
                <div class="hotkey-input">
                    <input type="text" id="hk-cycle" value="${hotkeys.cycleMaid}" readonly>
                    <button class="btn btn-secondary" onclick="recordHotkey('hk-cycle')">Record</button>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-label"><span>Zoom In</span></div>
                <div class="hotkey-input">
                    <input type="text" id="hk-zoomin" value="${hotkeys.zoomIn}" readonly>
                    <button class="btn btn-secondary" onclick="recordHotkey('hk-zoomin')">Record</button>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-label"><span>Zoom Out</span></div>
                <div class="hotkey-input">
                    <input type="text" id="hk-zoomout" value="${hotkeys.zoomOut}" readonly>
                    <button class="btn btn-secondary" onclick="recordHotkey('hk-zoomout')">Record</button>
                </div>
            </div>
        </div>
    `;
}

function renderAdvancedTab() {
    const container = document.getElementById('advanced');
    container.innerHTML = `
        <div class="section">
            <h3>📷 Camera Tracking</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Use Advanced Detection</span>
                    <small>MediaPipe for better face tracking (loads ~2MB)</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="use-mediapipe" ${settings.avatar?.useMediaPipe ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
        <div class="section">
            <h3>🔔 Notifications</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>React to Notifications</span>
                    <small>Avatar reacts when you receive notifications</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="notification-react" ${settings.notifications?.enabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
        <div class="section">
            <h3>🎵 Audio Visualization</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Show Waveform</span>
                    <small>Display audio waveform when speaking</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="show-waveform" ${settings.audio?.showWaveform !== false ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Show Listening Ring</span>
                    <small>Pulsing ring when listening for input</small>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="show-listening-ring" ${settings.audio?.showListeningRing !== false ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
        <div class="section">
            <h3>💾 Data</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Settings Location</span>
                    <small id="settings-path">Loading...</small>
                </div>
                <button class="btn btn-secondary" onclick="openSettingsFolder()">Open Folder</button>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Export Settings</span>
                    <small>Save settings to a file</small>
                </div>
                <button class="btn btn-secondary" onclick="exportSettings()">Export</button>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Import Settings</span>
                    <small>Load settings from a file</small>
                </div>
                <button class="btn btn-secondary" onclick="importSettings()">Import</button>
            </div>
        </div>
    `;
    loadSettingsPath();
}

async function loadSettingsPath() {
    const path = await window.electronAPI.getSettingsPath();
    document.getElementById('settings-path').textContent = path;
}


// Hotkey recording
let recordingInput = null;

function recordHotkey(inputId) {
    const input = document.getElementById(inputId);
    input.value = 'Press keys...';
    input.style.background = 'rgba(255,107,157,0.2)';
    recordingInput = input;
    
    document.addEventListener('keydown', handleHotkeyRecord, { once: true });
}

function handleHotkeyRecord(e) {
    e.preventDefault();
    if (!recordingInput) return;
    
    const parts = [];
    if (e.ctrlKey) parts.push('Ctrl');
    if (e.shiftKey) parts.push('Shift');
    if (e.altKey) parts.push('Alt');
    
    const key = e.key.length === 1 ? e.key.toUpperCase() : e.key;
    if (!['Control', 'Shift', 'Alt'].includes(e.key)) {
        parts.push(key);
    }
    
    recordingInput.value = parts.join('+') || 'None';
    recordingInput.style.background = '';
    recordingInput = null;
}

// Actions
async function moveToMonitor(index) {
    await window.electronAPI.moveToMonitor(index);
}

async function openSettingsFolder() {
    await window.electronAPI.openSettingsFolder();
}

async function exportSettings() {
    await window.electronAPI.exportSettings();
}

async function importSettings() {
    const result = await window.electronAPI.importSettings();
    if (result) {
        settings = result;
        renderAllTabs();
    }
}

// Save settings
function collectSettings() {
    return {
        window: {
            ...settings.window,
            opacity: parseInt(document.getElementById('opacity')?.value || 100) / 100,
            startMinimized: document.getElementById('start-minimized')?.checked || false,
            alwaysOnTop: document.getElementById('always-on-top')?.checked !== false
        },
        avatar: {
            ...settings.avatar,
            currentMaid: document.getElementById('default-maid')?.value || 'aria',
            movementMode: document.getElementById('movement-mode')?.value || 'idle',
            trackingSpeed: parseInt(document.getElementById('tracking-speed')?.value || 50) / 100,
            useMediaPipe: document.getElementById('use-mediapipe')?.checked || false,
            modelScale: parseInt(document.getElementById('model-scale')?.value || 100) / 100,
            focusMode: document.getElementById('focus-mode')?.value || 'upper',
            modelOffsetY: parseInt(document.getElementById('model-offset')?.value || 0) / 100
        },
        autoHide: {
            enabled: document.getElementById('auto-hide-enabled')?.checked || false,
            inactivityMinutes: parseInt(document.getElementById('auto-hide-minutes')?.value || 5),
            hideInFullscreen: document.getElementById('hide-fullscreen')?.checked || false
        },
        hotkeys: {
            toggleVisibility: document.getElementById('hk-toggle')?.value || 'Ctrl+Shift+A',
            cycleMaid: document.getElementById('hk-cycle')?.value || 'Ctrl+Shift+M',
            zoomIn: document.getElementById('hk-zoomin')?.value || 'Ctrl+Shift+Plus',
            zoomOut: document.getElementById('hk-zoomout')?.value || 'Ctrl+Shift+-'
        },
        notifications: {
            enabled: document.getElementById('notification-react')?.checked || false
        },
        audio: {
            showWaveform: document.getElementById('show-waveform')?.checked !== false,
            showListeningRing: document.getElementById('show-listening-ring')?.checked !== false
        }
    };
}

// Window preset helper
async function applyWindowPreset(value) {
    if (!value) return;
    const [width, height] = value.split(',').map(Number);
    await window.electronAPI.resizeWindow(width, height);
    settings.window.width = width;
    settings.window.height = height;
}

document.getElementById('btn-save').addEventListener('click', async () => {
    const newSettings = collectSettings();
    await window.electronAPI.saveSettings(newSettings);
    window.close();
});

document.getElementById('btn-reset').addEventListener('click', async () => {
    if (confirm('Reset all settings to defaults?')) {
        await window.electronAPI.resetSettings();
        settings = await window.electronAPI.getSettings();
        renderAllTabs();
    }
});

// Initialize
loadSettings();

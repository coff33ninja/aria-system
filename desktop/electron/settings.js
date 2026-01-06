/**
 * Aria Desktop Settings UI
 * Enhanced with accessibility and real-time updates
 */

let settings = null;
let monitors = [];
let updateTimeout = null;

// Debounced settings update function
function debouncedSettingsUpdate(changedSettings, delay = 300) {
    if (updateTimeout) {
        clearTimeout(updateTimeout);
    }
    
    updateTimeout = setTimeout(() => {
        if (window.electronAPI) {
            window.electronAPI.changeSettings(changedSettings);
        }
    }, delay);
}

// Tab switching with keyboard support
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    tab.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            switchTab(tab.dataset.tab);
        }
        // Arrow key navigation
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            const tabs = Array.from(document.querySelectorAll('.tab'));
            const currentIndex = tabs.indexOf(tab);
            const nextIndex = e.key === 'ArrowRight' 
                ? (currentIndex + 1) % tabs.length 
                : (currentIndex - 1 + tabs.length) % tabs.length;
            tabs[nextIndex].focus();
            switchTab(tabs[nextIndex].dataset.tab);
        }
    });
});

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    const activeContent = document.getElementById(tabName);
    
    activeTab.classList.add('active');
    activeTab.setAttribute('aria-selected', 'true');
    activeContent.classList.add('active');
    
    // Announce tab change to screen readers
    announceToScreenReader(`Switched to ${activeTab.textContent} tab`);
}

// Load settings from main process
async function loadSettings() {
    settings = await window.electronAPI.getSettings();
    monitors = await window.electronAPI.getMonitors();
    renderAllTabs();
    
    // Set up real-time settings synchronization
    if (window.electronAPI.onSettingsUpdated) {
        window.electronAPI.onSettingsUpdated((newSettings) => {
            settings = newSettings;
            updateAllControls();
        });
    }
}

function updateAllControls() {
    // Update all form controls to reflect current settings
    updateControlValue('default-maid', settings.avatar?.currentMaid);
    updateControlValue('start-minimized', settings.window?.startMinimized);
    updateControlValue('always-on-top', settings.window?.alwaysOnTop);
    updateControlValue('opacity', Math.round((settings.window?.opacity || 1) * 100));
    updateControlValue('model-scale', Math.round((settings.avatar?.modelScale || 1) * 100));
    updateControlValue('focus-mode', settings.avatar?.focusMode);
    updateControlValue('model-offset', Math.round((settings.avatar?.modelOffsetY || 0) * 100));
    updateControlValue('movement-mode', settings.avatar?.movementMode);
    updateControlValue('tracking-speed', Math.round((settings.avatar?.trackingSpeed || 0.5) * 100));
    updateControlValue('auto-hide-enabled', settings.autoHide?.enabled);
    updateControlValue('auto-hide-minutes', settings.autoHide?.inactivityMinutes);
    updateControlValue('hide-fullscreen', settings.autoHide?.hideInFullscreen);
    
    // Update display values
    updateDisplayValues();
}

function updateControlValue(id, value) {
    const element = document.getElementById(id);
    if (!element) return;
    
    if (element.type === 'checkbox') {
        element.checked = Boolean(value);
    } else if (element.type === 'range') {
        element.value = value || 0;
    } else {
        element.value = value || '';
    }
}

function updateDisplayValues() {
    // Update percentage displays
    const opacitySlider = document.getElementById('opacity');
    const opacityDisplay = opacitySlider?.nextElementSibling;
    if (opacitySlider && opacityDisplay) {
        opacityDisplay.textContent = `${opacitySlider.value}%`;
    }
    
    const scaleSlider = document.getElementById('model-scale');
    const scaleDisplay = scaleSlider?.nextElementSibling;
    if (scaleSlider && scaleDisplay) {
        scaleDisplay.textContent = `${scaleSlider.value}%`;
    }
    
    const offsetSlider = document.getElementById('model-offset');
    const offsetDisplay = offsetSlider?.nextElementSibling;
    if (offsetSlider && offsetDisplay) {
        const value = parseInt(offsetSlider.value);
        offsetDisplay.textContent = value > 0 ? 'Down' : value < 0 ? 'Up' : 'Center';
    }
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
                <select id="default-maid" 
                        aria-label="Default maid selection"
                        aria-describedby="maid-help">
                    <option value="aria" ${settings.avatar?.currentMaid === 'aria' ? 'selected' : ''}>Aria (Head Maid)</option>
                    <option value="luna" ${settings.avatar?.currentMaid === 'luna' ? 'selected' : ''}>Luna (Entertainment)</option>
                </select>
                <div id="maid-help" class="sr-only">Select which maid will be active when the application starts</div>
            </div>
        </div>
        <div class="section">
            <h3>🚀 Startup</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Start Minimized</span>
                    <small>Start in system tray instead of showing avatar</small>
                </div>
                <label class="toggle" aria-label="Start minimized toggle">
                    <input type="checkbox" 
                           id="start-minimized" 
                           ${settings.window?.startMinimized ? 'checked' : ''}
                           aria-describedby="minimized-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="minimized-help" class="sr-only">When enabled, the application will start hidden in the system tray</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Always on Top</span>
                    <small>Keep avatar above other windows</small>
                </div>
                <label class="toggle" aria-label="Always on top toggle">
                    <input type="checkbox" 
                           id="always-on-top" 
                           ${settings.window?.alwaysOnTop ? 'checked' : ''}
                           aria-describedby="ontop-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="ontop-help" class="sr-only">When enabled, the avatar window will stay above all other windows</div>
            </div>
        </div>
    `;
    
    setupGeneralEventListeners();
}

function setupGeneralEventListeners() {
    // Default maid selection with immediate updates
    const maidSelect = document.getElementById('default-maid');
    if (maidSelect) {
        maidSelect.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                avatar: { currentMaid: e.target.value }
            }, 50);
            announceToScreenReader(`Default maid changed to ${e.target.selectedOptions[0].text}`);
        });
    }
    
    // Start minimized toggle with immediate updates
    const minimizedToggle = document.getElementById('start-minimized');
    if (minimizedToggle) {
        minimizedToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                window: { startMinimized: e.target.checked }
            }, 50);
            announceToScreenReader(`Start minimized ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // Always on top toggle with immediate updates
    const onTopToggle = document.getElementById('always-on-top');
    if (onTopToggle) {
        onTopToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                window: { alwaysOnTop: e.target.checked }
            }, 50);
            announceToScreenReader(`Always on top ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
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
                <select id="window-preset" 
                        aria-label="Window size preset"
                        onchange="applyWindowPreset(this.value)">
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
                <input type="range" 
                       id="opacity" 
                       min="30" 
                       max="100" 
                       value="${Math.round((settings.window?.opacity || 1) * 100)}"
                       aria-label="Window opacity percentage"
                       aria-describedby="opacity-value">
                <span id="opacity-value" aria-live="polite">${Math.round((settings.window?.opacity || 1) * 100)}%</span>
            </div>
        </div>
        <div class="section">
            <h3>👤 Character Display</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Character Size</span>
                    <small id="scale-description">Scale: ${Math.round((settings.avatar?.modelScale || 1) * 100)}%</small>
                </div>
                <input type="range" 
                       id="model-scale" 
                       min="50" 
                       max="200" 
                       value="${Math.round((settings.avatar?.modelScale || 1) * 100)}"
                       aria-label="Character size percentage"
                       aria-describedby="scale-value">
                <span id="scale-value" aria-live="polite">${Math.round((settings.avatar?.modelScale || 1) * 100)}%</span>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Focus Mode</span>
                    <small>What part of character to show</small>
                </div>
                <select id="focus-mode" aria-label="Character focus mode">
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
                <input type="range" 
                       id="model-offset" 
                       min="-100" 
                       max="100" 
                       value="${Math.round((settings.avatar?.modelOffsetY || 0) * 100)}"
                       aria-label="Character vertical position"
                       aria-describedby="offset-value">
                <span id="offset-value" aria-live="polite">${settings.avatar?.modelOffsetY > 0 ? 'Down' : settings.avatar?.modelOffsetY < 0 ? 'Up' : 'Center'}</span>
            </div>
        </div>
        <div class="section">
            <h3>🖥️ Monitor Selection</h3>
            <div class="monitor-list" id="monitor-list" role="list" aria-label="Available monitors"></div>
        </div>
    `;
    
    renderMonitorList();
    setupDisplayEventListeners();
}

function setupDisplayEventListeners() {
    // Opacity slider with real-time updates
    const opacitySlider = document.getElementById('opacity');
    if (opacitySlider) {
        opacitySlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            const display = document.getElementById('opacity-value');
            if (display) display.textContent = `${value}%`;
            
            // Real-time update
            debouncedSettingsUpdate({
                window: { opacity: value / 100 }
            }, 100);
        });
    }
    
    // Model scale slider with real-time updates
    const scaleSlider = document.getElementById('model-scale');
    if (scaleSlider) {
        scaleSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            const display = document.getElementById('scale-value');
            const description = document.getElementById('scale-description');
            if (display) display.textContent = `${value}%`;
            if (description) description.textContent = `Scale: ${value}%`;
            
            // Real-time update
            debouncedSettingsUpdate({
                avatar: { modelScale: value / 100 }
            }, 100);
        });
    }
    
    // Model offset slider with real-time updates
    const offsetSlider = document.getElementById('model-offset');
    if (offsetSlider) {
        offsetSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            const display = document.getElementById('offset-value');
            if (display) {
                display.textContent = value > 0 ? 'Down' : value < 0 ? 'Up' : 'Center';
            }
            
            // Real-time update
            debouncedSettingsUpdate({
                avatar: { modelOffsetY: value / 100 }
            }, 100);
        });
    }
    
    // Focus mode dropdown with immediate updates
    const focusSelect = document.getElementById('focus-mode');
    if (focusSelect) {
        focusSelect.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                avatar: { focusMode: e.target.value }
            }, 50);
        });
    }
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
                <select id="movement-mode" 
                        aria-label="Avatar movement mode"
                        aria-describedby="movement-help">
                    ${modes.map(m => `<option value="${m}" ${(settings.avatar?.movementMode || 'idle') === m ? 'selected' : ''}>${m === 'follow' ? 'Follow Active Window' : m.charAt(0).toUpperCase() + m.slice(1)}</option>`).join('')}
                </select>
                <div id="movement-help" class="sr-only">Select how the avatar should move and track</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Tracking Speed</span>
                    <small>How fast avatar follows mouse/camera</small>
                </div>
                <input type="range" 
                       id="tracking-speed" 
                       min="10" 
                       max="100" 
                       value="${Math.round((settings.avatar?.trackingSpeed || 0.5) * 100)}"
                       aria-label="Tracking speed percentage"
                       aria-describedby="speed-value">
                <span id="speed-value" aria-live="polite">${Math.round((settings.avatar?.trackingSpeed || 0.5) * 100)}%</span>
            </div>
        </div>
        <div class="section">
            <h3>👁️ Auto-Hide</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Enable Auto-Hide</span>
                    <small>Hide avatar after inactivity</small>
                </div>
                <label class="toggle" aria-label="Auto-hide toggle">
                    <input type="checkbox" 
                           id="auto-hide-enabled" 
                           ${settings.autoHide?.enabled ? 'checked' : ''}
                           aria-describedby="autohide-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="autohide-help" class="sr-only">Automatically hide the avatar after a period of inactivity</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Inactivity Timeout</span>
                    <small>Minutes before hiding</small>
                </div>
                <input type="number" 
                       id="auto-hide-minutes" 
                       min="1" 
                       max="60" 
                       value="${settings.autoHide?.inactivityMinutes || 5}" 
                       style="width:80px"
                       aria-label="Auto-hide timeout in minutes"
                       aria-describedby="timeout-help">
                <div id="timeout-help" class="sr-only">Number of minutes of inactivity before hiding the avatar</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Hide in Fullscreen</span>
                    <small>Auto-hide when apps go fullscreen</small>
                </div>
                <label class="toggle" aria-label="Hide in fullscreen toggle">
                    <input type="checkbox" 
                           id="hide-fullscreen" 
                           ${settings.autoHide?.hideInFullscreen ? 'checked' : ''}
                           aria-describedby="fullscreen-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="fullscreen-help" class="sr-only">Hide the avatar when other applications enter fullscreen mode</div>
            </div>
        </div>
    `;
    
    setupMovementEventListeners();
}

function setupMovementEventListeners() {
    // Movement mode selection with immediate updates
    const movementSelect = document.getElementById('movement-mode');
    if (movementSelect) {
        movementSelect.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                avatar: { movementMode: e.target.value }
            }, 50);
            announceToScreenReader(`Movement mode changed to ${e.target.selectedOptions[0].text}`);
        });
    }
    
    // Tracking speed slider with real-time updates
    const speedSlider = document.getElementById('tracking-speed');
    if (speedSlider) {
        speedSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            const display = document.getElementById('speed-value');
            if (display) display.textContent = `${value}%`;
            
            debouncedSettingsUpdate({
                avatar: { trackingSpeed: value / 100 }
            }, 100);
        });
    }
    
    // Auto-hide enabled toggle
    const autoHideToggle = document.getElementById('auto-hide-enabled');
    if (autoHideToggle) {
        autoHideToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                autoHide: { enabled: e.target.checked }
            }, 50);
            announceToScreenReader(`Auto-hide ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // Auto-hide timeout input
    const timeoutInput = document.getElementById('auto-hide-minutes');
    if (timeoutInput) {
        timeoutInput.addEventListener('change', (e) => {
            const value = parseInt(e.target.value);
            if (value >= 1 && value <= 60) {
                debouncedSettingsUpdate({
                    autoHide: { inactivityMinutes: value }
                }, 200);
                announceToScreenReader(`Auto-hide timeout set to ${value} minutes`);
            }
        });
    }
    
    // Hide in fullscreen toggle
    const fullscreenToggle = document.getElementById('hide-fullscreen');
    if (fullscreenToggle) {
        fullscreenToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                autoHide: { hideInFullscreen: e.target.checked }
            }, 50);
            announceToScreenReader(`Hide in fullscreen ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
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
                <div class="setting-label">
                    <span>Toggle Visibility</span>
                    <small>Show or hide the avatar window</small>
                </div>
                <div class="hotkey-input">
                    <input type="text" 
                           id="hk-toggle" 
                           value="${hotkeys.toggleVisibility}" 
                           readonly
                           aria-label="Toggle visibility hotkey"
                           aria-describedby="toggle-help">
                    <button class="btn btn-secondary" 
                            onclick="recordHotkey('hk-toggle')"
                            aria-describedby="record-help">
                        Record
                    </button>
                </div>
                <div id="toggle-help" class="sr-only">Current hotkey for toggling avatar visibility</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Cycle Maids</span>
                    <small>Switch between available maids</small>
                </div>
                <div class="hotkey-input">
                    <input type="text" 
                           id="hk-cycle" 
                           value="${hotkeys.cycleMaid}" 
                           readonly
                           aria-label="Cycle maids hotkey">
                    <button class="btn btn-secondary" 
                            onclick="recordHotkey('hk-cycle')">
                        Record
                    </button>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Zoom In</span>
                    <small>Increase character size</small>
                </div>
                <div class="hotkey-input">
                    <input type="text" 
                           id="hk-zoomin" 
                           value="${hotkeys.zoomIn}" 
                           readonly
                           aria-label="Zoom in hotkey">
                    <button class="btn btn-secondary" 
                            onclick="recordHotkey('hk-zoomin')">
                        Record
                    </button>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Zoom Out</span>
                    <small>Decrease character size</small>
                </div>
                <div class="hotkey-input">
                    <input type="text" 
                           id="hk-zoomout" 
                           value="${hotkeys.zoomOut}" 
                           readonly
                           aria-label="Zoom out hotkey">
                    <button class="btn btn-secondary" 
                            onclick="recordHotkey('hk-zoomout')">
                        Record
                    </button>
                </div>
            </div>
            <div id="record-help" class="sr-only">Click Record and then press the key combination you want to use</div>
        </div>
    `;
}

function renderAdvancedTab() {
    const container = document.getElementById('advanced');
    container.innerHTML = `
        <div class="section">
            <h3>🖱️ Modifier Controls</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Enable Modifier Controls</span>
                    <small>Ctrl+drag to move window, Ctrl+scroll to resize character</small>
                </div>
                <label class="toggle" aria-label="Modifier controls toggle">
                    <input type="checkbox" 
                           id="modifier-controls" 
                           ${settings.controls?.modifierDragEnabled !== false ? 'checked' : ''}
                           aria-describedby="modifier-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="modifier-help" class="sr-only">Enable Ctrl+drag to move window and Ctrl+scroll to resize character</div>
            </div>
        </div>
        <div class="section">
            <h3>📷 Camera Tracking</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Use Advanced Detection</span>
                    <small>MediaPipe for better face tracking (loads ~2MB)</small>
                </div>
                <label class="toggle" aria-label="Advanced face detection toggle">
                    <input type="checkbox" 
                           id="use-mediapipe" 
                           ${settings.avatar?.useMediaPipe ? 'checked' : ''}
                           aria-describedby="mediapipe-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="mediapipe-help" class="sr-only">Use MediaPipe for more accurate face tracking, requires downloading additional data</div>
            </div>
        </div>
        <div class="section">
            <h3>🔔 Notifications</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>React to Notifications</span>
                    <small>Avatar reacts when you receive notifications</small>
                </div>
                <label class="toggle" aria-label="Notification reactions toggle">
                    <input type="checkbox" 
                           id="notification-react" 
                           ${settings.notifications?.enabled ? 'checked' : ''}
                           aria-describedby="notification-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="notification-help" class="sr-only">Make the avatar react with expressions when system notifications appear</div>
            </div>
        </div>
        <div class="section">
            <h3>🎵 Audio Visualization</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Show Waveform</span>
                    <small>Display audio waveform when speaking</small>
                </div>
                <label class="toggle" aria-label="Audio waveform toggle">
                    <input type="checkbox" 
                           id="show-waveform" 
                           ${settings.audio?.showWaveform !== false ? 'checked' : ''}
                           aria-describedby="waveform-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="waveform-help" class="sr-only">Display visual waveform animation when the avatar is speaking</div>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Show Listening Ring</span>
                    <small>Pulsing ring when listening for input</small>
                </div>
                <label class="toggle" aria-label="Listening ring toggle">
                    <input type="checkbox" 
                           id="show-listening-ring" 
                           ${settings.audio?.showListeningRing !== false ? 'checked' : ''}
                           aria-describedby="listening-help">
                    <span class="toggle-slider" role="presentation"></span>
                </label>
                <div id="listening-help" class="sr-only">Show a pulsing ring animation when the avatar is listening for voice input</div>
            </div>
        </div>
        <div class="section">
            <h3>💾 Data</h3>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Settings Location</span>
                    <small id="settings-path">Loading...</small>
                </div>
                <button class="btn btn-secondary" 
                        onclick="openSettingsFolder()"
                        aria-label="Open settings folder in file explorer">
                    Open Folder
                </button>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Export Settings</span>
                    <small>Save settings to a file</small>
                </div>
                <button class="btn btn-secondary" 
                        onclick="exportSettings()"
                        aria-label="Export current settings to a JSON file">
                    Export
                </button>
            </div>
            <div class="setting-row">
                <div class="setting-label">
                    <span>Import Settings</span>
                    <small>Load settings from a file</small>
                </div>
                <button class="btn btn-secondary" 
                        onclick="importSettings()"
                        aria-label="Import settings from a JSON file">
                    Import
                </button>
            </div>
        </div>
    `;
    
    loadSettingsPath();
    setupAdvancedEventListeners();
}

function setupAdvancedEventListeners() {
    // Modifier controls toggle
    const modifierToggle = document.getElementById('modifier-controls');
    if (modifierToggle) {
        modifierToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                controls: { modifierDragEnabled: e.target.checked }
            }, 50);
            announceToScreenReader(`Modifier controls ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // MediaPipe toggle
    const mediaPipeToggle = document.getElementById('use-mediapipe');
    if (mediaPipeToggle) {
        mediaPipeToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                avatar: { useMediaPipe: e.target.checked }
            }, 50);
            announceToScreenReader(`Advanced face detection ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // Notification reactions toggle
    const notificationToggle = document.getElementById('notification-react');
    if (notificationToggle) {
        notificationToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                notifications: { enabled: e.target.checked }
            }, 50);
            announceToScreenReader(`Notification reactions ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // Show waveform toggle
    const waveformToggle = document.getElementById('show-waveform');
    if (waveformToggle) {
        waveformToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                audio: { showWaveform: e.target.checked }
            }, 50);
            announceToScreenReader(`Audio waveform ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
    
    // Show listening ring toggle
    const listeningToggle = document.getElementById('show-listening-ring');
    if (listeningToggle) {
        listeningToggle.addEventListener('change', (e) => {
            debouncedSettingsUpdate({
                audio: { showListeningRing: e.target.checked }
            }, 50);
            announceToScreenReader(`Listening ring ${e.target.checked ? 'enabled' : 'disabled'}`);
        });
    }
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
        },
        controls: {
            modifierDragEnabled: document.getElementById('modifier-controls')?.checked !== false
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

// Enhanced save and reset button handlers with accessibility
document.getElementById('btn-save').addEventListener('click', async () => {
    try {
        const newSettings = collectSettings();
        await window.electronAPI.saveSettings(newSettings);
        announceToScreenReader('Settings saved successfully');
        window.close();
    } catch (error) {
        console.error('Failed to save settings:', error);
        announceToScreenReader('Failed to save settings');
    }
});

document.getElementById('btn-reset').addEventListener('click', async () => {
    if (confirm('Reset all settings to defaults? This cannot be undone.')) {
        try {
            await window.electronAPI.resetSettings();
            settings = await window.electronAPI.getSettings();
            renderAllTabs();
            announceToScreenReader('Settings reset to defaults');
        } catch (error) {
            console.error('Failed to reset settings:', error);
            announceToScreenReader('Failed to reset settings');
        }
    }
});

// Initialize
loadSettings();

// Accessibility helper functions
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.cssText = `
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    `;
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
        if (document.body.contains(announcement)) {
            document.body.removeChild(announcement);
        }
    }, 1000);
}

// Keyboard navigation setup
document.addEventListener('keydown', (e) => {
    // Global keyboard shortcuts
    if (e.key === 'Escape') {
        // Close settings window
        window.close();
    }
    
    if (e.altKey && e.key === 'h') {
        // Show keyboard help
        e.preventDefault();
        showKeyboardHelp();
    }
});

function showKeyboardHelp() {
    const helpText = `
Keyboard Shortcuts:
- Tab/Shift+Tab: Navigate between controls
- Arrow keys: Navigate between tabs
- Enter/Space: Activate buttons and toggles
- Escape: Close settings
- Alt+H: Show this help
    `.trim();
    
    announceToScreenReader(helpText);
    alert(helpText); // Simple modal for now
}

// Enhanced error handling
window.addEventListener('error', (e) => {
    console.error('Settings UI error:', e.error);
    announceToScreenReader('An error occurred in the settings interface');
});

// Focus management
document.addEventListener('focusin', (e) => {
    // Ensure focused elements are visible
    e.target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});

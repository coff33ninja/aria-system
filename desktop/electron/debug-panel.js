/**
 * Aria Live2D Debug Panel
 * 
 * Provides advanced controls for Live2D model debugging and testing
 */

import { ModelInfoPanel, MODEL_INFO_PANEL_STYLES } from './components/ModelInfoPanel.js';

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = MODEL_INFO_PANEL_STYLES;
document.head.appendChild(styleSheet);

// State
let isDocked = false;
let currentMaid = null;
let parameters = new Map();
let animations = [];
let performanceHistory = [];
let modelInfoPanel = null;

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Header controls
document.getElementById('btn-import').addEventListener('click', importConfiguration);
document.getElementById('btn-export').addEventListener('click', exportConfiguration);
document.getElementById('btn-dock').addEventListener('click', toggleDock);
document.getElementById('btn-close').addEventListener('click', () => {
    window.close();
});

function toggleDock() {
    isDocked = !isDocked;
    const btn = document.getElementById('btn-dock');
    btn.textContent = isDocked ? '📌 Undock' : '📌 Dock';
    
    // Send dock state to main process
    if (window.electronAPI) {
        window.electronAPI.send('debug-panel-dock', isDocked);
    }
}

// Parameters Tab
function initializeParameters() {
    const paramList = document.getElementById('param-list');
    
    // Default Live2D parameters
    const defaultParams = [
        'ParamEyeLOpen', 'ParamEyeROpen',
        'ParamEyeBallX', 'ParamEyeBallY',
        'ParamMouthOpenY', 'ParamMouthForm',
        'ParamAngleX', 'ParamAngleY', 'ParamAngleZ',
        'ParamBodyAngleX', 'ParamBodyAngleY', 'ParamBodyAngleZ',
        'ParamBreath', 'ParamBrowLY', 'ParamBrowRY'
    ];
    
    defaultParams.forEach(paramName => {
        const value = 0.0;
        parameters.set(paramName, value);
        addParameterControl(paramName, value);
    });
}

function addParameterControl(paramName, initialValue) {
    const paramList = document.getElementById('param-list');
    
    const item = document.createElement('div');
    item.className = 'param-item';
    item.dataset.paramName = paramName;
    
    item.innerHTML = `
        <span class="param-name" title="${paramName}">${paramName}</span>
        <input type="range" class="param-slider" min="-100" max="100" value="${initialValue * 100}" 
            data-param="${paramName}">
        <span class="param-value">${initialValue.toFixed(2)}</span>
    `;
    
    const slider = item.querySelector('.param-slider');
    const valueSpan = item.querySelector('.param-value');
    
    slider.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value) / 100;
        valueSpan.textContent = value.toFixed(2);
        parameters.set(paramName, value);
        sendParameterUpdate(paramName, value);
    });
    
    paramList.appendChild(item);
}

function sendParameterUpdate(paramName, value) {
    if (window.electronAPI) {
        window.electronAPI.send('debug-parameter-update', {
            parameter: paramName,
            value: value
        });
    }
}

// Parameter search
document.getElementById('param-search').addEventListener('input', (e) => {
    const search = e.target.value.toLowerCase();
    document.querySelectorAll('.param-item').forEach(item => {
        const paramName = item.dataset.paramName.toLowerCase();
        item.style.display = paramName.includes(search) ? 'flex' : 'none';
    });
});

// Reset all parameters
document.getElementById('btn-reset-params').addEventListener('click', () => {
    document.querySelectorAll('.param-slider').forEach(slider => {
        slider.value = 0;
        const paramName = slider.dataset.param;
        const valueSpan = slider.parentElement.querySelector('.param-value');
        valueSpan.textContent = '0.00';
        parameters.set(paramName, 0.0);
        sendParameterUpdate(paramName, 0.0);
    });
});

// Viewport Controls
const viewportState = {
    x: 0,
    y: 0,
    zoom: 1.0,
    rotation: 0
};

document.getElementById('btn-pan-up').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'pan', dx: 0, dy: -50 });
    }
});

document.getElementById('btn-pan-down').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'pan', dx: 0, dy: 50 });
    }
});

document.getElementById('btn-pan-left').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'pan', dx: -50, dy: 0 });
    }
});

document.getElementById('btn-pan-right').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'pan', dx: 50, dy: 0 });
    }
});

document.getElementById('btn-zoom-in').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'zoom', factor: 1.2 });
    }
});

document.getElementById('btn-zoom-out').addEventListener('click', () => {
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'zoom', factor: 0.8 });
    }
});

document.getElementById('btn-rotate-left').addEventListener('click', () => {
    viewportState.rotation -= 15;
    updateViewportDisplay();
});

document.getElementById('btn-rotate-right').addEventListener('click', () => {
    viewportState.rotation += 15;
    updateViewportDisplay();
});

document.getElementById('btn-reset-view').addEventListener('click', () => {
    viewportState.x = 0;
    viewportState.y = 0;
    viewportState.zoom = 1.0;
    viewportState.rotation = 0;
    updateViewportDisplay();
    
    if (window.electronAPI) {
        window.electronAPI.send('debug-viewport-update', { action: 'reset' });
    }
});

function updateViewportDisplay() {
    document.getElementById('viewport-pos').textContent = `${viewportState.x.toFixed(0)}, ${viewportState.y.toFixed(0)}`;
    document.getElementById('viewport-zoom').textContent = `${(viewportState.zoom * 100).toFixed(0)}%`;
    document.getElementById('viewport-rotation').textContent = `${viewportState.rotation.toFixed(0)}°`;
}

// Animations Tab
function initializeAnimations() {
    const animList = document.getElementById('animation-list');
    
    // Default animations (will be populated from model)
    const defaultAnimations = [
        'Idle', 'TapBody', 'PinchIn', 'PinchOut', 'Shake'
    ];
    
    defaultAnimations.forEach(animName => {
        addAnimationControl(animName);
    });
}

function addAnimationControl(animName) {
    const animList = document.getElementById('animation-list');
    
    const item = document.createElement('div');
    item.className = 'animation-item';
    
    item.innerHTML = `
        <span class="animation-name">${animName}</span>
        <div class="animation-controls">
            <button class="anim-btn" data-action="play" data-anim="${animName}">▶️ Play</button>
            <button class="anim-btn" data-action="pause" data-anim="${animName}">⏸️ Pause</button>
            <button class="anim-btn" data-action="stop" data-anim="${animName}">⏹️ Stop</button>
        </div>
    `;
    
    item.querySelectorAll('.anim-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            const anim = e.target.dataset.anim;
            sendAnimationCommand(anim, action);
        });
    });
    
    animList.appendChild(item);
}

function sendAnimationCommand(animName, action) {
    if (window.electronAPI) {
        window.electronAPI.send('debug-animation-command', {
            action: action === 'play' ? 'play' : 'stop',
            group: animName,
            index: 0
        });
    }
}

// Grid Controls
document.getElementById('grid-enabled').addEventListener('change', (e) => {
    sendGridUpdate({ enabled: e.target.checked });
});

document.getElementById('grid-type').addEventListener('change', (e) => {
    sendGridUpdate({ type: e.target.value });
});

document.getElementById('grid-spacing').addEventListener('input', (e) => {
    const value = e.target.value;
    document.getElementById('grid-spacing-value').textContent = `${value}px`;
    sendGridUpdate({ spacing: parseInt(value) });
});

document.getElementById('grid-opacity').addEventListener('input', (e) => {
    const value = e.target.value;
    document.getElementById('grid-opacity-value').textContent = `${value}%`;
    sendGridUpdate({ opacity: parseInt(value) / 100 });
});

document.getElementById('grid-color').addEventListener('change', (e) => {
    sendGridUpdate({ color: e.target.value });
});

function sendGridUpdate(changes) {
    if (window.electronAPI) {
        window.electronAPI.send('debug-grid-update', changes);
    }
}

// Performance Monitoring
let lastFrameTime = performance.now();
let frameCount = 0;
let fps = 60;

function updatePerformanceMetrics() {
    const now = performance.now();
    const delta = now - lastFrameTime;
    lastFrameTime = now;
    
    frameCount++;
    if (frameCount >= 10) {
        fps = Math.round(1000 / delta);
        frameCount = 0;
    }
    
    // Update display
    document.getElementById('perf-fps').textContent = fps;
    document.getElementById('perf-frametime').textContent = `${delta.toFixed(1)}ms`;
    
    // Update memory if available
    if (performance.memory) {
        const memoryMB = (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(1);
        document.getElementById('perf-memory').textContent = `${memoryMB}MB`;
    }
    
    // Update graph
    performanceHistory.push(fps);
    if (performanceHistory.length > 60) {
        performanceHistory.shift();
    }
    drawPerformanceGraph();
    
    requestAnimationFrame(updatePerformanceMetrics);
}

function drawPerformanceGraph() {
    const canvas = document.getElementById('perf-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    // Clear
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw graph
    ctx.strokeStyle = '#ff6b9d';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    const step = canvas.width / performanceHistory.length;
    performanceHistory.forEach((value, index) => {
        const x = index * step;
        const y = canvas.height - (value / 60 * canvas.height);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Draw 60 FPS line
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(canvas.width, 0);
    ctx.stroke();
}

// Model Info
function updateModelInfo(info) {
    // Initialize ModelInfoPanel if not already created
    if (!modelInfoPanel) {
        modelInfoPanel = new ModelInfoPanel('model-info-container');
    }
    
    // Update with new info
    if (info) {
        modelInfoPanel.updateModelInfo(info);
    } else {
        modelInfoPanel.clear();
    }
}

// IPC Communication
if (window.electronAPI) {
    // Listen for model updates
    window.electronAPI.on('model-loaded', (data) => {
        currentMaid = data.maidName;
        
        // Extract and update model info
        if (data.live2dModel) {
            const extractedInfo = modelInfoPanel ? 
                modelInfoPanel.extractModelInfo(data.live2dModel) : 
                null;
            updateModelInfo(extractedInfo || data.modelInfo);
        } else {
            updateModelInfo(data.modelInfo);
        }
        
        // Update parameters if provided
        if (data.parameters) {
            parameters.clear();
            document.getElementById('param-list').innerHTML = '';
            
            data.parameters.forEach(param => {
                parameters.set(param.name, param.value);
                addParameterControl(param.name, param.value);
            });
        }
        
        // Update animations if provided
        if (data.animations) {
            document.getElementById('animation-list').innerHTML = '';
            data.animations.forEach(anim => {
                addAnimationControl(anim);
            });
        }
    });
    
    // Listen for parameter updates from main window
    window.electronAPI.on('parameter-changed', (data) => {
        const slider = document.querySelector(`[data-param="${data.parameter}"]`);
        if (slider) {
            slider.value = data.value * 100;
            const valueSpan = slider.parentElement.querySelector('.param-value');
            valueSpan.textContent = data.value.toFixed(2);
            parameters.set(data.parameter, data.value);
        }
    });
}

// Initialize
initializeParameters();
initializeAnimations();
updatePerformanceMetrics();

console.log('🔧 Debug panel initialized');

// ============ Import/Export Functionality ============

/**
 * Export current configuration
 */
function exportConfiguration() {
    try {
        // Collect all current state
        const config = {
            metadata: {
                timestamp: new Date().toISOString(),
                version: '1.0.0',
                maid: currentMaid || 'unknown'
            },
            parameters: Object.fromEntries(parameters),
            viewport: { ...viewportState },
            grid: {
                enabled: document.getElementById('grid-enabled').checked,
                type: document.getElementById('grid-type').value,
                spacing: parseInt(document.getElementById('grid-spacing').value),
                opacity: parseInt(document.getElementById('grid-opacity').value) / 100,
                color: document.getElementById('grid-color').value
            }
        };
        
        // Create download
        const json = JSON.stringify(config, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `live2d-config-${currentMaid || 'unknown'}-${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        
        console.log('✅ Configuration exported');
        
    } catch (error) {
        console.error('❌ Export failed:', error);
        alert(`Failed to export configuration: ${error.message}`);
    }
}

/**
 * Import configuration from file
 */
function importConfiguration() {
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            try {
                const file = e.target.files[0];
                if (!file) return;
                
                const text = await file.text();
                const config = JSON.parse(text);
                
                // Validate config structure
                if (!config.metadata || !config.parameters) {
                    throw new Error('Invalid configuration file');
                }
                
                // Apply parameters
                if (config.parameters) {
                    for (const [paramName, value] of Object.entries(config.parameters)) {
                        const slider = document.querySelector(`[data-param="${paramName}"]`);
                        if (slider) {
                            slider.value = value * 100;
                            const valueSpan = slider.parentElement.querySelector('.param-value');
                            valueSpan.textContent = value.toFixed(2);
                            parameters.set(paramName, value);
                            sendParameterUpdate(paramName, value);
                        }
                    }
                }
                
                // Apply viewport
                if (config.viewport) {
                    Object.assign(viewportState, config.viewport);
                    updateViewportDisplay();
                    if (window.electronAPI) {
                        window.electronAPI.send('debug-viewport-update', { action: 'reset' });
                    }
                }
                
                // Apply grid settings
                if (config.grid) {
                    document.getElementById('grid-enabled').checked = config.grid.enabled || false;
                    document.getElementById('grid-type').value = config.grid.type || 'lines';
                    document.getElementById('grid-spacing').value = config.grid.spacing || 50;
                    document.getElementById('grid-opacity').value = (config.grid.opacity || 0.3) * 100;
                    document.getElementById('grid-color').value = config.grid.color || '#ffffff';
                    
                    // Update displays
                    document.getElementById('grid-spacing-value').textContent = `${config.grid.spacing || 50}px`;
                    document.getElementById('grid-opacity-value').textContent = `${Math.round((config.grid.opacity || 0.3) * 100)}%`;
                    
                    // Send updates
                    sendGridUpdate(config.grid);
                }
                
                console.log('✅ Configuration imported');
                
            } catch (error) {
                console.error('❌ Import failed:', error);
                alert(`Failed to import configuration: ${error.message}`);
            }
        };
        
        input.click();
        
    } catch (error) {
        console.error('❌ Import failed:', error);
        alert(`Failed to import configuration: ${error.message}`);
    }
}

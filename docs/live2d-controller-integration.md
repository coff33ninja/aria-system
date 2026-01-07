# Live2D Controller Integration Guide

## Overview

The new `Live2DController` class provides enhanced Live2D rendering with features from the perplexity renderer:

- ✅ **Version-aware idle motion detection** (Cubism 2 vs 4)
- ✅ **Dynamic click-through window** (desktop mascot mode)
- ✅ **Hit area detection** for tap interactions
- ✅ **Motion priority system** (IDLE < NORMAL < FORCE)
- ✅ **Circular hit detection** for accurate click-through
- ✅ **Built-in focus helper** for mouse tracking
- ✅ **Expression management** with fade transitions

## Quick Start

### 1. Include the Controller

Add to your HTML (after PIXI and Live2D libraries):

```html
<!-- In desktop/frontend/avatar.html or index.html -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/pixi.js/6.5.10/browser/pixi.min.js"></script>
<script src="https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js"></script>

<!-- New controller -->
<script src="live2d-controller.js"></script>
<script src="app.js"></script>
```

### 2. Initialize the Controller

```javascript
// In desktop/frontend/app.js
const canvas = document.getElementById('live2d-canvas');

// Create controller with options
const live2dController = new Live2DController(canvas, {
    zoomMin: 0.5,
    zoomMax: 2.0,
    hitRadius: 0.4  // 40% of canvas size
});

// Load a model
async function loadMaid(maidId) {
    try {
        const modelPath = await window.electronAPI.getAbsoluteModelPath(
            maidId, 
            `${maidId}.model3.json`
        );
        
        const info = await live2dController.loadModel(modelPath, maidId);
        console.log('Model loaded:', info);
        
        // Model info includes:
        // - name: Model name
        // - version: Cubism 2 or Cubism 4+
        // - motions: Array of available motions
        // - expressions: Array of available expressions
        // - hitAreas: Array of hit area names
        
    } catch (error) {
        console.error('Failed to load model:', error);
    }
}

// Load initial model
loadMaid('aria');
```

### 3. Enable Click-Through (Desktop Mascot Mode)

The controller automatically handles click-through based on mouse position:

```javascript
// Click-through is automatic!
// - Mouse over model → window accepts clicks
// - Mouse outside model → clicks pass through to desktop

// The controller calls window.electronAPI.setMouseThrough() automatically
// No additional code needed!
```

### 4. Play Motions with Priority

```javascript
// Play idle motion (can be interrupted)
live2dController.playMotion('Idle', 0, 'IDLE');

// Play normal motion (plays fully unless forced)
live2dController.playMotion('TapBody', 0, 'NORMAL');

// Force motion (interrupts everything)
live2dController.playMotion('Surprised', 0, 'FORCE');
```

### 5. Set Expressions

```javascript
// Set expression with automatic fade
live2dController.setExpression('happy');
live2dController.setExpression('heart_eyes');
live2dController.setExpression('sassy');
```

### 6. Control View

```javascript
// Zoom
live2dController.setViewState({ zoom: 1.5 });

// Pan
live2dController.setViewState({ panX: 0.2, panY: -0.1 });

// Rotate
live2dController.setViewState({ rotationDeg: 15 });

// Opacity
live2dController.setViewState({ opacity: 0.8 });

// Multiple at once
live2dController.setViewState({
    zoom: 1.2,
    panX: 0,
    panY: -0.2,
    rotationDeg: 0,
    opacity: 1.0
});
```

## Integration with Existing Code

### Replacing Old Live2D Code

If you have existing Live2D code in `app.js`, here's how to migrate:

#### Before (Old Code):
```javascript
// Old manual PIXI setup
const app = new PIXI.Application({
    view: canvas,
    transparent: true,
    // ...
});

const model = await PIXI.live2d.Live2DModel.from(modelPath);
app.stage.addChild(model);

// Manual mouse tracking
canvas.addEventListener('mousemove', (e) => {
    // Complex manual parameter setting
    model.internalModel.coreModel.setParameterValueById('ParamAngleX', ...);
    // ...
});
```

#### After (New Controller):
```javascript
// New controller handles everything
const controller = new Live2DController(canvas);
await controller.loadModel(modelPath, maidId);

// Mouse tracking is automatic!
// Click-through is automatic!
// Version detection is automatic!
```

### Integration with Expression System

Connect the controller to your existing `expressions.py` system:

```javascript
// In desktop/frontend/app.js

// Listen for expression triggers from Python
window.electronAPI.onTriggerExpression((expression) => {
    console.log('Triggering expression:', expression);
    live2dController.setExpression(expression);
});

// Listen for action triggers
window.electronAPI.onTriggerAction((action) => {
    console.log('Triggering action:', action);
    
    switch (action) {
        case 'wave':
            live2dController.playMotion('Wave', 0, 'NORMAL');
            break;
        case 'blink':
            live2dController.playMotion('Blink', 0, 'NORMAL');
            break;
        case 'nod':
            live2dController.playMotion('Nod', 0, 'NORMAL');
            break;
    }
});
```

### Integration with Settings

Connect to the existing settings system:

```javascript
// Listen for settings changes
window.electronAPI.onSettingsLoaded((settings) => {
    // Apply model scale
    if (settings.avatar.modelScale) {
        live2dController.setViewState({ 
            zoom: settings.avatar.modelScale 
        });
    }
    
    // Apply model offset
    if (settings.avatar.modelOffsetY) {
        live2dController.setViewState({ 
            panY: settings.avatar.modelOffsetY 
        });
    }
    
    // Apply focus mode (affects zoom/pan)
    applyFocusMode(settings.avatar.focusMode);
});

// Listen for model scale changes from tray menu
window.electronAPI.onSetModelScale((scale) => {
    live2dController.setViewState({ zoom: scale });
});

// Listen for model offset changes
window.electronAPI.onSetModelOffset((offset) => {
    live2dController.setViewState({ panY: offset });
});

// Listen for focus mode changes
window.electronAPI.onSetFocusMode((mode) => {
    applyFocusMode(mode);
});

function applyFocusMode(mode) {
    switch (mode) {
        case 'face':
            live2dController.setViewState({ 
                zoom: 1.8, 
                panY: -0.3 
            });
            break;
        case 'upper':
            live2dController.setViewState({ 
                zoom: 1.2, 
                panY: -0.1 
            });
            break;
        case 'full':
            live2dController.setViewState({ 
                zoom: 1.0, 
                panY: 0 
            });
            break;
    }
}
```

### Integration with Maid Switching

```javascript
// Listen for maid switch events
window.electronAPI.onSwitchMaid(async (maidId) => {
    console.log('Switching to maid:', maidId);
    
    // Show loading state
    showLoading(true);
    
    try {
        // Load new maid's model
        await loadMaid(maidId);
        
        // Update UI
        updateCurrentMaidBadge(maidId);
        
        // Play greeting motion
        live2dController.playMotion('Greeting', 0, 'NORMAL');
        
    } catch (error) {
        console.error('Failed to switch maid:', error);
    } finally {
        showLoading(false);
    }
});
```

## Advanced Features

### Custom Hit Detection

Override the default circular hit detection:

```javascript
// Check if point is inside model
const isInside = live2dController.isPointInsideModel(x, y);

// Use for custom interactions
canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (live2dController.isPointInsideModel(x, y)) {
        console.log('Clicked on model!');
        live2dController.playMotion('Tap', 0, 'NORMAL');
    }
});
```

### Motion Callbacks

```javascript
// The controller logs motion events automatically
// Check console for:
// 🎬 Playing motion: Idle[0] (priority: IDLE)
// ✅ Motion finished: Idle[0]
```

### Performance Monitoring

```javascript
// Get model info including FPS
const info = live2dController.getModelInfo();
console.log('FPS:', info.fps);

// Display FPS in UI
setInterval(() => {
    const info = live2dController.getModelInfo();
    document.getElementById('fps-label').textContent = `FPS: ${info.fps.toFixed(1)}`;
}, 500);
```

### View State Persistence

```javascript
// Save view state to settings
function saveViewState() {
    const viewState = live2dController.getViewState();
    window.electronAPI.saveSettings({
        avatar: {
            viewState: viewState
        }
    });
}

// Restore view state from settings
function restoreViewState(settings) {
    if (settings.avatar?.viewState) {
        live2dController.setViewState(settings.avatar.viewState);
    }
}
```

## Troubleshooting

### Model Not Loading

**Problem:** Model fails to load with error

**Solutions:**
1. Check model path is correct
2. Verify model3.json exists
3. Check console for detailed error
4. Ensure all texture files are present
5. Try loading in browser first (without Electron)

```javascript
// Debug model loading
try {
    const info = await live2dController.loadModel(modelPath, maidId);
    console.log('✅ Model loaded successfully:', info);
} catch (error) {
    console.error('❌ Model load failed:', error);
    console.error('Path:', modelPath);
    console.error('Maid:', maidId);
}
```

### Click-Through Not Working

**Problem:** Clicks don't pass through empty areas

**Solutions:**
1. Verify Electron version is 13+ (you have 30.0.0 ✅)
2. Check `setMouseThrough` is being called
3. Adjust hit radius in config
4. Check console for IPC errors

```javascript
// Debug click-through
const controller = new Live2DController(canvas, {
    hitRadius: 0.3  // Try smaller radius
});

// Monitor hover state
canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const inside = controller.isPointInsideModel(x, y);
    console.log('Mouse inside model:', inside);
});
```

### Motions Not Playing

**Problem:** Motions don't play or are cut off

**Solutions:**
1. Check motion name and index are correct
2. Verify motion exists in model
3. Check priority level
4. Look for motion conflicts

```javascript
// Debug motions
const info = live2dController.getModelInfo();
console.log('Available motions:', info.motions);

// Try playing with FORCE priority
live2dController.playMotion('Idle', 0, 'FORCE');
```

### Version Detection Issues

**Problem:** Idle motions don't work

**Solutions:**
1. Check console for version detection message
2. Manually inspect model3.json for motion group names
3. Override idle group if needed

```javascript
// Check detected version
const info = live2dController.getModelInfo();
console.log('Detected version:', info.version);

// If detection fails, check model3.json:
// Cubism 2: "Motions": { "idle": [...] }
// Cubism 4: "Motions": { "Idle": [...] }
```

## Performance Tips

### 1. Preload Common Motions

```javascript
// Load model with idle motion preload (already done by controller)
// This is automatic in Live2DController!
```

### 2. Throttle Mouse Events

```javascript
// The controller already uses requestAnimationFrame
// No additional throttling needed!
```

### 3. Pause When Hidden

```javascript
// Pause rendering when window is hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        live2dController.app.ticker.stop();
    } else {
        live2dController.app.ticker.start();
    }
});
```

### 4. Cleanup on Unload

```javascript
// Cleanup when switching models or closing
window.addEventListener('beforeunload', () => {
    live2dController.destroy();
});
```

## Testing Checklist

### Basic Functionality
- [ ] Model loads successfully
- [ ] Model displays correctly
- [ ] Mouse tracking works
- [ ] Expressions change
- [ ] Motions play

### Click-Through
- [ ] Clicks pass through empty areas
- [ ] Clicks work on model
- [ ] Drag works on model
- [ ] Hover detection is accurate
- [ ] Works on all monitors

### Version Detection
- [ ] Cubism 2 models work
- [ ] Cubism 4 models work
- [ ] Idle animations work
- [ ] Console shows correct version

### Motion System
- [ ] IDLE motions can be interrupted
- [ ] NORMAL motions play fully
- [ ] FORCE motions override
- [ ] Motion callbacks work

### Integration
- [ ] Settings sync works
- [ ] Maid switching works
- [ ] Expression triggers work
- [ ] Tray menu controls work
- [ ] Hotkeys work

## Next Steps

1. **Test with your models** - Load Aria and Luna models
2. **Verify click-through** - Test desktop mascot mode
3. **Check version detection** - Ensure idle motions work
4. **Test expressions** - Trigger from Python backend
5. **Performance test** - Monitor FPS and memory

## Resources

- [Live2D Controller Source](../desktop/frontend/live2d-controller.js)
- [VRM Improvements Doc](./vrm-renderer-improvements.md)
- [Perplexity Reference](../perplexity/perplexity.md)
- [pixi-live2d-display Docs](https://github.com/guansss/pixi-live2d-display)

## Support

If you encounter issues:
1. Check console for errors
2. Verify model files are correct
3. Test in browser mode first
4. Check Electron IPC communication
5. Review this guide's troubleshooting section

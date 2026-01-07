# Live2D Advanced Controls Components

This directory contains reusable components for advanced Live2D model control and debugging.

## Components

### Core Control Components

#### ViewportControls.js
Provides pan, zoom, and rotation controls for Live2D viewport.
- Mouse/touch drag for panning
- Mouse wheel for zooming
- Programmatic control methods
- Event system for state changes
- Transform matrix generation

#### ParameterPanel.js
Displays and controls Live2D model parameters in real-time.
- Real-time parameter sliders (-1.0 to 1.0 range)
- Search and filter functionality
- Automatic parameter grouping
- Import/export parameter values
- Throttled updates for performance

#### AnimationManager.js
Manages Live2D animations with playback controls.
- Play/pause/stop controls
- Speed control (0.1x to 3.0x)
- Loop toggle
- Timeline visualization with scrubbing
- Frame-by-frame stepping

#### GridOverlay.js
Renders customizable grid overlay on canvas.
- Multiple grid types (lines, dots, crosshair)
- Adjustable spacing (10px to 200px)
- Color and opacity controls
- Toggle on/off
- Automatic canvas size matching

#### PerformanceMonitor.js
Tracks and displays performance metrics.
- FPS tracking with color coding
- Frame time measurement
- Memory usage monitoring
- Draw call counting
- Historical graph visualization

### System Components

#### SettingsManager.js
Manages settings persistence across sessions.
- localStorage for web frontends
- Electron file system integration
- Schema-based validation
- Auto-save with debouncing
- Import/export functionality
- Preset management

#### KeyboardShortcutManager.js
Manages keyboard shortcuts for all controls.
- Customizable key bindings
- Modifier key support (Ctrl, Shift, Alt)
- Conflict detection
- Enable/disable shortcuts
- Input field exclusion

#### DefaultShortcuts.js
Default keyboard shortcuts configuration.
- Space: Play/pause animation
- R: Reset viewport
- G: Toggle grid
- P: Toggle performance monitor
- 1-9: Switch maids
- Arrow keys: Pan viewport
- +/-: Zoom in/out
- Ctrl+S: Save settings
- Ctrl+D: Toggle debug panel

### Integration

#### Live2DControlsIntegration.js
Unified interface for all control components.
- Automatic component initialization
- Settings synchronization
- Centralized event handling
- Preset management
- Export/import all settings

## Usage

### Basic Setup

```javascript
// Import components
const ViewportControls = require('./components/ViewportControls');
const ParameterPanel = require('./components/ParameterPanel');
const GridOverlay = require('./components/GridOverlay');

// Initialize viewport controls
const canvas = document.getElementById('live2d-canvas');
const viewportControls = new ViewportControls(canvas);

// Initialize parameter panel
const paramContainer = document.getElementById('param-panel');
const parameterPanel = new ParameterPanel(paramContainer);

// Add parameters
parameterPanel.setParameter('ParamEyeLOpen', 1.0);
parameterPanel.setParameter('ParamMouthOpenY', 0.0);

// Listen for changes
parameterPanel.on('change', (event) => {
    console.log(`Parameter ${event.parameter} changed to ${event.value}`);
});

// Initialize grid overlay
const gridOverlay = new GridOverlay(canvas, {
    enabled: true,
    type: 'lines',
    spacing: 50
});
```

### Integrated Setup

```javascript
const Live2DControlsIntegration = require('./components/Live2DControlsIntegration');

// Initialize all components at once
const controls = new Live2DControlsIntegration(canvas, {
    parameterContainer: document.getElementById('param-panel'),
    animationContainer: document.getElementById('anim-panel'),
    performanceContainer: document.getElementById('perf-panel'),
    autoLoadSettings: true,
    autoSaveSettings: true
});

// Access individual components
const viewport = controls.getViewportControls();
const params = controls.getParameterPanel();
const grid = controls.getGridOverlay();

// Export settings
const json = controls.exportSettings();

// Load preset
controls.loadPreset('my-preset');
```

### Keyboard Shortcuts

```javascript
const KeyboardShortcutManager = require('./components/KeyboardShortcutManager');
const { setupDefaultShortcuts } = require('./components/DefaultShortcuts');

// Create shortcut manager
const shortcuts = new KeyboardShortcutManager();

// Setup default shortcuts
setupDefaultShortcuts(shortcuts, {
    viewportControls,
    gridOverlay,
    performanceMonitor,
    parameterPanel,
    animationManager,
    settingsManager,
    onMaidSwitch: (maid) => console.log(`Switching to ${maid}`),
    onDebugToggle: () => console.log('Toggle debug panel')
});

// Register custom shortcut
shortcuts.register('Ctrl+Shift+R', () => {
    console.log('Custom action');
}, { description: 'My custom action' });
```

## Events

All components emit events that can be listened to:

### ViewportControls Events
- `change`: Any viewport state change
- `pan`: Pan operation
- `zoom`: Zoom operation
- `rotate`: Rotation operation
- `reset`: Reset to initial state

### ParameterPanel Events
- `change`: Parameter value changed
- `change:ParamName`: Specific parameter changed

### AnimationManager Events
- `play`: Animation started
- `pause`: Animation paused
- `stop`: Animation stopped
- `frame`: Frame update
- `loop`: Animation looped
- `complete`: Animation completed

### GridOverlay Events
- `change`: Any grid setting changed
- `change:property`: Specific property changed

### PerformanceMonitor Events
- `update`: Metrics updated

### SettingsManager Events
- `change`: Settings changed
- `change:path`: Specific setting changed
- `loaded`: Settings loaded
- `saved`: Settings saved
- `presetSaved`: Preset saved
- `presetLoaded`: Preset loaded

## Component Architecture

All components follow these principles:

1. **Modular**: Each component is self-contained and reusable
2. **Event-driven**: Components emit events for state changes
3. **Configurable**: Options can be passed during initialization
4. **Disposable**: All components have a `dispose()` method for cleanup
5. **Validated**: Settings are validated against schemas
6. **Persistent**: State can be saved and restored

## File Structure

```
components/
├── ViewportControls.js          # Viewport manipulation
├── ParameterPanel.js            # Parameter controls
├── AnimationManager.js          # Animation playback
├── GridOverlay.js               # Grid visualization
├── PerformanceMonitor.js        # Performance tracking
├── SettingsManager.js           # Settings persistence
├── KeyboardShortcutManager.js   # Keyboard shortcuts
├── DefaultShortcuts.js          # Default key bindings
├── Live2DControlsIntegration.js # Unified integration
└── README.md                    # This file
```

## Integration with Electron

These components are designed to work seamlessly with the Electron debug panel:

```javascript
// In debug-panel.js
const controls = new Live2DControlsIntegration(canvas, {
    parameterContainer: document.getElementById('param-list'),
    animationContainer: document.getElementById('animation-list'),
    performanceContainer: document.getElementById('performance'),
    autoLoadSettings: true
});

// Listen for IPC messages from main process
window.electronAPI.on('debug-parameter-update', (data) => {
    controls.getParameterPanel().updateParameter(data.parameter, data.value);
});

// Send updates to main window
controls.getParameterPanel().on('change', (event) => {
    window.electronAPI.send('debug-parameter-update', {
        parameter: event.parameter,
        value: event.value
    });
});
```

## Browser Compatibility

All components are compatible with:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Electron 12+

Required APIs:
- Canvas 2D Context
- ResizeObserver
- localStorage (for settings)
- requestAnimationFrame

## Performance Considerations

- Parameter updates are throttled to prevent excessive re-renders
- Grid overlay uses a separate canvas layer
- Performance monitor updates at configurable intervals (default 100ms)
- Settings auto-save is debounced (default 1000ms)
- Event listeners are properly cleaned up on dispose

## Future Enhancements

Potential additions:
- Expression manager component
- Timeline visualization component
- Model info display component
- Batch parameter operations
- Parameter animation recording
- Custom grid patterns
- Advanced performance profiling

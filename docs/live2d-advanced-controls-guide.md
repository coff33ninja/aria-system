# Live2D Advanced Controls Guide

## Overview

The Aria Maid System features professional-grade Live2D avatar controls across all deployment modes. This guide covers the advanced control systems, web frontends, and lip sync capabilities.

---

## 🎮 Control Systems

### Core Components

All frontends share these modular control components:

#### 1. **Viewport Controls**
- **Pan**: Click and drag to move the model
- **Zoom**: Mouse wheel or pinch to zoom (0.1x to 3.0x)
- **Rotation**: Rotate the model view
- **Reset**: Return to default view with one click
- **Fit to Screen**: Automatically scale model to fit viewport

**Keyboard Shortcuts**:
- Arrow keys: Pan viewport
- `+`/`-`: Zoom in/out
- `R`: Reset view

#### 2. **Parameter Panel**
- Real-time display of all Live2D model parameters
- Interactive sliders for manual adjustment (-1.0 to 1.0 range)
- Search/filter parameters by name
- Automatic grouping by category (Eyes, Mouth, Body, etc.)
- Debounced updates (max 60 updates/second for smooth performance)

**Parameter Categories**:
- Eyes (opening, direction, blinking)
- Mouth (opening, form, smile)
- Eyebrows (angle, form)
- Body (angle, position)
- Hair (physics, movement)
- Animation (breathing, idle motions)

#### 3. **Animation Manager**
- List all available animations
- Play/Pause/Stop controls
- Speed control (0.1x to 3.0x)
- Loop toggle
- Timeline visualization with scrubbing
- Frame-by-frame stepping

#### 4. **Expression Manager**
- Quick-select expression buttons
- Expression preview on hover
- Custom expression creation (save current parameters)
- Expression blending controls
- Import/Export expressions as JSON

**Available Expressions** (model-dependent):
- Aria: coat_toggle, heart_eyes, angry, eye_roll, eye_mask, blush, dark_face
- Luna: black face, cry, Love eye, Money eye, shyness, sitting position, etc.

#### 5. **Grid Overlay**
- Toggle grid on/off (`G` key)
- Three grid types: Lines, Dots, Crosshair
- Adjustable spacing (10px to 200px)
- Customizable color and opacity
- Cached rendering for optimal performance

#### 6. **Performance Monitor**
- Real-time FPS display
- Frame time tracking
- Memory usage monitoring
- Model complexity metrics (vertices, textures, draw calls)
- Performance graph with 60-second history
- Color-coded FPS indicator (green/yellow/red)

#### 7. **Model Info Panel**
- Model name, version, author
- Parameter count and names
- Available animations list
- Texture information
- Physics settings
- Collapsible for space saving

#### 8. **Batch Operations**
- Apply parameter presets to multiple parameters
- Reset all parameters to defaults
- Randomize parameters for testing
- Copy/paste parameter sets

#### 9. **Settings Persistence**
- Auto-save all control states
- Import/Export configurations as JSON
- Preset management (save/load named presets)
- Per-model settings
- Cross-session persistence

#### 10. **Keyboard Shortcuts**
- Fully customizable shortcuts
- Default shortcuts for common actions
- Modifier key support (Ctrl, Shift, Alt)
- Shortcut hints in UI
- Conflict detection

**Default Shortcuts**:
- `Space`: Play/pause animation
- `R`: Reset viewport
- `G`: Toggle grid overlay
- `P`: Toggle performance monitor
- `1-9`: Switch between maids (where applicable)
- `+`/`-`: Zoom in/out
- Arrow keys: Pan viewport

---

## 🎤 Lip Sync System

### Professional-Grade Audio Analysis

All frontends now feature real-time lip sync using Web Audio API:

**Features**:
- Real-time frequency analysis
- Volume-based mouth opening
- Smooth parameter transitions (60fps)
- Configurable sensitivity and smoothing
- Natural mouth movement curves
- Automatic voice activity detection

**How It Works**:
1. Audio stream analyzed using FFT (Fast Fourier Transform)
2. Average volume calculated from frequency data
3. Volume smoothed to reduce jitter
4. Power curve applied for natural movement
5. `ParamMouthOpenY` parameter updated in real-time

**Configuration**:
- Smoothing: 0.7 (reduces jitter)
- Sensitivity: 1.2 (amplifies mouth movement)
- Min Volume: 0.01 (threshold for mouth opening)
- Max Mouth Open: 0.9 (prevents over-opening)

### Lip Sync by Frontend

#### LiveKit Mode
- ✅ **Automatic** - Analyzes agent's audio track
- Real-time sync with voice output
- Status indicator shows "Lip Sync: Active/Inactive"
- No configuration needed

#### Desktop Mode
- ✅ **Automatic** - Analyzes audio playback
- Graceful fallback to simple animation
- Initializes on app startup
- Works with WebSocket audio streams

#### Standalone Testing Tool
- ✅ **Manual Testing** - Upload audio files
- Visual feedback (volume and mouth opening bars)
- Perfect for testing and tuning
- Supports all audio formats

---

## 🌐 Web Frontends

### 1. Desktop Mode Frontend (`desktop/frontend/`)

**URL**: `http://localhost:8080` (when running Desktop Mode)

**Purpose**: Main chat interface with Live2D avatar for Desktop Mode (Gemini Direct)

**Features**:
- Full chat interface with message history
- Live2D avatar with real-time lip sync
- Expression quick-select panel
- Parameter adjustment sliders
- Maid selector (for testing)
- Voice controls (mic/speaker toggles)
- WebSocket connection to Python backend
- Settings persistence via localStorage
- Keyboard shortcuts
- Collapsible control panel

**Components**:
- Chat messages with role indicators
- Current maid badge
- Connection status indicator
- Live2D canvas with PIXI.js
- Quick controls panel (collapsible)
- Model info panel (collapsible)

**Usage**:
1. Start Desktop Mode: `python -m desktop.agent`
2. Browser opens automatically to `http://localhost:8080`
3. Chat with Aria and watch her respond with lip sync
4. Click controls toggle to access advanced controls
5. Use expression buttons for quick expressions
6. Adjust parameters with sliders

**Advanced Controls**:
- Toggle with button in top-right
- Expression quick-select buttons
- Common parameter sliders (mouth, eyes, smile)
- Auto-saves control panel state

---

### 2. LiveKit Mode Frontend (`livekit_mode/frontend/demo.html`)

**URL**: Served by LiveKit agent (typically `http://localhost:3000`)

**Purpose**: Web-based LiveKit client with Live2D avatar for cloud deployment

**Features**:
- LiveKit room connection
- Real-time voice communication
- Live2D avatar with automatic lip sync
- Expression controls
- Parameter sliders
- Grid overlay toggle
- Performance monitor
- Room status display
- Audio visualization

**Components**:
- LiveKit connection panel
- Room status indicators
- Live2D canvas
- Expression selector
- Parameter controls
- Performance metrics
- Audio level visualization

**Usage**:
1. Start LiveKit Mode: `python -m livekit_mode.agent dev`
2. Open frontend in browser
3. Enter room name and connect
4. Speak to Aria - lip sync automatically activates
5. Use controls to adjust avatar appearance

**Lip Sync**:
- Automatically analyzes agent's audio track
- Status indicator shows sync state
- No manual configuration needed
- Works with all LiveKit audio sources

---

### 3. Standalone Testing Tool (`desktop/standalone-tool.html`)

**URL**: `http://localhost:8080/desktop/standalone-tool.html` (when HTTP server running)

**Purpose**: Comprehensive testing and development tool for Live2D models

**Features**:
- Model selector (all 6 maids)
- Full viewport controls
- Complete parameter panel with search
- Animation manager with timeline
- Expression manager
- Grid overlay with customization
- Performance monitoring
- Model info display
- **Lip sync testing with audio files**
- Import/Export configurations
- Screenshot capture
- Batch operations
- Keyboard shortcuts

**Components**:
- Header with action buttons
- Model selector sidebar
- Live2D canvas with overlays
- Comprehensive control panels
- Status indicators
- FPS display

**Usage**:
1. Start HTTP server (automatic with Desktop Mode)
2. Navigate to `http://localhost:8080/desktop/standalone-tool.html`
3. Select a model from the sidebar
4. Use control panels to test all features
5. Upload audio file to test lip sync
6. Export configurations for use in production

**Lip Sync Testing**:
1. Scroll to "🎤 Lip Sync Testing" panel
2. Click "Choose File" and select audio file
3. Click "▶ Play Audio"
4. Watch real-time lip sync with visual feedback
5. Volume and mouth opening bars show analysis
6. Perfect for tuning sensitivity and smoothing

**Export/Import**:
- Export current configuration as JSON
- Export parameter values
- Import saved configurations
- Take screenshots of current view
- Reset all settings to defaults

---

### 4. Electron Desktop Overlay (`desktop/electron/`)

**Purpose**: Transparent desktop overlay for Live2D avatar (optional)

**Features**:
- Transparent window overlay
- Always-on-top avatar
- Click-through support
- Tray menu controls
- Debug panel (developer mode)
- IPC communication with main process

**Usage**:
1. Set environment: `ARIA_DESKTOP_FRONTEND=electron`
2. Install dependencies: `cd desktop/electron && npm install`
3. Start Desktop Mode: `python -m desktop.agent`
4. Electron window opens automatically

**Debug Panel**:
- Access via tray menu: "Toggle Debug Panel"
- Full control suite
- Real-time parameter display
- Animation timeline
- Performance graphs
- IPC message log

---

## 📊 Performance Optimizations

### Implemented Optimizations

#### 1. **Parameter Updates**
- Debounced to max 60 updates/second per parameter
- Immediate UI feedback for responsive feel
- Prevents overwhelming Live2D model
- Per-parameter debounce functions

#### 2. **Graph Rendering**
- RAF-throttled (requestAnimationFrame)
- Max 60fps rendering
- Only redraws when visible
- Syncs with browser paint cycle

#### 3. **Grid Rendering**
- Cached rendering system
- Only re-renders on settings change
- Eliminates redundant draws
- Cache invalidation on updates

#### 4. **General Optimizations**
- Minimized re-renders across components
- Event delegation where possible
- Lazy-loading of components
- Efficient memory management
- Proper cleanup on dispose

**Performance Targets**:
- 60 FPS rendering
- < 1% CPU overhead for controls
- < 50MB memory footprint
- Smooth parameter transitions
- No frame drops during interaction

---

## 🎨 Customization

### Settings Configuration

All settings are persisted automatically:

**Desktop Mode**: `localStorage` (browser)
**Electron Mode**: `settings.json` (file system)
**Standalone Tool**: `localStorage` (browser)

**Configurable Settings**:
- Viewport position, zoom, rotation
- Grid type, spacing, color, opacity
- Performance monitor visibility
- Keyboard shortcuts
- Control panel visibility
- Last used model
- Expression presets
- Parameter presets

### Creating Custom Expressions

1. Adjust parameters to desired state
2. Open Expression Manager
3. Click "Save Current as Expression"
4. Name your expression
5. Expression saved to settings
6. Use quick-select button to apply

### Creating Parameter Presets

1. Adjust parameters to desired values
2. Click "Export Parameters" button
3. Save JSON file
4. Later: Click "Import" and select file
5. Parameters restored instantly

### Keyboard Shortcut Customization

1. Open Settings (gear icon)
2. Navigate to "Keyboard Shortcuts"
3. Click on shortcut to rebind
4. Press new key combination
5. Conflicts automatically detected
6. Reset to defaults available

---

## 🔧 Technical Details

### Architecture

**Component Pattern**: Event-driven, modular components
- Each component is self-contained
- EventEmitter pattern for communication
- Dispose methods for cleanup
- Settings integration
- Keyboard shortcut support

**File Structure**:
```
desktop/
├── frontend/
│   ├── index.html          # Desktop Mode UI
│   ├── app.js              # Main application logic
│   ├── LipSyncAnalyzer.js  # Lip sync audio analysis
│   └── styles.css          # Styling
├── electron/
│   ├── components/         # Reusable control components
│   │   ├── ViewportControls.js
│   │   ├── ParameterPanel.js
│   │   ├── AnimationManager.js
│   │   ├── GridOverlay.js
│   │   ├── PerformanceMonitor.js
│   │   ├── SettingsManager.js
│   │   ├── KeyboardShortcutManager.js
│   │   ├── Live2DControlsIntegration.js
│   │   ├── ModelInfoPanel.js
│   │   ├── ExpressionManager.js
│   │   ├── TimelineVisualization.js
│   │   ├── BatchOperations.js
│   │   ├── LoadingErrorHandler.js
│   │   └── PerformanceUtils.js
│   ├── main.js             # Electron main process
│   ├── preload.js          # Electron preload script
│   └── package.json        # Electron dependencies
├── standalone-tool.html    # Testing tool (all-in-one)
└── server.py               # HTTP + WebSocket server
```

### Dependencies

**Frontend**:
- PIXI.js 6.5.10 (rendering engine)
- Live2D Cubism SDK (model support)
- pixi-live2d-display 0.4.0 (Live2D integration)
- Web Audio API (lip sync)

**Backend**:
- Python 3.12+
- websockets (WebSocket server)
- asyncio (async operations)

**Electron** (optional):
- Electron 27+
- Node.js 18+

### Browser Compatibility

**Supported Browsers**:
- Chrome/Edge 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Opera 76+ ✅

**Required Features**:
- WebGL 2.0 (for PIXI.js)
- Web Audio API (for lip sync)
- ES6 Modules (for components)
- localStorage (for settings)

**Mobile Support**:
- iOS Safari 14+ ✅
- Chrome Android 90+ ✅
- Touch controls supported
- Responsive layouts

---

## 🚀 Quick Start

### Desktop Mode with Advanced Controls

```bash
# Start Desktop Mode
python -m desktop.agent

# Browser opens automatically to http://localhost:8080
# Chat with Aria and use advanced controls
```

### Standalone Testing Tool

```bash
# Start Desktop Mode (starts HTTP server)
python -m desktop.agent

# In browser, navigate to:
# http://localhost:8080/desktop/standalone-tool.html

# Select model and test all features
```

### LiveKit Mode

```bash
# Start LiveKit Mode
python -m livekit_mode.agent dev

# Open frontend in browser
# Connect to room and interact
```

### Electron Desktop Overlay

```bash
# Install Electron dependencies (first time only)
cd desktop/electron
npm install
cd ../..

# Set environment variable
export ARIA_DESKTOP_FRONTEND=electron  # Linux/Mac
set ARIA_DESKTOP_FRONTEND=electron     # Windows

# Start Desktop Mode
python -m desktop.agent

# Electron window opens automatically
```

---

## 📝 Usage Examples

### Example 1: Testing Expressions

```javascript
// In browser console (Standalone Tool)

// Get expression manager
const exprManager = window.controlsIntegration.expressionManager;

// Apply expression
exprManager.applyExpression('heart_eyes');

// Create custom expression
exprManager.saveCurrentAsExpression('my_custom_expression');

// Export expressions
const json = exprManager.exportJSON();
console.log(json);
```

### Example 2: Adjusting Parameters

```javascript
// Get parameter panel
const paramPanel = window.controlsIntegration.parameterPanel;

// Set parameter value
paramPanel.setParameter('ParamMouthOpenY', 0.8);

// Get all parameters
const params = paramPanel.getAllParameters();
console.log(params);

// Reset all parameters
paramPanel.resetAll();
```

### Example 3: Viewport Control

```javascript
// Get viewport controls
const viewport = window.controlsIntegration.viewportControls;

// Zoom in
viewport.zoomIn();

// Pan to position
viewport.pan(100, 50);

// Reset view
viewport.reset();

// Get current state
const state = viewport.getState();
console.log(state);
```

### Example 4: Lip Sync Testing

```javascript
// In Standalone Tool

// Upload audio file via UI
// Or programmatically:
const analyzer = new LipSyncAnalyzer({
    sensitivity: 1.5,
    smoothing: 0.8
});

await analyzer.initialize();

// Connect to audio element
const audio = document.getElementById('my-audio');
await analyzer.connectAudioElement(audio);

// Set callback
analyzer.onMouthUpdate = (mouthOpen) => {
    console.log('Mouth open:', mouthOpen);
};

// Play audio
audio.play();
```

---

## 🐛 Troubleshooting

### Common Issues

#### Lip Sync Not Working

**Symptoms**: Mouth doesn't move during speech

**Solutions**:
1. Check browser console for errors
2. Ensure Web Audio API is supported
3. Verify audio is playing
4. Check volume levels (may be too quiet)
5. Try adjusting sensitivity in settings
6. Ensure user has interacted with page (browser requirement)

#### Performance Issues

**Symptoms**: Low FPS, stuttering, lag

**Solutions**:
1. Check Performance Monitor for metrics
2. Disable grid overlay if enabled
3. Reduce parameter update frequency
4. Close other browser tabs
5. Update graphics drivers
6. Try different browser

#### Model Not Loading

**Symptoms**: Loading spinner never completes

**Solutions**:
1. Check browser console for errors
2. Verify model files exist in `live2d/models/`
3. Check network tab for 404 errors
4. Ensure HTTP server is running
5. Try different model
6. Clear browser cache

#### Controls Not Responding

**Symptoms**: Buttons/sliders don't work

**Solutions**:
1. Check browser console for errors
2. Verify JavaScript is enabled
3. Try refreshing page
4. Check if model is loaded
5. Ensure controls are initialized
6. Try different browser

#### WebSocket Connection Failed

**Symptoms**: "Disconnected" status in Desktop Mode

**Solutions**:
1. Verify Python backend is running
2. Check port 8765 is not in use
3. Check firewall settings
4. Try restarting backend
5. Check browser console for errors
6. Verify WebSocket URL is correct

---

## 📚 Additional Resources

### Documentation

- [Live2D Integration Guide](./live2d-integration-guide.md)
- [Electron Desktop Avatar Plan](./electron-desktop-avatar-plan.md)
- [Voice Optimization Guide](./voice-optimization-rebuild-plan.md)
- [MCP Integration Guide](./livekit-mcp-integration.md)

### API References

- [Agent Reference](./agent-reference.md)
- [Tools Reference](./tools-reference.md)
- [Prompts Reference](./prompts-reference.md)
- [MCP Server Reference](./mcp-server-reference.md)

### Specifications

- [Requirements Document](./.kiro/specs/live2d-advanced-controls/requirements.md)
- [Design Document](./.kiro/specs/live2d-advanced-controls/design.md)
- [Implementation Tasks](./.kiro/specs/live2d-advanced-controls/tasks.md)
- [Performance Optimizations](./.kiro/specs/live2d-advanced-controls/performance-optimizations.md)
- [Lip Sync Improvements](./.kiro/specs/live2d-advanced-controls/lip-sync-improvements.md)

---

## 🎯 Best Practices

### For Development

1. **Use Standalone Tool** for testing new features
2. **Export configurations** before making changes
3. **Test across browsers** for compatibility
4. **Monitor performance** during development
5. **Use keyboard shortcuts** for efficiency

### For Production

1. **Optimize settings** for target hardware
2. **Disable debug features** in production
3. **Test lip sync** with various audio sources
4. **Monitor FPS** and adjust quality settings
5. **Provide fallbacks** for older browsers

### For Users

1. **Start with defaults** and adjust as needed
2. **Save presets** for different scenarios
3. **Use keyboard shortcuts** for common actions
4. **Test audio** before important sessions
5. **Keep browser updated** for best performance

---

## 🔮 Future Enhancements

Planned improvements for future releases:

1. **Phoneme Detection**: Analyze frequency patterns for vowel sounds
2. **Advanced Mouth Shapes**: Different shapes for different sounds
3. **Breathing Animation**: Subtle chest movement when idle
4. **Multi-Parameter Sync**: Sync eyebrows, eyes with speech
5. **Recording Support**: Record and replay sessions
6. **Cloud Sync**: Sync settings across devices
7. **Mobile App**: Native iOS/Android apps
8. **VR Support**: VR headset integration
9. **Motion Capture**: Webcam-based facial tracking
10. **AI Expression**: Automatic expression selection based on emotion

---

## 📄 License

Part of the Aria Maid System. See main LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please see main CONTRIBUTING.md for guidelines.

---

## 💬 Support

For issues, questions, or suggestions:
- Check documentation first
- Search existing issues
- Create new issue with details
- Include browser/OS information
- Provide console errors if applicable

---

**Last Updated**: January 2026
**Version**: 1.0.0
**Status**: Production Ready ✅

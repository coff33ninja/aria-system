# README Section: Live2D Advanced Controls

**Copy this section into your main README.md where appropriate**

---

## 🎮 Live2D Advanced Controls

Professional-grade avatar controls with real-time lip sync across all deployment modes.

### Features

- **Viewport Controls**: Pan, zoom, rotate with mouse/touch
- **Parameter Panel**: Real-time adjustment of all model parameters
- **Animation Manager**: Play, pause, speed control, timeline scrubbing
- **Expression Manager**: Quick-select expressions, custom presets
- **Grid Overlay**: Customizable alignment grid (lines/dots/crosshair)
- **Performance Monitor**: Real-time FPS, memory, and metrics tracking
- **Lip Sync**: Professional audio analysis for natural mouth movements
- **Keyboard Shortcuts**: Fully customizable hotkeys
- **Settings Persistence**: Auto-save all configurations
- **Import/Export**: Share configurations as JSON

### Web Frontends

#### 1. Desktop Mode Frontend
**URL**: `http://localhost:8080`

Main chat interface with Live2D avatar for Desktop Mode (Gemini Direct).

**Features**:
- Full chat interface with message history
- Real-time lip sync during conversations
- Collapsible control panel
- Expression quick-select
- Parameter sliders
- WebSocket connection to backend

**Usage**:
```bash
python -m desktop.agent
# Browser opens automatically
```

#### 2. LiveKit Mode Frontend
**URL**: Served by LiveKit agent

Web-based LiveKit client with Live2D avatar for cloud deployment.

**Features**:
- LiveKit room connection
- Real-time voice communication
- Automatic lip sync with agent audio
- Expression and parameter controls
- Performance monitoring

**Usage**:
```bash
python -m livekit_mode.agent dev
# Open frontend in browser
```

#### 3. Standalone Testing Tool
**URL**: `http://localhost:8080/desktop/standalone-tool.html`

Comprehensive testing and development tool for Live2D models.

**Features**:
- Model selector (all 6 maids)
- Complete control suite
- **Lip sync testing with audio files**
- Animation timeline
- Screenshot capture
- Configuration import/export

**Usage**:
```bash
python -m desktop.agent
# Navigate to standalone-tool.html in browser
```

**Lip Sync Testing**:
1. Select a model
2. Scroll to "🎤 Lip Sync Testing" panel
3. Upload audio file
4. Click "▶ Play Audio"
5. Watch real-time lip sync with visual feedback

#### 4. Electron Desktop Overlay (Optional)
Transparent desktop overlay with always-on-top avatar.

**Setup**:
```bash
cd desktop/electron
npm install
cd ../..

# Windows
set ARIA_DESKTOP_FRONTEND=electron

# Linux/Mac
export ARIA_DESKTOP_FRONTEND=electron

python -m desktop.agent
```

### Lip Sync System

All frontends feature professional-grade lip sync using Web Audio API:

| Frontend | Status | Method |
|----------|--------|--------|
| **LiveKit Mode** | ✅ Automatic | Real-time audio analysis |
| **Desktop Mode** | ✅ Automatic | Real-time audio analysis + fallback |
| **Standalone Tool** | ✅ Testing | Audio file upload and analysis |
| **Electron Overlay** | ✅ Automatic | Real-time audio analysis |

**How It Works**:
- Analyzes audio using FFT (Fast Fourier Transform)
- Calculates volume from frequency data
- Applies smoothing to reduce jitter
- Updates mouth parameters at 60fps
- Natural movement curves for realistic animation

### Keyboard Shortcuts

Default shortcuts (fully customizable):

- `Space`: Play/pause animation
- `R`: Reset viewport
- `G`: Toggle grid overlay
- `P`: Toggle performance monitor
- `+`/`-`: Zoom in/out
- Arrow keys: Pan viewport
- `1-9`: Switch between maids (where applicable)

### Performance

Optimized for smooth 60 FPS operation:

- Debounced parameter updates (max 60/second)
- RAF-throttled graph rendering
- Cached grid rendering
- Minimal CPU overhead (< 1%)
- Efficient memory management

### Documentation

For detailed information, see:
- [Live2D Advanced Controls Guide](./docs/live2d-advanced-controls-guide.md)
- [Lip Sync Improvements](./docs/lip-sync-improvements.md)
- [Performance Optimizations](./docs/performance-optimizations.md)

### Browser Compatibility

- Chrome/Edge 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Mobile (iOS/Android) ✅

**Requirements**:
- WebGL 2.0
- Web Audio API
- ES6 Modules
- localStorage

---

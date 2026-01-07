# Live2D Controls Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Aria Maid System                             │
│                  Live2D Advanced Controls                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                    ┌─────────▼─────────┐          ┌───────────▼──────────┐
                    │  Desktop Mode     │          │   LiveKit Mode       │
                    │  (Gemini Direct)  │          │   (Cloud)            │
                    └─────────┬─────────┘          └───────────┬──────────┘
                              │                                 │
                    ┌─────────▼─────────┐          ┌───────────▼──────────┐
                    │  HTTP Server      │          │  LiveKit Agent       │
                    │  Port 8080        │          │  WebRTC              │
                    └─────────┬─────────┘          └───────────┬──────────┘
                              │                                 │
                    ┌─────────▼─────────┐          ┌───────────▼──────────┐
                    │  WebSocket        │          │  LiveKit Client      │
                    │  Port 8765        │          │  SDK                 │
                    └─────────┬─────────┘          └───────────┬──────────┘
                              │                                 │
                              └─────────────┬───────────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │   Web Frontends           │
                              │   (Browser-based)         │
                              └─────────────┬─────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
          ┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
          │ Desktop Frontend  │  │ LiveKit Frontend  │  │ Standalone Tool   │
          │ index.html        │  │ demo.html         │  │ standalone-tool   │
          └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │   Control Components      │
                              │   (Modular JavaScript)    │
                              └─────────────┬─────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
          ┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
          │ ViewportControls  │  │ ParameterPanel    │  │ AnimationManager  │
          │ GridOverlay       │  │ ExpressionManager │  │ PerformanceMonitor│
          │ SettingsManager   │  │ ModelInfoPanel    │  │ LipSyncAnalyzer   │
          └───────────────────┘  └───────────────────┘  └───────────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │   PIXI.js + Live2D        │
                              │   Rendering Engine        │
                              └─────────────┬─────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │   Live2D Models           │
                              │   (Aria, Luna, etc.)      │
                              └───────────────────────────┘
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Live2DControlsIntegration                     │
│                    (Main Orchestrator)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ manages
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│ ViewportControls│  │ ParameterPanel   │  │ AnimationManager│
│                 │  │                  │  │                 │
│ • Pan           │  │ • Sliders        │  │ • Play/Pause    │
│ • Zoom          │  │ • Search         │  │ • Speed Control │
│ • Rotate        │  │ • Grouping       │  │ • Timeline      │
│ • Reset         │  │ • Export/Import  │  │ • Scrubbing     │
└─────────────────┘  └──────────────────┘  └─────────────────┘

┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ GridOverlay     │  │ PerformanceMonitor│  │ ExpressionManager│
│                 │  │                  │  │                 │
│ • Lines         │  │ • FPS            │  │ • Quick Select  │
│ • Dots          │  │ • Memory         │  │ • Custom Create │
│ • Crosshair     │  │ • Graph          │  │ • Blending      │
│ • Caching       │  │ • Metrics        │  │ • Presets       │
└─────────────────┘  └──────────────────┘  └─────────────────┘

┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ SettingsManager │  │ KeyboardShortcuts│  │ ModelInfoPanel  │
│                 │  │                  │  │                 │
│ • localStorage  │  │ • Registration   │  │ • Metadata      │
│ • Import/Export │  │ • Customization  │  │ • Parameters    │
│ • Validation    │  │ • Conflict Check │  │ • Animations    │
│ • Persistence   │  │ • Hints          │  │ • Textures      │
└─────────────────┘  └──────────────────┘  └─────────────────┘

┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ LipSyncAnalyzer │  │ BatchOperations  │  │ LoadingError    │
│                 │  │                  │  │ Handler         │
│ • Audio Analysis│  │ • Multi-Param    │  │                 │
│ • FFT           │  │ • Reset All      │  │ • Spinners      │
│ • Smoothing     │  │ • Randomize      │  │ • Error Display │
│ • Callbacks     │  │ • Presets        │  │ • Retry Logic   │
└─────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Data Flow

### Parameter Update Flow

```
User Input (Slider)
        │
        ▼
Debounce (16ms)
        │
        ▼
ParameterPanel.updateParameter()
        │
        ▼
Emit 'change' event
        │
        ▼
Live2DControlsIntegration
        │
        ▼
Live2D Model.setParameter()
        │
        ▼
PIXI.js Render
        │
        ▼
Canvas Display
```

### Lip Sync Flow

```
Audio Source (Stream/Element)
        │
        ▼
Web Audio API
        │
        ▼
AnalyserNode (FFT)
        │
        ▼
Frequency Data Array
        │
        ▼
Calculate Average Volume
        │
        ▼
Apply Smoothing (0.7)
        │
        ▼
Volume to Mouth Curve (power 0.6)
        │
        ▼
onMouthUpdate Callback
        │
        ▼
setParameter('ParamMouthOpenY')
        │
        ▼
Live2D Model Update (60fps)
        │
        ▼
Canvas Display
```

### Settings Persistence Flow

```
User Changes Setting
        │
        ▼
Component Updates State
        │
        ▼
Emit 'change' event
        │
        ▼
SettingsManager.updateSettings()
        │
        ▼
Debounce (500ms)
        │
        ▼
Serialize to JSON
        │
        ▼
localStorage.setItem()
        │
        ▼
Settings Saved
```

---

## Frontend Comparison

### Desktop Mode Frontend

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Mode Frontend                     │
│                    (index.html + app.js)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Chat Interface                         │    │
│  │  • Message history                                  │    │
│  │  • Input field                                      │    │
│  │  • Send button                                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Live2D Canvas                          │    │
│  │  • PIXI.js rendering                                │    │
│  │  • Model display                                    │    │
│  │  • Automatic lip sync                               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Quick Controls (Collapsible)           │    │
│  │  • Expression buttons                               │    │
│  │  • Parameter sliders (mouth, eyes, smile)           │    │
│  │  • Model info panel                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              WebSocket Connection                   │    │
│  │  • Real-time communication                          │    │
│  │  • Transcript streaming                             │    │
│  │  • Handoff notifications                            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### LiveKit Mode Frontend

```
┌─────────────────────────────────────────────────────────────┐
│                   LiveKit Mode Frontend                      │
│                   (demo.html)                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Connection Panel                       │    │
│  │  • Room name input                                  │    │
│  │  • Connect button                                   │    │
│  │  • Status indicators                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Live2D Canvas                          │    │
│  │  • PIXI.js rendering                                │    │
│  │  • Model display                                    │    │
│  │  • Automatic lip sync (agent audio)                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Controls Panel                         │    │
│  │  • Expression selector                              │    │
│  │  • Parameter sliders                                │    │
│  │  • Grid overlay toggle                              │    │
│  │  • Performance monitor                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              LiveKit Client SDK                     │    │
│  │  • WebRTC connection                                │    │
│  │  • Audio track handling                             │    │
│  │  • Room events                                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Standalone Testing Tool

```
┌─────────────────────────────────────────────────────────────┐
│                  Standalone Testing Tool                     │
│                  (standalone-tool.html)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Header Actions                         │    │
│  │  • Import/Export                                    │    │
│  │  • Screenshot                                       │    │
│  │  • Reset                                            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌────────────────────────────────┐     │
│  │ Model        │  │  Live2D Canvas                  │     │
│  │ Selector     │  │  • PIXI.js rendering            │     │
│  │              │  │  • Model display                │     │
│  │ • Aria       │  │  • Grid overlay                 │     │
│  │ • Luna       │  │  • Performance monitor          │     │
│  │ • Sophia     │  └────────────────────────────────┘     │
│  │ • Rose       │                                          │
│  │ • Mei        │  ┌────────────────────────────────┐     │
│  │ • Clara      │  │  Control Panels                 │     │
│  └──────────────┘  │  • Viewport Controls            │     │
│                     │  • Parameter Panel              │     │
│                     │  • Animation Manager            │     │
│                     │  • Expression Manager           │     │
│                     │  • Lip Sync Testing             │     │
│                     │  • Grid Overlay                 │     │
│                     │  • Performance Monitor          │     │
│                     │  • Model Info                   │     │
│                     └────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Performance Optimizations                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│ Debouncing     │  │ RAF Throttling   │  │ Caching         │
│                │  │                  │  │                 │
│ • Parameters   │  │ • Graph Render   │  │ • Grid Render   │
│ • Settings     │  │ • 60fps Max      │  │ • Key-based     │
│ • 16ms Delay   │  │ • Paint Sync     │  │ • Invalidation  │
└────────────────┘  └──────────────────┘  └─────────────────┘

        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│ Event          │  │ Lazy Loading     │  │ Memory          │
│ Delegation     │  │                  │  │ Management      │
│                │  │ • Components     │  │                 │
│ • Minimize     │  │ • On-demand      │  │ • Cleanup       │
│ • Bubble Up    │  │ • Visibility     │  │ • Dispose       │
└────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      Technology Stack                        │
└─────────────────────────────────────────────────────────────┘

Frontend (Browser)
├── PIXI.js 6.5.10          (Rendering engine)
├── Live2D Cubism SDK       (Model support)
├── pixi-live2d-display     (Live2D integration)
├── Web Audio API           (Lip sync analysis)
├── ES6 Modules             (Component system)
└── localStorage            (Settings persistence)

Backend (Python)
├── Python 3.12+            (Runtime)
├── websockets              (WebSocket server)
├── asyncio                 (Async operations)
├── http.server             (HTTP server)
└── livekit-agents          (LiveKit integration)

Optional (Electron)
├── Electron 27+            (Desktop app)
├── Node.js 18+             (Runtime)
└── IPC                     (Process communication)

Live2D Models
├── .moc3                   (Model file)
├── .model3.json            (Configuration)
├── .physics3.json          (Physics)
├── EXP3/                   (Expressions)
└── textures/               (Textures)
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Deployment Modes                          │
└─────────────────────────────────────────────────────────────┘

Desktop Mode (Local)
┌────────────────────────────────────────────────────────┐
│  Python Backend                                         │
│  ├── Gemini Live API (Direct)                          │
│  ├── HTTP Server (Port 8080)                           │
│  ├── WebSocket Server (Port 8765)                      │
│  └── PyAudio (Local audio)                             │
│                                                          │
│  Browser Frontend                                       │
│  ├── http://localhost:8080                             │
│  ├── WebSocket Connection                              │
│  └── Live2D Rendering                                  │
└────────────────────────────────────────────────────────┘

LiveKit Mode (Cloud)
┌────────────────────────────────────────────────────────┐
│  Python Backend                                         │
│  ├── LiveKit Agent                                     │
│  ├── WebRTC Connection                                 │
│  └── Cloud Audio Processing                            │
│                                                          │
│  Browser Frontend                                       │
│  ├── LiveKit Client SDK                                │
│  ├── WebRTC Connection                                 │
│  └── Live2D Rendering                                  │
└────────────────────────────────────────────────────────┘

Electron Mode (Desktop Overlay)
┌────────────────────────────────────────────────────────┐
│  Python Backend                                         │
│  ├── Gemini Live API (Direct)                          │
│  ├── HTTP Server (Port 8080)                           │
│  └── WebSocket Server (Port 8765)                      │
│                                                          │
│  Electron App                                           │
│  ├── Transparent Window                                │
│  ├── Always-on-top                                     │
│  ├── IPC Communication                                 │
│  └── Live2D Rendering                                  │
└────────────────────────────────────────────────────────┘
```

---

## Event Flow

```
User Interaction
        │
        ▼
Component Event Handler
        │
        ▼
Debounce/Throttle (if needed)
        │
        ▼
Component State Update
        │
        ▼
Emit Custom Event
        │
        ├──────────────────┬──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
Live2D Model      Settings Manager    Other Components
        │                  │                  │
        ▼                  ▼                  ▼
PIXI.js Render    localStorage Save   UI Update
        │
        ▼
Canvas Display (60fps)
```

---

## Module Dependencies

```
Live2DControlsIntegration
        │
        ├── ViewportControls
        │   └── (no dependencies)
        │
        ├── ParameterPanel
        │   └── PerformanceUtils (debounce)
        │
        ├── AnimationManager
        │   ├── TimelineVisualization
        │   └── LoadingErrorHandler
        │
        ├── ExpressionManager
        │   └── LoadingErrorHandler
        │
        ├── GridOverlay
        │   └── (no dependencies)
        │
        ├── PerformanceMonitor
        │   └── PerformanceUtils (rafThrottle)
        │
        ├── SettingsManager
        │   └── (no dependencies)
        │
        ├── KeyboardShortcutManager
        │   └── DefaultShortcuts
        │
        ├── ModelInfoPanel
        │   └── (no dependencies)
        │
        ├── BatchOperations
        │   └── (no dependencies)
        │
        └── LipSyncAnalyzer
            └── (no dependencies)
```

---

## File Organization

```
desktop/
├── frontend/
│   ├── index.html              # Desktop Mode UI
│   ├── app.js                  # Main application
│   ├── LipSyncAnalyzer.js      # Lip sync module
│   └── styles.css              # Styling
│
├── electron/
│   ├── components/             # Reusable components
│   │   ├── ViewportControls.js
│   │   ├── ParameterPanel.js
│   │   ├── AnimationManager.js
│   │   ├── GridOverlay.js
│   │   ├── PerformanceMonitor.js
│   │   ├── SettingsManager.js
│   │   ├── KeyboardShortcutManager.js
│   │   ├── DefaultShortcuts.js
│   │   ├── Live2DControlsIntegration.js
│   │   ├── ModelInfoPanel.js
│   │   ├── ExpressionManager.js
│   │   ├── TimelineVisualization.js
│   │   ├── BatchOperations.js
│   │   ├── LoadingErrorHandler.js
│   │   └── PerformanceUtils.js
│   │
│   ├── main.js                 # Electron main process
│   ├── preload.js              # Electron preload
│   └── package.json            # Dependencies
│
├── standalone-tool.html        # Testing tool
└── server.py                   # HTTP + WebSocket server

livekit_mode/
└── frontend/
    └── demo.html               # LiveKit frontend

live2d/
└── models/
    ├── aria/                   # Changli model
    └── luna/                   # Nicole model
```

---

**Last Updated**: January 2026
**Version**: 1.0.0

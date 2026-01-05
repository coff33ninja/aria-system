# Electron Desktop Avatar — Feature Plan

## Overview

Enhance the Electron desktop overlay to be a fully-featured desktop companion with system tray controls, avatar customization, and interactive behaviors.

---

## Current State

| Feature | Status |
|---------|--------|
| Transparent frameless window | ✅ Done |
| Always on top | ✅ Done |
| Draggable window | ✅ Done |
| Full tray menu with controls | ✅ Done |
| Live2D avatar rendering | ✅ Done |
| WebSocket connection to backend | ✅ Done |
| Expression system | ✅ Done |
| Zoom controls (tray + hotkeys) | ✅ Done |
| Maid switcher (tray) | ✅ Done |
| Movement modes (static/idle/mouse) | ✅ Done |
| Minimize to tray | ✅ Done |
| Settings persistence | ✅ Done |
| Global hotkeys | ✅ Done |
| Idle animation (breathing, blinking) | ✅ Done |
| Mouse tracking | ✅ Done |

---

## Planned Features

### Phase 1: Core Tray & Controls ✅ COMPLETE

#### 1.1 System Tray Icon
- [x] Fallback colored icon (pink square)
- [ ] Create Aria-themed tray icon (16x16, 32x32, 256x256)
- [ ] Animated tray icon when speaking/listening
- [ ] Badge indicator for connection status (green/red dot)

#### 1.2 Zoom/Scale Controls ✅
- [x] Tray menu: Zoom submenu (50%, 75%, 100%, 125%, 150%, 200%)
- [x] Keyboard shortcuts: `Ctrl+Shift++` zoom in, `Ctrl+Shift+-` zoom out
- [x] Remember zoom level in settings
- [x] Smooth zoom animation

#### 1.3 Minimize to Tray ✅
- [x] Close button (X) minimizes to tray instead of quitting
- [x] Double-click tray icon to restore
- [x] Option to "Really Quit" in tray menu
- [x] Start minimized option

---

### Phase 2: Maid Switcher ✅ COMPLETE

#### 2.1 Quick Maid Switcher (Tray) ✅
```
Tray Menu:
├── Current: Aria ✓
├── Switch Maid →
│   ├── Aria (Head Maid) ✓
│   ├── Sophia (Research) [No Avatar]
│   ├── Luna (Entertainment)
│   ├── Rose (Scheduling) [No Avatar]
│   ├── Mei (Smart Home) [No Avatar]
│   └── Clara (Communication) [No Avatar]
```

- [x] Submenu showing all maids with availability
- [x] Checkmark on current maid
- [x] Grayed out maids without Live2D models
- [x] Sends message to renderer to trigger model swap
- [ ] Avatar swaps with transition animation (crossfade)

#### 2.2 Avatar Hot-Swap
- [x] Model swap on maid switch
- [ ] Smooth crossfade between maid avatars (0.5s)
- [ ] Loading indicator while model loads
- [ ] Fallback to silhouette if model missing
- [ ] Cache loaded models for instant switching

---

### Phase 3: Movement & Tracking (Partial)

#### 3.1 Movement Modes ✅
```
Tray Menu:
├── Movement →
│   ├── Static ✓
│   ├── Idle Animation ✓
│   ├── Mouse Tracking ✓
│   ├── Camera Tracking (Beta)
│   └── Random Wander
```

| Mode | Description | Status |
|------|-------------|--------|
| **Static** | Avatar stays still, only expressions change | ✅ Done |
| **Idle Animation** | Subtle breathing, blinking, small movements | ✅ Done |
| **Mouse Tracking** | Eyes/head follow mouse cursor | ✅ Done |
| **Camera Tracking** | Eyes/head follow user via webcam | ⏳ Placeholder |
| **Random Wander** | Avatar occasionally looks around randomly | ❌ Not started |

#### 3.2 Mouse Tracking Implementation ✅
- [x] Track global mouse position (electron `screen` API)
- [x] Calculate angle from avatar center to cursor
- [x] Map to Live2D parameters: `ParamAngleX`, `ParamAngleY`, `ParamEyeBallX`, `ParamEyeBallY`
- [x] Smooth interpolation (lerp) for natural movement
- [ ] Configurable tracking speed/sensitivity

#### 3.3 Camera Tracking Implementation ✅
- [x] Request webcam permission
- [x] Simple skin-tone based face detection (no external deps)
- [x] Detect face position relative to screen center
- [x] Map face position to avatar gaze direction
- [x] Privacy: Option to disable, no data sent anywhere
- [x] Fallback to idle if camera unavailable
- [ ] Upgrade to TensorFlow.js/MediaPipe for better accuracy (optional)

#### 3.4 Auto-Hide Behavior ✅
```
Tray Menu:
├── Auto-Hide →
│   ├── Disabled ✓
│   ├── After 5 min inactive
│   ├── After 15 min inactive
│   └── Hide in Fullscreen Apps
```

- [x] Configurable inactivity timeout
- [x] Fade out animation when hiding
- [x] Show on activity (mouse/click/key)
- [x] Hide in fullscreen apps option
- [ ] App whitelist/blacklist

#### 3.5 Random Wander Mode ✅
- [x] Avatar randomly looks around
- [x] Smooth transitions between positions
- [x] Combined with breathing and blinking

---

### Phase 4: Expressions & Interactions ✅ COMPLETE

#### 4.1 Manual Expression Triggers (Tray) ✅
```
Tray Menu:
├── Expression →
│   ├── Default ✓
│   ├── Happy ✓
│   ├── Thinking ✓
│   ├── Sassy (Aria) ✓
│   ├── Heart Eyes ✓
│   ├── Blush ✓
│   ├── Wave 👋 ✓
│   └── Blink ✓
```

- [x] Quick expression triggers from tray
- [x] Action triggers (wave, blink)
- [ ] Shows only expressions available for current maid
- [ ] Expression preview on hover (tooltip)

#### 4.2 Click Interactions ✅
- [x] Single-click avatar: Wave/greeting animation
- [x] Double-click avatar: Happy expression
- [x] Triple-click avatar: Annoyed reaction
- [x] Right-click avatar: Shows hint to use tray menu
- [x] Drag avatar: Reposition window

#### 4.3 Hotkey Support ✅
| Hotkey | Action | Status |
|--------|--------|--------|
| `Ctrl+Shift+A` | Toggle avatar visibility | ✅ |
| `Ctrl+Shift+M` | Cycle through maids | ✅ |
| `Ctrl+Shift++` | Zoom in | ✅ |
| `Ctrl+Shift+-` | Zoom out | ✅ |

- [x] Global hotkeys (work even when app not focused)
- [ ] Configurable in settings UI

---

### Phase 5: Advanced Features

#### 5.1 Multiple Monitor Support
- [ ] Remember position per monitor
- [ ] Move to specific monitor from tray
- [ ] Follow active window option

#### 5.2 Themes & Customization
```
Tray Menu:
├── Appearance →
│   ├── Window Size (Small/Medium/Large)
│   ├── Opacity (50%-100%)
│   ├── Border Glow (On/Off)
│   └── Background (Transparent/Subtle/Solid)
```

- [ ] Adjustable window opacity
- [ ] Optional subtle glow/shadow around avatar
- [ ] Size presets (compact, normal, large)

#### 5.3 Notification Integration
- [ ] Avatar reacts to system notifications
- [ ] Custom reactions for specific apps (Discord ping → excited)
- [ ] "Do not disturb" mode

#### 5.4 Voice Activity Indicator
- [ ] Pulsing ring around avatar when listening
- [ ] Waveform visualization when speaking
- [ ] Mute indicator overlay

#### 5.5 Settings Persistence
- [ ] Save all settings to `%APPDATA%/aria-desktop/settings.json`
- [ ] Settings UI window (accessible from tray)
- [ ] Import/export settings

---

## Technical Architecture

### IPC Messages (Renderer ↔ Main)

```javascript
// Main → Renderer
'set-maid': { maid: 'aria' | 'luna' | ... }
'set-expression': { expression: 'happy', duration: 2000 }
'set-movement-mode': { mode: 'static' | 'mouse' | 'camera' | 'idle' }
'set-zoom': { scale: 1.5 }
'set-visibility': { visible: boolean }

// Renderer → Main
'maid-loaded': { maid: 'aria', success: boolean }
'expression-complete': { expression: 'happy' }
'request-settings': {}
'save-settings': { settings: {...} }
```

### Settings Schema

```json
{
  "window": {
    "x": 1500,
    "y": 800,
    "width": 400,
    "height": 500,
    "zoom": 1.0,
    "opacity": 1.0,
    "alwaysOnTop": true,
    "startMinimized": false
  },
  "avatar": {
    "currentMaid": "aria",
    "movementMode": "idle",
    "trackingSpeed": 0.5
  },
  "autoHide": {
    "enabled": false,
    "inactivityMinutes": 5,
    "hideInFullscreen": true,
    "appBlacklist": ["game.exe"]
  },
  "hotkeys": {
    "toggleVisibility": "Ctrl+Shift+A",
    "toggleMute": "Ctrl+Shift+M",
    "cycleMaid": "Ctrl+Shift+S"
  }
}
```

### File Structure (After Implementation)

```
desktop/electron/
├── main.js              # Main process (tray, window, IPC)
├── preload.js           # Context bridge
├── avatar.html          # Renderer HTML
├── renderer.js          # Renderer logic (Live2D, tracking)
├── settings.js          # Settings management
├── tracking/
│   ├── mouse.js         # Mouse tracking module
│   └── camera.js        # Camera/face tracking module
├── assets/
│   ├── icon.png         # Tray icon
│   ├── icon-speaking.png
│   └── icon-listening.png
└── package.json
```

---

## Implementation Priority

| Priority | Feature | Effort | Impact | Status |
|----------|---------|--------|--------|--------|
| 🔴 High | Tray icon + minimize to tray | Low | High | ✅ Done |
| 🔴 High | Zoom controls | Low | Medium | ✅ Done |
| 🔴 High | Maid switcher (tray) | Medium | High | ✅ Done |
| 🟡 Medium | Mouse tracking | Medium | High | ✅ Done |
| 🟡 Medium | Auto-hide | Medium | Medium | ✅ Done |
| 🟡 Medium | Idle animations | Low | Medium | ✅ Done |
| � LMedium | Click interactions | Low | Medium | ✅ Done |
| � Medi|um | Expression triggers | Low | Medium | ✅ Done |
| 🟢 Low | Camera tracking | High | Medium | ✅ Done (basic) |
| 🟢 Low | Random wander | Low | Low | ✅ Done |
| 🟢 Low | Hotkeys | Medium | Medium | ✅ Done |
| 🟢 Low | Settings UI | High | Low | ❌ Not started |
| 🟢 Low | Notification reactions | High | Low | ❌ Not started |
| 🟢 Low | Multi-monitor support | Medium | Low | ❌ Not started |

---

## Dependencies

| Feature | Dependency | Notes | Status |
|---------|------------|-------|--------|
| Camera tracking | Built-in (skin detection) | No external deps, ~basic accuracy | ✅ Implemented |
| Camera tracking (advanced) | `@mediapipe/face_mesh` or `face-api.js` | ~2MB, better accuracy | Optional upgrade |
| Global hotkeys | `electron-globalShortcut` | Built into Electron | ✅ Implemented |
| Settings storage | Native `fs` module | JSON file in userData | ✅ Implemented |
| Mouse tracking | `electron.screen` | Built into Electron | ✅ Implemented |

---

## Open Questions

1. **Camera tracking privacy**: Should we add a visible indicator when camera is active?
2. **Performance**: How much CPU does continuous mouse/camera tracking use?
3. **Model availability**: Which maids need Live2D models created?
4. **Hotkey conflicts**: How to handle conflicts with other apps?

---

## References

- [Electron Tray API](https://www.electronjs.org/docs/latest/api/tray)
- [Live2D Cubism SDK](https://www.live2d.com/en/sdk/about/)
- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [electron-store](https://github.com/sindresorhus/electron-store)

# Live2D Controls - Quick Reference Card

## 🚀 Quick Start

### Desktop Mode
```bash
python -m desktop.agent
# Opens http://localhost:8080 automatically
```

### Standalone Testing Tool
```bash
python -m desktop.agent
# Navigate to: http://localhost:8080/desktop/standalone-tool.html
```

### LiveKit Mode
```bash
python -m livekit_mode.agent dev
# Open frontend in browser
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/pause animation |
| `R` | Reset viewport |
| `G` | Toggle grid overlay |
| `P` | Toggle performance monitor |
| `+` | Zoom in |
| `-` | Zoom out |
| `↑↓←→` | Pan viewport |
| `1-9` | Switch maids (where applicable) |

---

## 🎮 Mouse Controls

| Action | Control |
|--------|---------|
| **Pan** | Click + Drag |
| **Zoom** | Mouse Wheel |
| **Rotate** | Shift + Drag |
| **Reset** | Double Click |
| **Interact** | Click on model |

---

## 🎤 Lip Sync

### Desktop Mode
✅ **Automatic** - Works during conversations

### LiveKit Mode
✅ **Automatic** - Syncs with agent audio

### Standalone Tool
📁 **Manual Testing**:
1. Scroll to "🎤 Lip Sync Testing"
2. Upload audio file
3. Click "▶ Play Audio"
4. Watch real-time sync

---

## 🎨 Expressions

### Quick Select
- Click expression button
- Expression applies instantly
- Auto-resets after 2 seconds

### Custom Expressions
1. Adjust parameters to desired state
2. Open Expression Manager
3. Click "Save Current"
4. Name and save

---

## 📊 Parameters

### Common Parameters
- `ParamMouthOpenY`: Mouth opening (0.0 to 1.0)
- `ParamEyeLOpen`: Left eye opening
- `ParamEyeROpen`: Right eye opening
- `ParamMouthForm`: Mouth shape (smile/frown)
- `ParamAngleX`: Head rotation X
- `ParamAngleY`: Head rotation Y
- `ParamAngleZ`: Head rotation Z

### Adjustment
- Use sliders in Parameter Panel
- Search/filter by name
- Reset individual or all parameters
- Export/import parameter sets

---

## 🎬 Animations

### Playback Controls
- ▶️ Play
- ⏸️ Pause
- ⏹️ Stop
- 🔁 Loop toggle
- 🎚️ Speed (0.1x to 3.0x)

### Timeline
- Click to seek
- Drag playhead
- Frame-by-frame stepping
- View parameter curves

---

## 📐 Grid Overlay

### Types
- **Lines**: Regular grid lines
- **Dots**: Dot grid pattern
- **Crosshair**: Center crosshair with ticks

### Settings
- Spacing: 10px to 200px
- Color: Any hex color
- Opacity: 0% to 100%
- Toggle: `G` key

---

## 📈 Performance Monitor

### Metrics
- **FPS**: Frames per second
- **Frame Time**: Milliseconds per frame
- **Memory**: Heap usage in MB
- **Draw Calls**: Render operations
- **Vertices**: Model complexity
- **Textures**: Texture count

### Graph
- 60-second history
- Color-coded FPS (green/yellow/red)
- Target FPS line (60fps)

---

## 💾 Settings

### Auto-Save
All settings automatically saved:
- Viewport position/zoom
- Grid configuration
- Performance monitor visibility
- Control panel state
- Last used model

### Import/Export
**Export**:
1. Click "Export" button
2. Save JSON file

**Import**:
1. Click "Import" button
2. Select JSON file
3. Settings restored

---

## 🎯 Tips & Tricks

### Performance
- Disable grid when not needed
- Close unused control panels
- Reduce parameter update frequency
- Monitor FPS in Performance Monitor

### Testing
- Use Standalone Tool for development
- Test expressions before production
- Export working configurations
- Take screenshots for reference

### Lip Sync
- Ensure audio is playing
- Check volume levels
- Adjust sensitivity if needed
- Test with different audio files

### Expressions
- Create presets for common states
- Export expressions to share
- Test blending between expressions
- Use quick-select for efficiency

---

## 🐛 Troubleshooting

### Lip Sync Not Working
1. Check browser console
2. Verify audio is playing
3. Ensure user interacted with page
4. Try adjusting sensitivity

### Low FPS
1. Check Performance Monitor
2. Disable grid overlay
3. Close other tabs
4. Update graphics drivers

### Model Not Loading
1. Check console for errors
2. Verify model files exist
3. Clear browser cache
4. Try different model

### Controls Not Responding
1. Refresh page
2. Check if model loaded
3. Verify JavaScript enabled
4. Try different browser

---

## 📚 More Information

- [Full Guide](./live2d-advanced-controls-guide.md)
- [Lip Sync Details](./lip-sync-improvements.md)
- [Performance Optimizations](./performance-optimizations.md)
- [API Reference](./agent-reference.md)

---

## 🆘 Support

**Issues?**
1. Check documentation
2. Search existing issues
3. Create new issue with:
   - Browser/OS info
   - Console errors
   - Steps to reproduce

---

**Version**: 1.0.0 | **Last Updated**: January 2026

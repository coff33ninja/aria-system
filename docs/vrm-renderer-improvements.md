# VRM/Live2D Renderer Improvements
## Based on Perplexity Web Renderer Analysis

This document outlines improvements to integrate the excellent VRM renderer logic from `perplexity/perplexity.md` into the Aria Desktop system.

## Key Features from Perplexity Renderer

### 1. **Transparent Click-Through Window**
The perplexity renderer implements a smart click-through system:
- Window is globally transparent and click-through by default
- Only the model area accepts mouse events
- Uses circular hit detection to toggle `setIgnoreMouseEvents()`

**Current Status in Aria:**
- ✅ Already has transparent window (`transparent: true`)
- ✅ Already has frameless window (`frame: false`)
- ❌ Missing: Dynamic click-through based on model hit area

**Recommendation:**
```javascript
// In desktop/electron/main.js
// Add IPC handler for dynamic click-through
ipcMain.on('set-mouse-through', (_event, ignore) => {
  if (mainWindow) {
    mainWindow.setIgnoreMouseEvents(ignore, { forward: true });
  }
});

// In desktop/electron/preload.js
// Expose to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  setMouseThrough: (ignore) => ipcRenderer.send('set-mouse-through', ignore)
});
```

### 2. **Version-Aware Idle Motion Support**
Handles Cubism 2 vs Cubism 4 differences automatically:

```javascript
const CONFIG = {
  idleGroups: {
    cubism2: 'idle',
    cubism4: 'Idle',
    fallback: 'idle'
  }
};

_setupIdleGroup() {
  const motions = this.model.internalModel.settings.motions || {};
  let idleGroup = null;
  
  if (motions[CONFIG.idleGroups.cubism4]) 
    idleGroup = CONFIG.idleGroups.cubism4;
  else if (motions[CONFIG.idleGroups.cubism2]) 
    idleGroup = CONFIG.idleGroups.cubism2;
  else 
    idleGroup = CONFIG.idleGroups.fallback;
  
  this.model.internalModel.motionManager.groups.idle = idleGroup;
}
```

**Current Status:**
- ❌ No version detection
- ❌ Hardcoded idle motion names

**Recommendation:**
Add to `desktop/frontend/app.js` or create new `desktop/frontend/live2d-controller.js`

### 3. **Advanced Interaction System**

#### Mouse Tracking with Built-in Focus Helper
```javascript
// Perplexity uses pixi-live2d-display's built-in focus()
view.addEventListener('pointermove', (e) => {
  if (!this.model) return;
  this.model.focus(e.clientX, e.clientY);
});
```

**Current Status:**
- ✅ Has mouse tracking in `desktop/frontend/app.js`
- ⚠️ Uses manual parameter setting (more control but more code)

**Recommendation:**
Keep current implementation but add `.focus()` as an option for simpler tracking.

#### Hit Area Detection for Interactions
```javascript
// Tap on body to trigger motion
this.model.on('hit', (areas) => {
  if (areas.includes('body')) {
    this.playMotion('Tap', 0, 'NORMAL');
  }
});
```

**Current Status:**
- ❌ No hit area detection
- ❌ No tap-to-interact

**Recommendation:**
Add hit area support for interactive expressions when clicking on the model.

### 4. **Circular Hit Detection for Click-Through**

```javascript
// Approximate circular hit area around model
canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const w = rect.width;
  const h = rect.height;

  const cx = w / 2;
  const cy = h / 2;
  const r = Math.min(w, h) * 0.4; // 40% radius

  const dx = x - cx;
  const dy = y - cy;
  const inside = (dx * dx + dy * dy) <= r * r;

  if (inside !== hoveredModel) {
    hoveredModel = inside;
    window.bridge.setMouseThrough(!inside);
  }
});
```

**Current Status:**
- ❌ No hit detection
- ❌ Window always accepts mouse events

**Recommendation:**
Implement this for true desktop mascot behavior - clicks pass through except on the character.

### 5. **Motion Priority System**

```javascript
playMotion(group, index, priority = 'NORMAL') {
  if (!this.model) return;
  this.model.motion(group, index, { priority });
}
```

**Current Status:**
- ⚠️ Basic motion support
- ❌ No priority system

**Recommendation:**
Add priority levels: `IDLE < NORMAL < FORCE` for better animation control.

### 6. **Auto-Resize Window Based on Scale**

The perplexity renderer has smart window sizing:
```javascript
autoAdjustWindowSize(modelScale, focusMode) {
  const baseDimensions = {
    'face': { width: 300, height: 350 },
    'upper': { width: 400, height: 500 },
    'full': { width: 500, height: 650 }
  };
  
  const base = baseDimensions[focusMode] || baseDimensions['upper'];
  const scaleFactor = Math.sqrt(modelScale); // Square root for smoother scaling
  const newWidth = Math.round(base.width * scaleFactor);
  const newHeight = Math.round(base.height * scaleFactor);
  // ... clamp and apply
}
```

**Current Status:**
- ✅ Already implemented in `desktop/electron/main.js`!
- ✅ Has focus modes (full, upper, face)
- ✅ Has auto-resize toggle

**Recommendation:**
Your implementation is already excellent! Consider adding the square root scaling for smoother feel.

## Implementation Priority

### High Priority (Immediate Impact)
1. **Click-Through Window** - Makes it a true desktop mascot
2. **Version-Aware Idle Motions** - Fixes compatibility issues
3. **Hit Area Detection** - Enables tap-to-interact

### Medium Priority (Quality of Life)
4. **Motion Priority System** - Better animation control
5. **Built-in Focus Helper** - Simpler mouse tracking option
6. **Circular Hit Detection** - More accurate click-through

### Low Priority (Nice to Have)
7. **Square Root Window Scaling** - Smoother resize feel
8. **Multi-Model Support** - Load multiple characters (future)

## Code Structure Recommendations

### Create New Module: `desktop/frontend/live2d-controller.js`

Extract Live2D logic into a clean controller class:

```javascript
class Live2DController {
  constructor(canvas) {
    this.canvas = canvas;
    this.app = null;
    this.model = null;
    this.config = {
      zoomMin: 0.5,
      zoomMax: 2.0,
      idleGroups: {
        cubism2: 'idle',
        cubism4: 'Idle',
        fallback: 'idle'
      }
    };
  }

  async loadModel(url) { /* ... */ }
  _setupIdleGroup() { /* ... */ }
  _setupHitAreas() { /* ... */ }
  playMotion(group, index, priority) { /* ... */ }
  setExpression(name) { /* ... */ }
  focus(x, y) { /* ... */ }
}
```

### Update `desktop/electron/preload.js`

Add new IPC methods:
```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  // Existing methods...
  
  // New methods for click-through
  setMouseThrough: (ignore) => ipcRenderer.send('set-mouse-through', ignore),
  
  // Hit area detection
  onModelHit: (callback) => ipcRenderer.on('model-hit', callback),
  
  // Motion priorities
  playMotionWithPriority: (group, index, priority) => 
    ipcRenderer.send('play-motion', { group, index, priority })
});
```

### Update `desktop/expressions.py`

Add motion priority support:
```python
@dataclass
class ExpressionConfig:
    name: str
    category: str
    priority: str = "NORMAL"  # IDLE, NORMAL, FORCE
    duration: Optional[float] = None
    fade_in: float = 0.5
    fade_out: float = 0.5

# Update MAID_EXPRESSIONS to use ExpressionConfig
MAID_EXPRESSIONS: Dict[str, Dict[str, List[ExpressionConfig]]] = {
    "aria": {
        "happy": [
            ExpressionConfig("heart_eyes", "happy", "NORMAL"),
            ExpressionConfig("blush", "happy", "NORMAL")
        ],
        "sassy": [
            ExpressionConfig("eye_roll", "sassy", "FORCE"),  # Force for strong personality
            ExpressionConfig("dark_face", "sassy", "NORMAL")
        ],
        # ...
    }
}
```

## Testing Checklist

### Click-Through Window
- [ ] Window is transparent
- [ ] Clicks pass through empty areas
- [ ] Clicks work on the model
- [ ] Drag works on the model
- [ ] Hover detection is accurate

### Version Detection
- [ ] Cubism 2 models load correctly
- [ ] Cubism 4 models load correctly
- [ ] Idle animations work for both versions
- [ ] Fallback works for unknown versions

### Hit Areas
- [ ] Tap on face triggers expression
- [ ] Tap on body triggers motion
- [ ] Hit areas match model visually
- [ ] Multiple hit areas work simultaneously

### Motion Priorities
- [ ] IDLE motions can be interrupted
- [ ] NORMAL motions play fully
- [ ] FORCE motions override everything
- [ ] Priority queue works correctly

## Example Usage

### Desktop Mascot with Click-Through
```javascript
// In desktop/frontend/app.js
const controller = new Live2DController(canvas);
await controller.loadModel('/models/aria/aria.model3.json');

// Enable click-through except on model
let hoveredModel = false;
canvas.addEventListener('mousemove', (e) => {
  const inside = controller.isPointInsideModel(e.clientX, e.clientY);
  if (inside !== hoveredModel) {
    hoveredModel = inside;
    window.electronAPI.setMouseThrough(!inside);
  }
});

// Tap to interact
canvas.addEventListener('click', (e) => {
  if (hoveredModel) {
    const hitAreas = controller.getHitAreas(e.clientX, e.clientY);
    if (hitAreas.includes('face')) {
      controller.playMotion('Tap', 0, 'NORMAL');
      controller.setExpression('happy');
    }
  }
});
```

### Expression with Priority
```python
# In desktop/agent.py
from desktop.expressions import get_expression_manager

manager = get_expression_manager()

# Analyze text and get expression with priority
result = manager.get_expression_for_text("aria", "Obviously, I knew that~")
if result:
    expression, category, priority = result
    # Send to frontend with priority
    await send_expression(expression, priority)
```

## Migration Path

### Phase 1: Foundation (Week 1)
1. Create `live2d-controller.js` module
2. Add click-through IPC handlers
3. Implement version detection

### Phase 2: Interactions (Week 2)
4. Add hit area detection
5. Implement motion priorities
6. Add tap-to-interact

### Phase 3: Polish (Week 3)
7. Refine hit detection accuracy
8. Add animation transitions
9. Performance optimization

### Phase 4: Testing (Week 4)
10. Test all Cubism versions
11. Test on multiple monitors
12. Test with all maids
13. User acceptance testing

## Performance Considerations

### Circular Hit Detection
- Cache canvas bounds
- Throttle mousemove events (16ms = 60fps)
- Use requestAnimationFrame for smooth updates

### Model Loading
- Preload common expressions
- Lazy load rare motions
- Cache model data

### Memory Management
- Destroy old models before loading new ones
- Clear unused textures
- Monitor VRAM usage

## Compatibility Notes

### Electron Version
- Requires Electron 13+ for `setIgnoreMouseEvents` with `forward: true`
- Current version in package.json: 30.0.0 ✅

### Live2D SDK
- pixi-live2d-display 0.4.0+ recommended
- Cubism Core 4.0+ for best features
- Backward compatible with Cubism 2.1+

### Operating Systems
- Windows: Full support ✅
- macOS: Full support ✅
- Linux: Click-through may need X11 workarounds ⚠️

## Resources

### Documentation
- [pixi-live2d-display GitHub](https://github.com/guansss/pixi-live2d-display)
- [Electron setIgnoreMouseEvents](https://www.electronjs.org/docs/latest/api/browser-window#winsetignoremouseeventsignore-options)
- [Live2D Cubism SDK](https://www.live2d.com/en/download/cubism-sdk/)

### Example Code
- See `perplexity/perplexity.md` for complete implementation
- Reference `desktop/electron/main.js` for current Aria implementation

## Conclusion

The perplexity renderer provides excellent patterns for:
1. **True desktop mascot behavior** with click-through
2. **Robust version detection** for Cubism compatibility
3. **Interactive hit areas** for engaging user experience
4. **Clean architecture** with separated concerns

Your current Aria implementation already has many of these features partially implemented. The main additions needed are:
- Dynamic click-through based on model position
- Version-aware idle motion detection
- Hit area tap interactions
- Motion priority system

These improvements will make Aria feel more like a true desktop companion that lives on your screen without getting in the way!

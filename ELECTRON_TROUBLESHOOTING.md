# Electron Desktop App - Live2D Model Not Rendering

## Quick Diagnosis

Run this test to identify the issue:

1. **Open the test page in browser:**
   ```bash
   # Start a simple HTTP server
   python -m http.server 8080
   
   # Then open in browser:
   # http://localhost:8080/desktop/electron/test-model-loading.html
   ```

2. **Check the console output** - it will tell you exactly what's failing

## Common Issues & Solutions

### Issue 1: Model Files Not Found
**Symptoms:** Console shows "404 Not Found" or "Failed to load model"

**Solution:**
```bash
# Verify model files exist
dir live2d\models\aria\长离.model3.json
dir live2d\models\luna\Nicole.model3.json

# If missing, check if files are in a different location
dir live2d\models /s /b | findstr model3.json
```

### Issue 2: HTTP Server Not Running
**Symptoms:** "net::ERR_CONNECTION_REFUSED" on port 8080

**Solution:**
```bash
# The Electron app needs the Python backend running
python -m desktop.agent

# Or start just the HTTP server:
python -m desktop.server
```

### Issue 3: PIXI.js Library Not Loading
**Symptoms:** "PIXI is not defined" or blank canvas

**Solution:**
- Check internet connection (libraries load from CDN)
- Open DevTools (F12) and check Network tab for failed requests
- Try the test page first to verify libraries work

### Issue 4: File Path Issues in Electron
**Symptoms:** Model loads in browser but not in Electron

**Solution:**
The recent code changes prioritize local file loading in Electron. Make sure:
1. Model files are in the correct location: `live2d/models/aria/`
2. The preload script has proper file access
3. Check Electron console (Ctrl+Shift+I when running with `--dev` flag)

### Issue 5: Canvas Size is Zero
**Symptoms:** Model loads but nothing visible

**Solution:**
```javascript
// Check in Electron DevTools console:
console.log('Canvas size:', canvas.width, canvas.height);
console.log('Window size:', window.innerWidth, window.innerHeight);
console.log('PIXI screen:', pixiApp.screen.width, pixiApp.screen.height);
```

## Step-by-Step Debugging

### Step 1: Test in Browser First
```bash
# Start HTTP server
python -m desktop.server

# Open browser test page
start http://localhost:8080/desktop/electron/test-model-loading.html
```

If this works, the model files and libraries are OK. Issue is Electron-specific.

### Step 2: Run Electron with DevTools
```bash
cd desktop\electron
npm start -- --dev
```

Press `Ctrl+Shift+I` to open DevTools and check:
- Console for errors
- Network tab for failed requests
- Elements tab to verify canvas exists

### Step 3: Check Model Loading
In Electron DevTools console, run:
```javascript
// Check if PIXI loaded
console.log('PIXI version:', PIXI.VERSION);
console.log('Live2D available:', typeof PIXI.live2d !== 'undefined');

// Check settings
console.log('Settings:', settings);
console.log('Current maid:', currentMaid);

// Try manual load
testScaling();
```

### Step 4: Verify File Paths
In Electron DevTools console:
```javascript
// Check what paths are being tried
console.log('Model paths:', MAIDS.aria);

// Try loading manually
PIXI.live2d.Live2DModel.from('../../live2d/models/aria/长离.model3.json')
    .then(model => console.log('✓ Loaded:', model))
    .catch(err => console.error('✗ Failed:', err));
```

## Recent Code Changes

I've made these fixes to `desktop/electron/avatar.html`:

1. **Fixed PIXI.js version** - Now uses consistent v6.5.10 (was mixing v6 and v7)
2. **Removed conflicting Live2D libraries** - Only loads pixi-live2d-display
3. **Improved path loading** - Electron now tries local files FIRST, then HTTP
4. **Better error messages** - Shows exactly which paths failed and why

## Testing the Fixes

1. **Close Electron app if running**
2. **Restart Electron:**
   ```bash
   cd desktop\electron
   npm start -- --dev
   ```
3. **Open DevTools** (Ctrl+Shift+I)
4. **Watch console** for loading messages

You should see:
```
🚀 Initializing PIXI Application...
✅ PIXI App created - Screen: 400x500
🔄 Loading model from: ...
✅ Model loaded successfully - Dimensions: 2048x2048
✅ Loaded Aria - Model size: 2048x2048
```

## Still Not Working?

If the model still doesn't render after these fixes:

1. **Share the console output** - Copy all messages from Electron DevTools
2. **Check these specific things:**
   - Does the test page work in browser?
   - What's the exact error message?
   - Does the canvas element exist in the DOM?
   - What's the canvas size?

3. **Try the nuclear option:**
   ```bash
   # Reinstall Electron dependencies
   cd desktop\electron
   rmdir /s /q node_modules
   npm install
   ```

## Quick Test Commands

```bash
# Test 1: Verify model files exist
Test-Path live2d\models\aria\长离.model3.json

# Test 2: Start HTTP server
python -m desktop.server

# Test 3: Open test page
start http://localhost:8080/desktop/electron/test-model-loading.html

# Test 4: Run Electron with debug
cd desktop\electron
npm start -- --dev
```

## Expected Console Output (Success)

```
🚀 Initializing PIXI Application...
Canvas size: 400x500
Window size: 400x500
✅ PIXI App created - Screen: 400x500
🔄 Trying local path: ../../live2d/models/aria/长离.model3.json
✅ Loaded from local path
✅ Model loaded successfully - Dimensions: 2048x2048
📊 Model Info:
   Name: 长离
   Version: Cubism 4+
   Motion Groups: Idle, TapBody
   Total Motions: 5
   Expressions: 3
🔧 Applying initial positioning (attempt 1)...
✅ Loaded Aria - Model size: 2048x2048
```

## Need More Help?

Run the test page and share:
1. Full console output from browser test
2. Full console output from Electron DevTools
3. Screenshot of what you see (or don't see)

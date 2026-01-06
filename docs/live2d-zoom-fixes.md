# Live2D Zoom and Scaling Fixes

## Overview

This document details the fixes applied to resolve Live2D avatar scaling and zoom functionality issues in the Electron desktop mode.

## Issues Identified

### 1. Zoom vs Scale Terminology Confusion

**Problem**: The codebase mixed "zoom" (browser/window zoom) with "scale" (model size), causing inconsistent behavior between the main process and renderer process.

**Symptoms**:
- Zoom controls in tray menu not working properly
- Model scaling inconsistent with user settings
- Ctrl+scroll zoom functionality broken

**Root Cause**: 
- `main.js` was using `setModelScale()` for character size
- `avatar.html` was expecting zoom values in legacy handlers
- Mixed usage of `settings.window.zoom` and `settings.avatar.modelScale`

### 2. Disabled Browser Zoom Conflicts

**Problem**: Browser zoom was disabled via `setVisualZoomLevelLimits(1, 1)` but zoom-related handlers still existed, creating dead code paths.

**Impact**: Confusion between browser zoom and character scaling functionality.

### 3. Inconsistent Model Scaling Logic

**Problem**: The `resizeModel()` function had complex logic but wasn't consistently applying user scale settings.

**Issues**:
- Base scale calculation didn't account for all focus modes properly
- User's `modelScale` setting not always applied correctly
- Edge cases in positioning logic

### 6. Window-Character Size Inconsistency

**Problem**: The Electron window size was fixed while the character could be scaled independently, causing clipping when scaled larger or wasted space when scaled smaller.

**Root Cause**: No relationship between window dimensions and character scale/focus mode settings.

### 6. Enhanced Window Auto-Resize System

**File**: `desktop/electron/main.js`

**New Feature**: Automatic window sizing that adapts to character scale and focus mode:

```javascript
function autoAdjustWindowSize(modelScale, focusMode) {
    // Base window dimensions optimized for each focus mode at 100% scale
    const baseDimensions = {
        'face': { width: 300, height: 350 },
        'upper': { width: 400, height: 500 },
        'full': { width: 500, height: 650 }
    };
    
    // Smart scaling using square root to prevent excessive growth
    const scaleFactor = Math.sqrt(modelScale);
    const newWidth = Math.round(base.width * scaleFactor);
    const newHeight = Math.round(base.height * scaleFactor);
    
    // Apply with bounds checking and screen positioning
}
```

**Key Improvements**:
- **Focus Mode Optimization**: Different base window sizes for face (300x350), upper body (400x500), and full body (500x650)
- **Smart Scaling Algorithm**: Uses square root scaling to prevent excessive window growth at high character scales
- **Intelligent Positioning**: Maintains window center point when resizing and ensures it stays on screen
- **User Control**: New tray menu option "Auto-Resize Window" to enable/disable the feature
- **Reasonable Limits**: Clamps window size between 250x300 and 800x900 pixels
- **Threshold-Based Updates**: Only resizes when change is significant (>10 pixels) to avoid constant adjustments

**Benefits**:
- No more character clipping at large scales
- No wasted space at small scales  
- Optimal window size for each focus mode
- Smooth user experience with intelligent positioning
- User can disable if they prefer manual control

## Fixes Applied

### 1. Fixed Legacy Zoom Handler

**File**: `desktop/electron/avatar.html`

```javascript
// Before (broken)
window.electronAPI.onSetZoom((zoom) => {
    currentZoom = zoom;
    resizeModel();
    showStatus(`Zoom: ${Math.round(zoom * 100)}%`);
});

// After (fixed)
window.electronAPI.onSetZoom((zoom) => {
    console.warn('⚠️ Legacy zoom handler called, redirecting to model scale');
    if (settings?.avatar) {
        settings.avatar.modelScale = zoom;
    }
    resizeModel();
    showStatus(`Size: ${Math.round(zoom * 100)}%`);
});
```

**Changes**:
- Added warning for legacy usage
- Properly redirects to model scale settings
- Maintains backward compatibility

### 2. Improved resizeModel() Function

**File**: `desktop/electron/avatar.html`

**Improvements**:
- Added comprehensive error checking and logging
- Cleaner scale calculation logic with proper fallbacks
- Better focus mode handling (face, upper, full)
- Consistent application of user's `modelScale` setting
- Improved positioning logic with manual offset support

**Key Changes**:
```javascript
// Better error handling
if (!live2dModel || !pixiApp) {
    console.log('❌ ResizeModel called but model or app not ready');
    return;
}

// Proper fallbacks for settings
const modelScale = settings?.avatar?.modelScale ?? 1.0;
const modelOffsetY = settings?.avatar?.modelOffsetY ?? 0;
const focusMode = settings?.avatar?.focusMode ?? 'upper';

// Detailed logging for debugging
console.log(`🔧 Resizing model - Scale: ${modelScale}, Focus: ${focusMode}, Offset: ${modelOffsetY}`);
```

### 3. Enhanced Model Loading with Error Handling

**File**: `desktop/electron/avatar.html`

**Improvements**:
- Comprehensive error handling with detailed logging
- Fallback recovery mechanism (falls back to Aria model on failure)
- Better validation of loaded models
- Improved error messages for debugging

**Key Changes**:
```javascript
try {
    console.log(`🔄 Loading model from: ${maid.modelPath}`);
    
    live2dModel = await PIXI.live2d.Live2DModel.from(maid.modelPath, {
        autoInteract: false,
        autoUpdate: true
    });
    
    if (!live2dModel) {
        throw new Error('Model loaded but is null/undefined');
    }
    
    console.log(`✅ Model loaded successfully - Dimensions: ${live2dModel.width}x${live2dModel.height}`);
    
} catch (error) {
    console.error(`❌ Failed to load ${maidId}:`, error);
    showStatus(`Failed to load ${maid.name}: ${error.message}`);
    
    // Fallback recovery
    if (maidId !== 'aria') {
        console.log('🔄 Attempting fallback to Aria model...');
        setTimeout(() => loadMaidModel('aria'), 2000);
    }
}
```

### 5. Added Parameter Validation

**File**: `desktop/electron/avatar.html`

**Improvement**: Enhanced `setModelParameter()` with proper validation and error reporting:

```javascript
function setModelParameter(paramId, value) {
    if (!live2dModel?.internalModel?.coreModel) return;
    try {
        const coreModel = live2dModel.internalModel.coreModel;
        const index = coreModel.getParameterIndex(paramId);
        if (index >= 0) {
            coreModel.setParameterValueByIndex(index, value);
        } else {
            console.warn(`⚠️ Parameter '${paramId}' not found in model`);
        }
    } catch (e) {
        console.error(`❌ Error setting parameter '${paramId}':`, e);
    }
}
```

### 7. Window Auto-Resize System

**File**: `desktop/electron/main.js`

**New Feature**: Intelligent window sizing that automatically adjusts to match character scale and focus mode.

**Key Components**:

1. **`autoAdjustWindowSize()` Function**: 
   - Calculates optimal window size based on character scale and focus mode
   - Uses square root scaling to prevent excessive window growth
   - Maintains window center point during resize
   - Ensures window stays within screen bounds

2. **Focus Mode Base Dimensions**:
   ```javascript
   const baseDimensions = {
       'face': { width: 300, height: 350 },    // Optimized for face view
       'upper': { width: 400, height: 500 },   // Optimized for upper body
       'full': { width: 500, height: 650 }     // Optimized for full body
   };
   ```

3. **Tray Menu Control**: New "Auto-Resize Window" checkbox option to enable/disable the feature

4. **Integration**: Automatically triggered when:
   - Character scale changes (Ctrl+scroll, tray menu)
   - Focus mode changes (face/upper/full)
   - Feature is toggled on

**Benefits**:
- Eliminates character clipping at large scales
- Removes wasted space at small scales
- Provides optimal viewing for each focus mode
- Maintains smooth user experience with intelligent positioning

## Troubleshooting Remaining Issues

### Character Still Loading in Upper Corner

If the character is still appearing in the upper corner instead of being centered, try these debugging steps:

#### 1. Use Debug Functions in Browser Console

Open the Electron app with dev tools and try these console commands:

```javascript
// Check current model state
debugModel()

// Test positioning manually
testPositioning()

// Force center the character
forceCenter()

// Test specific scale values
testScale(1.0)
testScale(1.5)
```

#### 2. Check Settings Loading

Verify that settings are being loaded properly:

```javascript
// Check if settings are loaded
console.log('Settings:', settings)
console.log('Model scale:', settings?.avatar?.modelScale)
console.log('Focus mode:', settings?.avatar?.focusMode)
```

#### 3. Manual Positioning Fix

If the character is stuck in the wrong position, try this manual fix:

```javascript
// Force proper positioning
if (live2dModel && pixiApp) {
    live2dModel.anchor.set(0.5, 0.5);
    live2dModel.x = pixiApp.screen.width / 2;
    live2dModel.y = pixiApp.screen.height * 0.65;
    pixiApp.renderer.render(pixiApp.stage);
    console.log('Character manually centered');
}
```

#### 4. Restart and Reload

Sometimes a simple restart helps:
1. Close the Electron app completely
2. Restart the app
3. Wait for the model to fully load
4. Check if positioning is correct

### Tray Menu Character Size Presets Not Working

If the tray menu character size options aren't working:

#### 1. Check Console for Errors

Look for error messages when clicking tray menu items:
- Open dev tools before using tray menu
- Click a character size preset (e.g., "120%")
- Check console for any error messages

#### 2. Verify Settings Propagation

Test if settings are being sent from main process:

```javascript
// Listen for settings updates
window.electronAPI.onSetModelScale((scale) => {
    console.log('Received scale from tray:', scale);
});

window.electronAPI.onSettingsUpdated((settings) => {
    console.log('Settings updated from tray:', settings);
});
```

#### 3. Manual Scale Test

Test scaling directly from console:

```javascript
// Test if scaling works at all
testScale(0.5)  // 50%
testScale(1.0)  // 100%
testScale(1.5)  // 150%
```

### Settings Not Persisting

If character size settings don't persist between app restarts:

#### 1. Check Settings File

The settings should be saved to a JSON file. Check if it exists and contains your scale settings.

#### 2. Verify Save Function

Test if settings are being saved:

```javascript
// Check current settings
console.log('Current settings:', settings);

// Try manual save (if available)
if (window.electronAPI.saveSettings) {
    window.electronAPI.saveSettings(settings);
}
```

## Testing and Validation

### Debug Functions Added

Several new debug functions are available in the browser console:

1. **`testScaling()`** - Tests the scaling functionality and logs detailed information
2. **`debugModel()`** - Displays current model state and settings  
3. **`testPositioning()`** - Tests manual positioning and logs position data
4. **`testScale(scale)`** - Tests a specific scale value
5. **`forceCenter()`** - Forces the character to center position

### Testing Steps

1. Open Electron app with dev tools (`--dev` flag)
2. Check console for error messages during model loading
3. Test Ctrl+scroll zoom functionality
4. Use tray menu to test character size presets
5. Try different focus modes (full, upper, face)
6. Test model offset adjustments
7. **Use debug functions to isolate positioning issues**
8. **Test tray menu presets with console monitoring**

### Validation Checklist

- [ ] Model loads without errors
- [ ] Scaling responds to user input (Ctrl+scroll, tray menu)
- [ ] Focus modes work correctly (full body, upper body, face)
- [ ] Model positioning is correct for different window sizes
- [ ] **Character loads in center, not upper corner**
- [ ] **Tray menu character size presets work properly**
- [ ] **Settings persist between app restarts**
- [ ] Window auto-resizes to match character scale and focus mode
- [ ] Auto-resize can be toggled on/off via tray menu
- [ ] Window maintains center position during auto-resize
- [ ] Error messages are helpful for debugging
- [ ] Fallback recovery works when models fail to load

## Common Issues and Solutions

### Model Not Loading

**Symptoms**: Avatar area is blank, console shows loading errors

**Solutions**:
1. Check that model files exist at the specified paths
2. Verify HTTP server is serving Live2D models correctly
3. Check browser console for CORS or network errors
4. Ensure model paths in `MAIDS` configuration are correct

### Scaling Not Working

**Symptoms**: Ctrl+scroll or tray menu scaling has no effect

**Solutions**:
1. Check that `settings.avatar.modelScale` is being updated
2. Verify `resizeModel()` is being called after scale changes
3. Use `debugModel()` in console to check current state
4. Ensure model is loaded before attempting to scale

### Window Size Inconsistency

**Symptoms**: Character appears clipped or there's excessive empty space around the avatar

**Solutions**:
1. Enable "Auto-Resize Window" in tray menu → Options
2. Manually adjust window size using tray menu → Display → Window Size
3. Check that character scale and focus mode are appropriate for your screen
4. Use `debugModel()` in console to check current scale and focus settings

### Expression Errors

**Symptoms**: Console warnings about missing parameters

**Solutions**:
1. Check what parameters your Live2D model actually supports
2. Update expression definitions to match model capabilities
3. Use parameter validation warnings to identify unsupported parameters

## Future Improvements

### Recommended Enhancements

1. **Model Validation**: Add startup validation to check model compatibility
2. **Expression Discovery**: Automatically detect available expressions from model
3. **Performance Monitoring**: Add FPS monitoring for animation performance
4. **Model Caching**: Cache loaded models to improve switching speed
5. **Error Recovery**: More sophisticated error recovery and user feedback

### Configuration Improvements

1. **Model Configuration File**: Move model paths and settings to external config
2. **Expression Customization**: Allow users to customize expression mappings
3. **Performance Settings**: Configurable animation quality and FPS limits

## Related Documentation

- [Live2D Integration Guide](live2d-integration-guide.md) - Complete setup guide
- [Electron Desktop Avatar Plan](electron-desktop-avatar-plan.md) - Architecture overview
- [Live2D vs VRM Comparison](live2d-vs-vrm-comparison.md) - Technology comparison

## Changelog

### 2026-01-06 - Latest Update
- **Enhanced Model Loading**: Added multiple positioning attempts with timing delays
- **Improved Settings Propagation**: Added real-time settings updates from tray menu
- **Force Render Updates**: Added multiple render passes to ensure positioning changes stick
- **New Debug Functions**: Added `testPositioning()`, `testScale()`, and `forceCenter()`
- **Better Error Recovery**: Enhanced model loading with retry mechanisms
- **Positioning Fixes**: Improved anchor setting and position calculation timing

### 2026-01-06 - Initial Fixes
- Fixed zoom vs scale terminology confusion
- Improved error handling in model loading
- Enhanced resizeModel() function with better logging
- Added parameter validation with warnings
- Cleaned up legacy zoom settings
- Added debug functions for testing
- Added intelligent window auto-resize system
- Implemented focus mode optimized window dimensions
- Added user control toggle for auto-resize feature
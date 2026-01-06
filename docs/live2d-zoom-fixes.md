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

## Testing and Validation

### Debug Functions Added

Two new debug functions are available in the browser console:

1. **`testScaling()`** - Tests the scaling functionality and logs detailed information
2. **`debugModel()`** - Displays current model state and settings

### Testing Steps

1. Open Electron app with dev tools (`--dev` flag)
2. Check console for error messages during model loading
3. Test Ctrl+scroll zoom functionality
4. Use tray menu to test character size presets
5. Try different focus modes (full, upper, face)
6. Test model offset adjustments

### Validation Checklist

- [ ] Model loads without errors
- [ ] Scaling responds to user input (Ctrl+scroll, tray menu)
- [ ] Focus modes work correctly (full body, upper body, face)
- [ ] Model positioning is correct for different window sizes
- [ ] **Window auto-resizes to match character scale and focus mode**
- [ ] **Auto-resize can be toggled on/off via tray menu**
- [ ] **Window maintains center position during auto-resize**
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

### 2026-01-06
- Fixed zoom vs scale terminology confusion
- Improved error handling in model loading
- Enhanced resizeModel() function with better logging
- Added parameter validation with warnings
- Cleaned up legacy zoom settings
- Added debug functions for testing
- **Added intelligent window auto-resize system**
- **Implemented focus mode optimized window dimensions**
- **Added user control toggle for auto-resize feature**
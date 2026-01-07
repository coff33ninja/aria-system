/**
 * DefaultShortcuts
 * 
 * Default keyboard shortcuts for Live2D controls
 * Can be customized by users
 */

const DEFAULT_SHORTCUTS = {
    // Animation controls
    'Space': {
        description: 'Play/pause animation',
        action: 'animation.playPause'
    },
    'Shift+Space': {
        description: 'Stop animation',
        action: 'animation.stop'
    },
    
    // Viewport controls
    'R': {
        description: 'Reset viewport',
        action: 'viewport.reset'
    },
    'F': {
        description: 'Fit to screen',
        action: 'viewport.fit'
    },
    '+': {
        description: 'Zoom in',
        action: 'viewport.zoomIn'
    },
    '-': {
        description: 'Zoom out',
        action: 'viewport.zoomOut'
    },
    'Up': {
        description: 'Pan up',
        action: 'viewport.panUp'
    },
    'Down': {
        description: 'Pan down',
        action: 'viewport.panDown'
    },
    'Left': {
        description: 'Pan left',
        action: 'viewport.panLeft'
    },
    'Right': {
        description: 'Pan right',
        action: 'viewport.panRight'
    },
    
    // Grid overlay
    'G': {
        description: 'Toggle grid overlay',
        action: 'grid.toggle'
    },
    'Shift+G': {
        description: 'Cycle grid type',
        action: 'grid.cycleType'
    },
    
    // Performance monitor
    'P': {
        description: 'Toggle performance monitor',
        action: 'performance.toggle'
    },
    
    // Maid switching (1-9)
    '1': {
        description: 'Switch to Aria',
        action: 'maid.switch',
        data: 'aria'
    },
    '2': {
        description: 'Switch to Sophia',
        action: 'maid.switch',
        data: 'sophia'
    },
    '3': {
        description: 'Switch to Luna',
        action: 'maid.switch',
        data: 'luna'
    },
    '4': {
        description: 'Switch to Rose',
        action: 'maid.switch',
        data: 'rose'
    },
    '5': {
        description: 'Switch to Mei',
        action: 'maid.switch',
        data: 'mei'
    },
    '6': {
        description: 'Switch to Clara',
        action: 'maid.switch',
        data: 'clara'
    },
    
    // Parameters
    'Ctrl+R': {
        description: 'Reset all parameters',
        action: 'parameters.resetAll'
    },
    
    // Settings
    'Ctrl+S': {
        description: 'Save settings',
        action: 'settings.save'
    },
    'Ctrl+Shift+S': {
        description: 'Save preset',
        action: 'settings.savePreset'
    },
    'Ctrl+O': {
        description: 'Load preset',
        action: 'settings.loadPreset'
    },
    'Ctrl+E': {
        description: 'Export settings',
        action: 'settings.export'
    },
    'Ctrl+I': {
        description: 'Import settings',
        action: 'settings.import'
    },
    
    // Debug panel
    'Ctrl+D': {
        description: 'Toggle debug panel',
        action: 'debug.toggle'
    },
    'Ctrl+Shift+D': {
        description: 'Toggle panel docking',
        action: 'debug.toggleDock'
    },
    
    // Help
    'Shift+/': {
        description: 'Show keyboard shortcuts',
        action: 'help.showShortcuts'
    }
};

/**
 * Setup default shortcuts for Live2D controls
 */
function setupDefaultShortcuts(shortcutManager, controls) {
    const { 
        viewportControls, 
        gridOverlay, 
        performanceMonitor, 
        parameterPanel,
        animationManager,
        settingsManager 
    } = controls;
    
    // Animation controls
    if (animationManager) {
        shortcutManager.register('Space', () => {
            const state = animationManager.getState();
            if (state.isPlaying && !state.isPaused) {
                animationManager.pause();
            } else {
                animationManager.play();
            }
        }, { description: DEFAULT_SHORTCUTS['Space'].description });
        
        shortcutManager.register('Shift+Space', () => {
            animationManager.stop();
        }, { description: DEFAULT_SHORTCUTS['Shift+Space'].description });
    }
    
    // Viewport controls
    if (viewportControls) {
        shortcutManager.register('R', () => {
            viewportControls.reset();
        }, { description: DEFAULT_SHORTCUTS['R'].description });
        
        shortcutManager.register('F', () => {
            viewportControls.fitToScreen();
        }, { description: DEFAULT_SHORTCUTS['F'].description });
        
        shortcutManager.register('+', () => {
            viewportControls.zoomIn();
        }, { description: DEFAULT_SHORTCUTS['+'].description });
        
        shortcutManager.register('-', () => {
            viewportControls.zoomOut();
        }, { description: DEFAULT_SHORTCUTS['-'].description });
        
        shortcutManager.register('Up', () => {
            viewportControls.pan(0, 10);
        }, { description: DEFAULT_SHORTCUTS['Up'].description });
        
        shortcutManager.register('Down', () => {
            viewportControls.pan(0, -10);
        }, { description: DEFAULT_SHORTCUTS['Down'].description });
        
        shortcutManager.register('Left', () => {
            viewportControls.pan(-10, 0);
        }, { description: DEFAULT_SHORTCUTS['Left'].description });
        
        shortcutManager.register('Right', () => {
            viewportControls.pan(10, 0);
        }, { description: DEFAULT_SHORTCUTS['Right'].description });
    }
    
    // Grid overlay
    if (gridOverlay) {
        shortcutManager.register('G', () => {
            gridOverlay.toggle();
        }, { description: DEFAULT_SHORTCUTS['G'].description });
        
        shortcutManager.register('Shift+G', () => {
            const types = ['lines', 'dots', 'crosshair'];
            const current = gridOverlay.getOptions().type;
            const currentIndex = types.indexOf(current);
            const nextIndex = (currentIndex + 1) % types.length;
            gridOverlay.setType(types[nextIndex]);
        }, { description: DEFAULT_SHORTCUTS['Shift+G'].description });
    }
    
    // Performance monitor
    if (performanceMonitor) {
        let perfVisible = true;
        shortcutManager.register('P', () => {
            perfVisible = !perfVisible;
            if (performanceMonitor.container) {
                performanceMonitor.container.style.display = perfVisible ? 'block' : 'none';
            }
        }, { description: DEFAULT_SHORTCUTS['P'].description });
    }
    
    // Parameters
    if (parameterPanel) {
        shortcutManager.register('Ctrl+R', () => {
            parameterPanel.resetAll();
        }, { description: DEFAULT_SHORTCUTS['Ctrl+R'].description });
    }
    
    // Settings
    if (settingsManager) {
        shortcutManager.register('Ctrl+S', () => {
            settingsManager.save();
            console.log('Settings saved');
        }, { description: DEFAULT_SHORTCUTS['Ctrl+S'].description });
        
        shortcutManager.register('Ctrl+E', () => {
            const json = settingsManager.export();
            // Trigger download
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'live2d-settings.json';
            a.click();
            URL.revokeObjectURL(url);
        }, { description: DEFAULT_SHORTCUTS['Ctrl+E'].description });
    }
    
    // Maid switching (if callback provided)
    if (controls.onMaidSwitch) {
        ['1', '2', '3', '4', '5', '6'].forEach((key, index) => {
            const maids = ['aria', 'sophia', 'luna', 'rose', 'mei', 'clara'];
            const maid = maids[index];
            
            shortcutManager.register(key, () => {
                controls.onMaidSwitch(maid);
            }, { description: DEFAULT_SHORTCUTS[key].description });
        });
    }
    
    // Debug panel (if callback provided)
    if (controls.onDebugToggle) {
        shortcutManager.register('Ctrl+D', () => {
            controls.onDebugToggle();
        }, { description: DEFAULT_SHORTCUTS['Ctrl+D'].description });
    }
    
    // Help (if callback provided)
    if (controls.onShowHelp) {
        shortcutManager.register('Shift+/', () => {
            controls.onShowHelp();
        }, { description: DEFAULT_SHORTCUTS['Shift+/'].description });
    }
}

/**
 * Get shortcut hints for UI display
 */
function getShortcutHints() {
    const hints = {};
    
    Object.entries(DEFAULT_SHORTCUTS).forEach(([key, config]) => {
        hints[config.action] = {
            shortcut: key,
            description: config.description
        };
    });
    
    return hints;
}

/**
 * Format shortcut for display
 */
function formatShortcut(shortcut) {
    return shortcut
        .replace('Ctrl', '⌃')
        .replace('Shift', '⇧')
        .replace('Alt', '⌥')
        .replace('Space', '␣');
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DEFAULT_SHORTCUTS,
        setupDefaultShortcuts,
        getShortcutHints,
        formatShortcut
    };
}

/**
 * Live2DControlsIntegration
 * 
 * Integrates all Live2D control components with settings persistence
 * Provides unified interface for managing all controls
 */

class Live2DControlsIntegration {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            autoLoadSettings: true,
            autoSaveSettings: true,
            ...options
        };
        
        // Components
        this.viewportControls = null;
        this.parameterPanel = null;
        this.animationManager = null;
        this.gridOverlay = null;
        this.performanceMonitor = null;
        this.settingsManager = null;
        this.modelInfoPanel = null;
        
        // Initialize
        this._initialize();
    }
    
    /**
     * Initialize all components
     */
    async _initialize() {
        // Create settings manager
        const SettingsManager = require('./SettingsManager');
        this.settingsManager = new SettingsManager({
            autoSave: this.options.autoSaveSettings
        });
        
        // Load settings
        if (this.options.autoLoadSettings) {
            await this.settingsManager.load();
        }
        
        // Initialize components with settings
        this._initializeComponents();
        
        // Setup settings synchronization
        this._setupSettingsSync();
    }
    
    /**
     * Initialize all control components
     */
    _initializeComponents() {
        // Viewport Controls
        const ViewportControls = require('./ViewportControls');
        this.viewportControls = new ViewportControls(this.canvas, {
            minZoom: 0.1,
            maxZoom: 5.0
        });
        
        // Apply saved viewport settings
        const viewportSettings = this.settingsManager.get('viewport');
        if (viewportSettings) {
            this.viewportControls.setState(viewportSettings);
        }
        
        // Grid Overlay
        const GridOverlay = require('./GridOverlay');
        this.gridOverlay = new GridOverlay(this.canvas);
        
        // Apply saved grid settings
        const gridSettings = this.settingsManager.get('grid');
        if (gridSettings) {
            this.gridOverlay.setOptions(gridSettings);
            if (gridSettings.enabled) {
                this.gridOverlay.enable();
            }
        }
        
        // Performance Monitor (if container provided)
        if (this.options.performanceContainer) {
            const PerformanceMonitor = require('./PerformanceMonitor');
            this.performanceMonitor = new PerformanceMonitor(
                this.options.performanceContainer,
                this.settingsManager.get('performance')
            );
        }
        
        // Parameter Panel (if container provided)
        if (this.options.parameterContainer) {
            const ParameterPanel = require('./ParameterPanel');
            this.parameterPanel = new ParameterPanel(
                this.options.parameterContainer
            );
            
            // Load saved parameters
            const parameterSettings = this.settingsManager.get('parameters');
            if (parameterSettings && parameterSettings.values) {
                Object.entries(parameterSettings.values).forEach(([name, value]) => {
                    this.parameterPanel.setParameter(name, value);
                });
            }
        }
        
        // Animation Manager (if container provided)
        if (this.options.animationContainer) {
            const AnimationManager = require('./AnimationManager');
            this.animationManager = new AnimationManager(
                this.options.animationContainer,
                this.settingsManager.get('animations')
            );
        }
        
        // Model Info Panel (if container provided)
        if (this.options.modelInfoContainer) {
            const ModelInfoPanel = require('./ModelInfoPanel');
            this.modelInfoPanel = new ModelInfoPanel.ModelInfoPanel(
                this.options.modelInfoContainer
            );
        }
    }
    
    /**
     * Setup settings synchronization
     */
    _setupSettingsSync() {
        // Viewport changes -> settings
        if (this.viewportControls) {
            this.viewportControls.on('change', (event) => {
                this.settingsManager.set('viewport.x', event.state.x);
                this.settingsManager.set('viewport.y', event.state.y);
                this.settingsManager.set('viewport.zoom', event.state.zoom);
                this.settingsManager.set('viewport.rotation', event.state.rotation);
            });
        }
        
        // Grid changes -> settings
        if (this.gridOverlay) {
            this.gridOverlay.on('change', (event) => {
                const path = `grid.${event.property}`;
                this.settingsManager.set(path, event.value);
            });
        }
        
        // Parameter changes -> settings
        if (this.parameterPanel) {
            this.parameterPanel.on('change', (event) => {
                const path = `parameters.values.${event.parameter}`;
                this.settingsManager.set(path, event.value);
            });
        }
        
        // Animation changes -> settings
        if (this.animationManager) {
            this.animationManager.on('speedChanged', (event) => {
                this.settingsManager.set('animations.speed', event.speed);
            });
            
            this.animationManager.on('loopChanged', (event) => {
                this.settingsManager.set('animations.loop', event.loop);
            });
        }
        
        // Settings changes -> components
        this.settingsManager.on('change', (event) => {
            this._handleSettingsChange(event.path, event.value);
        });
    }
    
    /**
     * Handle settings changes
     */
    _handleSettingsChange(path, value) {
        const parts = path.split('.');
        const section = parts[0];
        
        switch (section) {
            case 'viewport':
                if (this.viewportControls && parts.length > 1) {
                    const state = this.viewportControls.getState();
                    state[parts[1]] = value;
                    this.viewportControls.setState(state);
                }
                break;
                
            case 'grid':
                if (this.gridOverlay && parts.length > 1) {
                    const property = parts[1];
                    if (property === 'enabled') {
                        value ? this.gridOverlay.enable() : this.gridOverlay.disable();
                    } else {
                        const setter = `set${property.charAt(0).toUpperCase() + property.slice(1)}`;
                        if (typeof this.gridOverlay[setter] === 'function') {
                            this.gridOverlay[setter](value);
                        }
                    }
                }
                break;
                
            case 'parameters':
                if (this.parameterPanel && parts.length === 3 && parts[1] === 'values') {
                    this.parameterPanel.updateParameter(parts[2], value);
                }
                break;
        }
    }
    
    /**
     * Get viewport controls
     */
    getViewportControls() {
        return this.viewportControls;
    }
    
    /**
     * Get parameter panel
     */
    getParameterPanel() {
        return this.parameterPanel;
    }
    
    /**
     * Get animation manager
     */
    getAnimationManager() {
        return this.animationManager;
    }
    
    /**
     * Get grid overlay
     */
    getGridOverlay() {
        return this.gridOverlay;
    }
    
    /**
     * Get performance monitor
     */
    getPerformanceMonitor() {
        return this.performanceMonitor;
    }
    
    /**
     * Get model info panel
     */
    getModelInfoPanel() {
        return this.modelInfoPanel;
    }
    
    /**
     * Update model info from Live2D model
     */
    updateModelInfo(live2dModel) {
        if (this.modelInfoPanel && live2dModel) {
            const modelInfo = this.modelInfoPanel.extractModelInfo(live2dModel);
            this.modelInfoPanel.updateModelInfo(modelInfo);
        }
    }
    
    /**
     * Get settings manager
     */
    getSettingsManager() {
        return this.settingsManager;
    }
    
    /**
     * Export all settings
     */
    exportSettings() {
        return this.settingsManager.export();
    }
    
    /**
     * Import settings
     */
    importSettings(json) {
        return this.settingsManager.import(json);
    }
    
    /**
     * Save preset
     */
    savePreset(name, description) {
        return this.settingsManager.savePreset(name, description);
    }
    
    /**
     * Load preset
     */
    loadPreset(name) {
        return this.settingsManager.loadPreset(name);
    }
    
    /**
     * Get all presets
     */
    getPresets() {
        return this.settingsManager.getPresets();
    }
    
    /**
     * Reset all settings
     */
    resetAll() {
        this.settingsManager.reset();
        
        // Reset components
        if (this.viewportControls) this.viewportControls.reset();
        if (this.parameterPanel) this.parameterPanel.resetAll();
        if (this.gridOverlay) this.gridOverlay.disable();
        if (this.performanceMonitor) this.performanceMonitor.reset();
    }
    
    /**
     * Clean up all components
     */
    dispose() {
        if (this.viewportControls) this.viewportControls.dispose();
        if (this.parameterPanel) this.parameterPanel.dispose();
        if (this.animationManager) this.animationManager.dispose();
        if (this.gridOverlay) this.gridOverlay.dispose();
        if (this.performanceMonitor) this.performanceMonitor.dispose();
        if (this.modelInfoPanel) this.modelInfoPanel.dispose();
        if (this.settingsManager) this.settingsManager.dispose();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DControlsIntegration;
}

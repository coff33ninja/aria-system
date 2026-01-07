/**
 * Live2D Controller - Enhanced version with perplexity renderer features
 * 
 * Features:
 * - Version-aware idle motion detection (Cubism 2 vs 4)
 * - Hit area detection for tap interactions
 * - Motion priority system (IDLE < NORMAL < FORCE)
 * - Circular hit detection for click-through windows
 * - Built-in focus helper for mouse tracking
 * - Expression management with fade transitions
 */

class Live2DController {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.app = null;
        this.model = null;
        this.currentMaid = null;
        
        // Configuration
        this.config = {
            zoomMin: options.zoomMin || 0.5,
            zoomMax: options.zoomMax || 2.0,
            // Version-aware idle motion names
            idleGroups: {
                cubism2: 'idle',
                cubism4: 'Idle',
                fallback: 'idle'
            },
            // Hit detection radius (percentage of canvas size)
            hitRadius: options.hitRadius || 0.4,
            // Motion priorities
            motionPriority: {
                IDLE: 0,
                NORMAL: 1,
                FORCE: 2
            },
            // Expression fade times
            expressionFadeIn: 0.5,
            expressionFadeOut: 0.5
        };
        
        // State
        this.viewState = {
            zoom: 1.0,
            panX: 0,
            panY: 0,
            rotationDeg: 0,
            opacity: 1.0
        };
        
        this.interactionState = {
            hoveredModel: false,
            dragging: false,
            dragStart: { x: 0, y: 0 },
            panStart: { x: 0, y: 0 }
        };
        
        // Performance tracking
        this.fps = 0;
        this.lastTime = performance.now();
        
        // Initialize
        this._initPixiApp();
        this._initInteraction();
    }
    
    /**
     * Initialize PIXI Application
     */
    _initPixiApp() {
        this.app = new PIXI.Application({
            view: this.canvas,
            backgroundAlpha: 0,
            resizeTo: window,
            antialias: true,
            autoStart: true
        });
        
        // FPS tracking
        this.app.ticker.add(() => {
            const now = performance.now();
            const dt = now - this.lastTime;
            this.lastTime = now;
            this.fps = 1000 / dt;
        });
    }
    
    /**
     * Load a Live2D model with version detection
     * @param {string} url - Path to model3.json
     * @param {string} maidName - Name of the maid (for tracking)
     * @returns {Promise<Object>} Model info
     */
    async loadModel(url, maidName = 'unknown') {
        console.log(`🎭 Loading model: ${maidName} from ${url}`);
        
        // Cleanup old model
        if (this.model) {
            this.app.stage.removeChild(this.model);
            this.model.destroy(true);
            this.model = null;
        }
        
        try {
            // Load model with idle motion preload
            this.model = await PIXI.live2d.Live2DModel.from(url, {
                motionPreload: PIXI.live2d.MotionPreloadStrategy.IDLE
            });
            
            this.currentMaid = maidName;
            
            // Center model
            this.model.anchor.set(0.5, 0.5);
            this.app.stage.addChild(this.model);
            
            // Setup version-aware idle motions
            this._setupIdleGroup();
            
            // Setup hit areas for interactions
            this._setupHitAreas();
            
            // Apply current view state
            this._applyViewState();
            
            const info = this.getModelInfo();
            console.log(`✅ Model loaded: ${info.name} (${info.version})`);
            console.log(`   Motions: ${info.motions.length}, Expressions: ${info.expressions.length}`);
            
            return info;
            
        } catch (error) {
            console.error('❌ Failed to load model:', error);
            throw error;
        }
    }
    
    /**
     * Setup version-aware idle motion groups
     * Handles Cubism 2 vs Cubism 4 differences
     */
    _setupIdleGroup() {
        if (!this.model) return;
        
        const settings = this.model.internalModel.settings;
        const motions = settings.motions || {};
        
        let idleGroup = null;
        
        // Try Cubism 4 naming first
        if (motions[this.config.idleGroups.cubism4]) {
            idleGroup = this.config.idleGroups.cubism4;
            console.log('📋 Detected Cubism 4 model (Idle motion group)');
        }
        // Fall back to Cubism 2 naming
        else if (motions[this.config.idleGroups.cubism2]) {
            idleGroup = this.config.idleGroups.cubism2;
            console.log('📋 Detected Cubism 2 model (idle motion group)');
        }
        // Use fallback
        else {
            idleGroup = this.config.idleGroups.fallback;
            console.log('⚠️ Unknown Cubism version, using fallback idle group');
        }
        
        // Set idle group for motion manager
        this.model.internalModel.motionManager.groups.idle = idleGroup;
    }
    
    /**
     * Setup hit areas for tap interactions
     */
    _setupHitAreas() {
        if (!this.model) return;
        
        // Enable hit testing
        this.model.interactive = true;
        this.model.buttonMode = true;
        
        // Listen for hit events
        this.model.on('hit', (hitAreas) => {
            console.log('👆 Model hit areas:', hitAreas);
            this._onModelHit(hitAreas);
        });
    }
    
    /**
     * Handle model hit events
     * @param {Array<string>} hitAreas - Names of hit areas
     */
    _onModelHit(hitAreas) {
        // Trigger appropriate motion based on hit area
        if (hitAreas.includes('body') || hitAreas.includes('Body')) {
            this.playMotion('Tap', 0, 'NORMAL');
        }
        else if (hitAreas.includes('head') || hitAreas.includes('Head')) {
            this.playMotion('TapHead', 0, 'NORMAL');
        }
        
        // Emit event for external handling
        if (window.electronAPI && window.electronAPI.onModelHit) {
            window.electronAPI.onModelHit(hitAreas);
        }
    }
    
    /**
     * Initialize mouse/touch interaction
     */
    _initInteraction() {
        const view = this.app.view;
        
        // Mouse wheel zoom
        view.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.05 : 0.05;
            const newZoom = Math.max(
                this.config.zoomMin,
                Math.min(this.config.zoomMax, this.viewState.zoom + delta)
            );
            this.setViewState({ zoom: newZoom });
        }, { passive: false });
        
        // Drag to pan
        view.addEventListener('mousedown', (e) => {
            this.interactionState.dragging = true;
            this.interactionState.dragStart = { x: e.clientX, y: e.clientY };
            this.interactionState.panStart = { 
                x: this.viewState.panX, 
                y: this.viewState.panY 
            };
        });
        
        window.addEventListener('mouseup', () => {
            this.interactionState.dragging = false;
        });
        
        window.addEventListener('mousemove', (e) => {
            // Handle drag
            if (this.interactionState.dragging) {
                const dx = e.clientX - this.interactionState.dragStart.x;
                const dy = e.clientY - this.interactionState.dragStart.y;
                const nx = dx / (this.app.renderer.width / 2);
                const ny = dy / (this.app.renderer.height / 2);
                
                this.setViewState({
                    panX: this.interactionState.panStart.x + nx,
                    panY: this.interactionState.panStart.y + ny
                });
            }
            
            // Update hover state for click-through
            this._updateHoverState(e);
        });
        
        // Mouse tracking using built-in focus helper
        view.addEventListener('pointermove', (e) => {
            if (!this.model) return;
            
            // Use pixi-live2d-display's built-in focus method
            // This handles head/eye tracking automatically
            this.model.focus(e.clientX, e.clientY);
        });
    }
    
    /**
     * Update hover state for click-through window
     * @param {MouseEvent} e - Mouse event
     */
    _updateHoverState(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const inside = this.isPointInsideModel(x, y);
        
        if (inside !== this.interactionState.hoveredModel) {
            this.interactionState.hoveredModel = inside;
            
            // Notify Electron to toggle click-through
            if (window.electronAPI && window.electronAPI.setMouseThrough) {
                window.electronAPI.setMouseThrough(!inside);
            }
        }
    }
    
    /**
     * Check if a point is inside the model's circular hit area
     * @param {number} x - X coordinate (canvas space)
     * @param {number} y - Y coordinate (canvas space)
     * @returns {boolean} True if inside model
     */
    isPointInsideModel(x, y) {
        if (!this.model) return false;
        
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        // Center of canvas
        const cx = w / 2;
        const cy = h / 2;
        
        // Radius based on canvas size and zoom
        const baseRadius = Math.min(w, h) * this.config.hitRadius;
        const radius = baseRadius * this.viewState.zoom;
        
        // Account for pan offset
        const offsetX = this.viewState.panX * (w / 4);
        const offsetY = this.viewState.panY * (h / 4);
        
        // Distance from center
        const dx = x - (cx + offsetX);
        const dy = y - (cy + offsetY);
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        return distance <= radius;
    }
    
    /**
     * Play a motion with priority
     * @param {string} group - Motion group name
     * @param {number} index - Motion index in group
     * @param {string} priority - Priority level (IDLE, NORMAL, FORCE)
     */
    playMotion(group, index = 0, priority = 'NORMAL') {
        if (!this.model) return;
        
        const priorityValue = this.config.motionPriority[priority] || 1;
        
        console.log(`🎬 Playing motion: ${group}[${index}] (priority: ${priority})`);
        
        try {
            this.model.motion(group, index, {
                priority: priorityValue,
                onFinish: () => {
                    console.log(`✅ Motion finished: ${group}[${index}]`);
                }
            });
        } catch (error) {
            console.error(`❌ Failed to play motion ${group}[${index}]:`, error);
        }
    }
    
    /**
     * Stop all motions
     */
    stopMotion() {
        if (!this.model) return;
        this.model.internalModel.motionManager.stopAllMotions();
    }
    
    /**
     * Set expression with fade
     * @param {string} expressionName - Expression name
     */
    setExpression(expressionName) {
        if (!this.model) return;
        
        console.log(`😊 Setting expression: ${expressionName}`);
        
        try {
            this.model.expression(expressionName);
        } catch (error) {
            console.error(`❌ Failed to set expression ${expressionName}:`, error);
        }
    }
    
    /**
     * Update view state (zoom, pan, rotation, opacity)
     * @param {Object} partial - Partial view state to update
     */
    setViewState(partial) {
        Object.assign(this.viewState, partial);
        this._applyViewState();
    }
    
    /**
     * Apply current view state to model
     */
    _applyViewState() {
        if (!this.model) return;
        
        const { zoom, panX, panY, rotationDeg, opacity } = this.viewState;
        const w = this.app.renderer.width;
        const h = this.app.renderer.height;
        
        // Position (center + pan offset)
        this.model.position.set(
            w / 2 + panX * (w / 4),
            h / 2 + panY * (h / 4)
        );
        
        // Scale
        this.model.scale.set(zoom);
        
        // Rotation
        this.model.rotation = (rotationDeg * Math.PI) / 180;
        
        // Opacity
        this.model.alpha = opacity;
    }
    
    /**
     * Get model information
     * @returns {Object} Model info
     */
    getModelInfo() {
        if (!this.model) {
            return {
                name: null,
                version: null,
                motions: [],
                expressions: [],
                hitAreas: []
            };
        }
        
        const settings = this.model.internalModel.settings;
        const motions = settings.motions || {};
        const expressions = settings.expressions || [];
        
        // Collect all motion groups
        const motionList = [];
        Object.keys(motions).forEach(group => {
            motions[group].forEach((motion, idx) => {
                motionList.push(`${group}:${idx}`);
            });
        });
        
        // Detect version
        let version = 'Unknown';
        if (motions['Idle']) version = 'Cubism 4+';
        else if (motions['idle']) version = 'Cubism 2';
        
        return {
            name: settings.name || this.currentMaid || 'Unknown',
            version: version,
            motions: motionList,
            expressions: expressions.map(e => e.Name || e.name),
            hitAreas: settings.hitAreas || [],
            fps: this.fps
        };
    }
    
    /**
     * Get current view state
     * @returns {Object} View state
     */
    getViewState() {
        return { ...this.viewState };
    }
    
    /**
     * Destroy controller and cleanup
     */
    destroy() {
        if (this.model) {
            this.app.stage.removeChild(this.model);
            this.model.destroy(true);
            this.model = null;
        }
        
        if (this.app) {
            this.app.destroy(true);
            this.app = null;
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DController;
}

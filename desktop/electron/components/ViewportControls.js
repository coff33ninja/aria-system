/**
 * ViewportControls Component
 * 
 * Provides pan, zoom, and rotation controls for Live2D viewport
 * Supports mouse/touch input and programmatic control
 */

class ViewportControls {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            minZoom: 0.1,
            maxZoom: 5.0,
            zoomStep: 0.1,
            panStep: 10,
            rotationStep: 15,
            enableMouse: true,
            enableTouch: true,
            enableWheel: true,
            ...options
        };
        
        // Viewport state
        this.state = {
            x: 0,
            y: 0,
            zoom: 1.0,
            rotation: 0
        };
        
        // Initial state for reset
        this.initialState = { ...this.state };
        
        // Mouse/touch tracking
        this.isDragging = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        this.dragStartState = null;
        
        // Event listeners
        this.listeners = new Map();
        
        this._setupEventListeners();
    }
    
    /**
     * Set up mouse and touch event listeners
     */
    _setupEventListeners() {
        if (this.options.enableMouse) {
            this.canvas.addEventListener('mousedown', this._onMouseDown.bind(this));
            this.canvas.addEventListener('mousemove', this._onMouseMove.bind(this));
            this.canvas.addEventListener('mouseup', this._onMouseUp.bind(this));
            this.canvas.addEventListener('mouseleave', this._onMouseUp.bind(this));
        }
        
        if (this.options.enableWheel) {
            this.canvas.addEventListener('wheel', this._onWheel.bind(this), { passive: false });
        }
        
        if (this.options.enableTouch) {
            this.canvas.addEventListener('touchstart', this._onTouchStart.bind(this));
            this.canvas.addEventListener('touchmove', this._onTouchMove.bind(this));
            this.canvas.addEventListener('touchend', this._onTouchEnd.bind(this));
        }
    }
    
    /**
     * Mouse down handler - start dragging
     */
    _onMouseDown(e) {
        this.isDragging = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
        this.dragStartState = { ...this.state };
        this.canvas.style.cursor = 'grabbing';
    }
    
    /**
     * Mouse move handler - pan viewport
     */
    _onMouseMove(e) {
        if (!this.isDragging) return;
        
        const deltaX = e.clientX - this.lastMouseX;
        const deltaY = e.clientY - this.lastMouseY;
        
        this.pan(deltaX, deltaY);
        
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
    }
    
    /**
     * Mouse up handler - stop dragging
     */
    _onMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        }
    }
    
    /**
     * Mouse wheel handler - zoom
     */
    _onWheel(e) {
        e.preventDefault();
        
        const delta = -Math.sign(e.deltaY) * this.options.zoomStep;
        this.zoom(this.state.zoom + delta);
    }
    
    /**
     * Touch start handler
     */
    _onTouchStart(e) {
        if (e.touches.length === 1) {
            this.isDragging = true;
            this.lastMouseX = e.touches[0].clientX;
            this.lastMouseY = e.touches[0].clientY;
            this.dragStartState = { ...this.state };
        }
    }
    
    /**
     * Touch move handler
     */
    _onTouchMove(e) {
        if (!this.isDragging || e.touches.length !== 1) return;
        
        e.preventDefault();
        
        const deltaX = e.touches[0].clientX - this.lastMouseX;
        const deltaY = e.touches[0].clientY - this.lastMouseY;
        
        this.pan(deltaX, deltaY);
        
        this.lastMouseX = e.touches[0].clientX;
        this.lastMouseY = e.touches[0].clientY;
    }
    
    /**
     * Touch end handler
     */
    _onTouchEnd(e) {
        this.isDragging = false;
    }
    
    /**
     * Pan viewport by delta pixels
     */
    pan(deltaX, deltaY) {
        this.state.x += deltaX;
        this.state.y += deltaY;
        this._emitChange('pan');
    }
    
    /**
     * Set absolute pan position
     */
    setPan(x, y) {
        this.state.x = x;
        this.state.y = y;
        this._emitChange('pan');
    }
    
    /**
     * Zoom to specific level
     */
    zoom(level) {
        const newZoom = Math.max(
            this.options.minZoom,
            Math.min(this.options.maxZoom, level)
        );
        
        if (newZoom !== this.state.zoom) {
            const oldZoom = this.state.zoom;
            this.state.zoom = newZoom;
            this._emitChange('zoom', { oldZoom, newZoom });
        }
    }
    
    /**
     * Zoom in by step
     */
    zoomIn() {
        this.zoom(this.state.zoom + this.options.zoomStep);
    }
    
    /**
     * Zoom out by step
     */
    zoomOut() {
        this.zoom(this.state.zoom - this.options.zoomStep);
    }
    
    /**
     * Rotate viewport by degrees
     */
    rotate(degrees) {
        this.state.rotation = (this.state.rotation + degrees) % 360;
        if (this.state.rotation < 0) {
            this.state.rotation += 360;
        }
        this._emitChange('rotate');
    }
    
    /**
     * Set absolute rotation
     */
    setRotation(degrees) {
        this.state.rotation = degrees % 360;
        if (this.state.rotation < 0) {
            this.state.rotation += 360;
        }
        this._emitChange('rotate');
    }
    
    /**
     * Reset viewport to initial state
     */
    reset() {
        const oldState = { ...this.state };
        this.state = { ...this.initialState };
        this._emitChange('reset', { oldState });
    }
    
    /**
     * Fit content to canvas
     */
    fitToScreen() {
        this.state.x = 0;
        this.state.y = 0;
        this.state.zoom = 1.0;
        this.state.rotation = 0;
        this._emitChange('fit');
    }
    
    /**
     * Get current viewport state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Set viewport state
     */
    setState(newState) {
        const oldState = { ...this.state };
        this.state = {
            x: newState.x !== undefined ? newState.x : this.state.x,
            y: newState.y !== undefined ? newState.y : this.state.y,
            zoom: newState.zoom !== undefined ? newState.zoom : this.state.zoom,
            rotation: newState.rotation !== undefined ? newState.rotation : this.state.rotation
        };
        
        // Clamp zoom
        this.state.zoom = Math.max(
            this.options.minZoom,
            Math.min(this.options.maxZoom, this.state.zoom)
        );
        
        this._emitChange('setState', { oldState });
    }
    
    /**
     * Get transformation matrix for rendering
     */
    getTransformMatrix() {
        const { x, y, zoom, rotation } = this.state;
        const rad = (rotation * Math.PI) / 180;
        
        return {
            translateX: x,
            translateY: y,
            scale: zoom,
            rotation: rad,
            cos: Math.cos(rad),
            sin: Math.sin(rad)
        };
    }
    
    /**
     * Apply transformation to canvas context
     */
    applyTransform(ctx) {
        const { x, y, zoom, rotation } = this.state;
        
        ctx.save();
        ctx.translate(x + this.canvas.width / 2, y + this.canvas.height / 2);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.scale(zoom, zoom);
        ctx.translate(-this.canvas.width / 2, -this.canvas.height / 2);
    }
    
    /**
     * Restore canvas context transformation
     */
    restoreTransform(ctx) {
        ctx.restore();
    }
    
    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    /**
     * Remove event listener
     */
    off(event, callback) {
        if (!this.listeners.has(event)) return;
        
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }
    
    /**
     * Emit change event
     */
    _emitChange(type, data = {}) {
        const event = {
            type,
            state: this.getState(),
            ...data
        };
        
        // Emit specific event
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(event));
        }
        
        // Emit general change event
        if (this.listeners.has('change')) {
            this.listeners.get('change').forEach(callback => callback(event));
        }
    }
    
    /**
     * Clean up event listeners
     */
    dispose() {
        this.canvas.removeEventListener('mousedown', this._onMouseDown);
        this.canvas.removeEventListener('mousemove', this._onMouseMove);
        this.canvas.removeEventListener('mouseup', this._onMouseUp);
        this.canvas.removeEventListener('mouseleave', this._onMouseUp);
        this.canvas.removeEventListener('wheel', this._onWheel);
        this.canvas.removeEventListener('touchstart', this._onTouchStart);
        this.canvas.removeEventListener('touchmove', this._onTouchMove);
        this.canvas.removeEventListener('touchend', this._onTouchEnd);
        
        this.listeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ViewportControls;
}

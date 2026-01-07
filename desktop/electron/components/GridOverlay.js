/**
 * GridOverlay Component
 * 
 * Renders customizable grid overlay on canvas
 * Supports lines, dots, and crosshair patterns
 */

class GridOverlay {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = {
            enabled: false,
            type: 'lines', // 'lines', 'dots', 'crosshair'
            spacing: 50,
            color: '#ffffff',
            opacity: 0.3,
            lineWidth: 1,
            dotSize: 2,
            ...options
        };
        
        // Create overlay canvas
        this.overlayCanvas = document.createElement('canvas');
        this.overlayCtx = this.overlayCanvas.getContext('2d');
        
        // Position overlay canvas
        this._setupOverlayCanvas();
        
        // Event listeners
        this.listeners = new Map();
        
        // Cache for grid rendering
        this.renderCache = {
            key: null,
            canvas: null
        };
        
        // Render on next frame
        if (this.options.enabled) {
            this.render();
        }
    }
    
    /**
     * Setup overlay canvas positioning
     */
    _setupOverlayCanvas() {
        this.overlayCanvas.style.position = 'absolute';
        this.overlayCanvas.style.top = '0';
        this.overlayCanvas.style.left = '0';
        this.overlayCanvas.style.pointerEvents = 'none';
        this.overlayCanvas.style.zIndex = '1000';
        
        // Match main canvas size
        this._updateSize();
        
        // Insert overlay after main canvas
        if (this.canvas.parentNode) {
            this.canvas.parentNode.insertBefore(this.overlayCanvas, this.canvas.nextSibling);
        }
        
        // Watch for canvas resize
        this.resizeObserver = new ResizeObserver(() => {
            this._updateSize();
            if (this.options.enabled) {
                this.render();
            }
        });
        this.resizeObserver.observe(this.canvas);
    }
    
    /**
     * Update overlay canvas size to match main canvas
     */
    _updateSize() {
        const rect = this.canvas.getBoundingClientRect();
        this.overlayCanvas.width = rect.width;
        this.overlayCanvas.height = rect.height;
        this.overlayCanvas.style.width = `${rect.width}px`;
        this.overlayCanvas.style.height = `${rect.height}px`;
    }
    
    /**
     * Enable grid overlay
     */
    enable() {
        this.options.enabled = true;
        this.overlayCanvas.style.display = 'block';
        this.render();
        this._emitChange('enabled', true);
    }
    
    /**
     * Disable grid overlay
     */
    disable() {
        this.options.enabled = false;
        this.overlayCanvas.style.display = 'none';
        this._emitChange('enabled', false);
    }
    
    /**
     * Toggle grid overlay
     */
    toggle() {
        if (this.options.enabled) {
            this.disable();
        } else {
            this.enable();
        }
    }
    
    /**
     * Set grid type
     */
    setType(type) {
        if (['lines', 'dots', 'crosshair'].includes(type)) {
            this.options.type = type;
            this._invalidateCache();
            this.render();
            this._emitChange('type', type);
        }
    }
    
    /**
     * Set grid spacing
     */
    setSpacing(spacing) {
        this.options.spacing = Math.max(10, Math.min(200, spacing));
        this._invalidateCache();
        this.render();
        this._emitChange('spacing', this.options.spacing);
    }
    
    /**
     * Set grid color
     */
    setColor(color) {
        this.options.color = color;
        this._invalidateCache();
        this.render();
        this._emitChange('color', color);
    }
    
    /**
     * Set grid opacity
     */
    setOpacity(opacity) {
        this.options.opacity = Math.max(0, Math.min(1, opacity));
        this._invalidateCache();
        this.render();
        this._emitChange('opacity', this.options.opacity);
    }
    
    /**
     * Set line width
     */
    setLineWidth(width) {
        this.options.lineWidth = Math.max(0.5, Math.min(5, width));
        this._invalidateCache();
        this.render();
        this._emitChange('lineWidth', this.options.lineWidth);
    }
    
    /**
     * Set dot size
     */
    setDotSize(size) {
        this.options.dotSize = Math.max(1, Math.min(10, size));
        this._invalidateCache();
        this.render();
        this._emitChange('dotSize', this.options.dotSize);
    }
    
    /**
     * Update multiple options at once
     */
    setOptions(options) {
        Object.assign(this.options, options);
        this._invalidateCache();
        this.render();
        this._emitChange('options', this.options);
    }
    
    /**
     * Get current options
     */
    getOptions() {
        return { ...this.options };
    }
    
    /**
     * Get cache key for current render settings
     */
    _getCacheKey() {
        return `${this.overlayCanvas.width}x${this.overlayCanvas.height}_${this.options.type}_${this.options.spacing}_${this.options.color}_${this.options.opacity}_${this.options.lineWidth}_${this.options.dotSize}`;
    }
    
    /**
     * Check if cached render is valid
     */
    _isCacheValid() {
        const currentKey = this._getCacheKey();
        return this.renderCache.key === currentKey && this.renderCache.canvas !== null;
    }
    
    /**
     * Invalidate render cache
     */
    _invalidateCache() {
        this.renderCache.key = null;
        this.renderCache.canvas = null;
    }
    
    /**
     * Render grid overlay
     */
    render() {
        if (!this.options.enabled) return;
        
        const ctx = this.overlayCtx;
        const width = this.overlayCanvas.width;
        const height = this.overlayCanvas.height;
        
        // Check if we can use cached render
        if (this._isCacheValid()) {
            // Use cached render
            ctx.clearRect(0, 0, width, height);
            ctx.drawImage(this.renderCache.canvas, 0, 0);
            return;
        }
        
        // Create new cache canvas
        const cacheCanvas = document.createElement('canvas');
        cacheCanvas.width = width;
        cacheCanvas.height = height;
        const cacheCtx = cacheCanvas.getContext('2d');
        
        // Set style
        cacheCtx.globalAlpha = this.options.opacity;
        cacheCtx.strokeStyle = this.options.color;
        cacheCtx.fillStyle = this.options.color;
        cacheCtx.lineWidth = this.options.lineWidth;
        
        // Render based on type
        switch (this.options.type) {
            case 'lines':
                this._renderLines(cacheCtx, width, height);
                break;
            case 'dots':
                this._renderDots(cacheCtx, width, height);
                break;
            case 'crosshair':
                this._renderCrosshair(cacheCtx, width, height);
                break;
        }
        
        cacheCtx.globalAlpha = 1.0;
        
        // Store in cache
        this.renderCache.key = this._getCacheKey();
        this.renderCache.canvas = cacheCanvas;
        
        // Draw cached render to overlay
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(cacheCanvas, 0, 0);
    }
    
    /**
     * Render line grid
     */
    _renderLines(ctx, width, height) {
        const spacing = this.options.spacing;
        
        ctx.beginPath();
        
        // Vertical lines
        for (let x = 0; x <= width; x += spacing) {
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
        }
        
        // Horizontal lines
        for (let y = 0; y <= height; y += spacing) {
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
        }
        
        ctx.stroke();
    }
    
    /**
     * Render dot grid
     */
    _renderDots(ctx, width, height) {
        const spacing = this.options.spacing;
        const dotSize = this.options.dotSize;
        
        for (let x = 0; x <= width; x += spacing) {
            for (let y = 0; y <= height; y += spacing) {
                ctx.beginPath();
                ctx.arc(x, y, dotSize, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }
    
    /**
     * Render crosshair grid
     */
    _renderCrosshair(ctx, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const spacing = this.options.spacing;
        
        ctx.beginPath();
        
        // Vertical center line
        ctx.moveTo(centerX, 0);
        ctx.lineTo(centerX, height);
        
        // Horizontal center line
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
        
        // Tick marks
        const tickSize = 10;
        
        // Vertical ticks
        for (let y = centerY % spacing; y <= height; y += spacing) {
            ctx.moveTo(centerX - tickSize, y);
            ctx.lineTo(centerX + tickSize, y);
        }
        
        // Horizontal ticks
        for (let x = centerX % spacing; x <= width; x += spacing) {
            ctx.moveTo(x, centerY - tickSize);
            ctx.lineTo(x, centerY + tickSize);
        }
        
        ctx.stroke();
        
        // Draw center circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
        ctx.fill();
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
    _emitChange(property, value) {
        const event = {
            property,
            value,
            options: this.getOptions()
        };
        
        // Emit specific property change
        if (this.listeners.has(`change:${property}`)) {
            this.listeners.get(`change:${property}`).forEach(callback => callback(event));
        }
        
        // Emit general change event
        if (this.listeners.has('change')) {
            this.listeners.get('change').forEach(callback => callback(event));
        }
    }
    
    /**
     * Export settings as JSON
     */
    exportJSON() {
        return JSON.stringify(this.options, null, 2);
    }
    
    /**
     * Import settings from JSON
     */
    importJSON(json) {
        try {
            const options = typeof json === 'string' ? JSON.parse(json) : json;
            this.setOptions(options);
            return true;
        } catch (error) {
            console.error('Failed to import grid settings:', error);
            return false;
        }
    }
    
    /**
     * Clean up
     */
    dispose() {
        // Remove overlay canvas
        if (this.overlayCanvas.parentNode) {
            this.overlayCanvas.parentNode.removeChild(this.overlayCanvas);
        }
        
        // Disconnect resize observer
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        // Clear cache
        this._invalidateCache();
        
        // Clear listeners
        this.listeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GridOverlay;
}

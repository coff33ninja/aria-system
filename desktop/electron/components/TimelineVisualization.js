/**
 * TimelineVisualization Component
 * 
 * Advanced timeline visualization for Live2D animations
 * Displays keyframes, parameter curves, and supports scrubbing
 */

class TimelineVisualization {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            height: 200,
            timelineHeight: 60,
            curveHeight: 140,
            showParameterCurves: true,
            showKeyframes: true,
            maxVisibleParameters: 5,
            colors: {
                background: 'rgba(0,0,0,0.3)',
                timeline: 'rgba(255,255,255,0.1)',
                playhead: '#ff6b9d',
                keyframe: '#ffa500',
                curve: '#00bfff',
                grid: 'rgba(255,255,255,0.05)'
            },
            ...options
        };
        
        // Animation data
        this.animation = null;
        this.duration = 0;
        this.currentTime = 0;
        this.totalFrames = 0;
        this.fps = 30;
        
        // Keyframes and curves
        this.keyframes = [];
        this.parameterCurves = new Map();
        this.visibleParameters = [];
        
        // Interaction state
        this.isDragging = false;
        this.isHovering = false;
        this.hoverTime = 0;
        
        // Event listeners
        this.listeners = new Map();
        
        // Canvas contexts
        this.timelineCanvas = null;
        this.timelineCtx = null;
        this.curvesCanvas = null;
        this.curvesCtx = null;
        
        this._initializeUI();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="timeline-visualization">
                <div class="timeline-controls">
                    <button class="timeline-step-btn" data-step="-1" title="Previous frame">⏮️</button>
                    <button class="timeline-step-btn" data-step="1" title="Next frame">⏭️</button>
                    <span class="timeline-time">0.00s / 0.00s</span>
                    <button class="timeline-zoom-btn" data-zoom="in" title="Zoom in">🔍+</button>
                    <button class="timeline-zoom-btn" data-zoom="out" title="Zoom out">🔍-</button>
                </div>
                
                <div class="timeline-canvas-container">
                    <canvas class="timeline-canvas"></canvas>
                    <div class="timeline-playhead"></div>
                    <div class="timeline-hover-indicator"></div>
                </div>
                
                ${this.options.showParameterCurves ? `
                    <div class="parameter-curves-container">
                        <div class="curves-header">
                            <span>Parameter Curves</span>
                            <select class="parameter-selector" multiple size="5">
                                <option value="">No parameters</option>
                            </select>
                        </div>
                        <canvas class="curves-canvas"></canvas>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.timelineCanvas = this.container.querySelector('.timeline-canvas');
        this.timelineCtx = this.timelineCanvas?.getContext('2d');
        this.curvesCanvas = this.container.querySelector('.curves-canvas');
        this.curvesCtx = this.curvesCanvas?.getContext('2d');
        this.playhead = this.container.querySelector('.timeline-playhead');
        this.hoverIndicator = this.container.querySelector('.timeline-hover-indicator');
        this.timeDisplay = this.container.querySelector('.timeline-time');
        this.parameterSelector = this.container.querySelector('.parameter-selector');
        
        this._setupEventListeners();
        this._resizeCanvases();
    }
    
    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Step controls
        this.container.querySelectorAll('.timeline-step-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const step = parseInt(e.currentTarget.dataset.step);
                this.stepFrame(step);
            });
        });
        
        // Zoom controls
        this.container.querySelectorAll('.timeline-zoom-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const zoom = e.currentTarget.dataset.zoom;
                if (zoom === 'in') {
                    this.zoomIn();
                } else {
                    this.zoomOut();
                }
            });
        });
        
        // Timeline scrubbing
        if (this.timelineCanvas) {
            this.timelineCanvas.addEventListener('mousedown', (e) => {
                this.isDragging = true;
                this._handleScrub(e);
            });
            
            this.timelineCanvas.addEventListener('mousemove', (e) => {
                this._handleHover(e);
                if (this.isDragging) {
                    this._handleScrub(e);
                }
            });
            
            this.timelineCanvas.addEventListener('mouseup', () => {
                this.isDragging = false;
            });
            
            this.timelineCanvas.addEventListener('mouseleave', () => {
                this.isDragging = false;
                this.isHovering = false;
                if (this.hoverIndicator) {
                    this.hoverIndicator.style.display = 'none';
                }
            });
            
            this.timelineCanvas.addEventListener('mouseenter', () => {
                this.isHovering = true;
            });
        }
        
        // Parameter selection
        if (this.parameterSelector) {
            this.parameterSelector.addEventListener('change', (e) => {
                this.visibleParameters = Array.from(e.target.selectedOptions)
                    .map(opt => opt.value)
                    .filter(v => v !== '');
                this._drawCurves();
            });
        }
        
        // Window resize
        window.addEventListener('resize', () => {
            this._resizeCanvases();
            this.render();
        });
    }
    
    /**
     * Set animation data
     */
    setAnimation(animation, metadata = {}) {
        try {
            this.animation = animation;
            this.duration = metadata.duration || 0;
            this.totalFrames = metadata.frameCount || 0;
            this.fps = metadata.fps || 30;
            this.keyframes = metadata.keyframes || [];
            
            // Validate animation data
            if (this.duration <= 0) {
                console.warn('Animation duration is zero or negative');
            }
            
            if (this.totalFrames <= 0) {
                console.warn('Animation has no frames');
            }
            
            // Extract parameter curves if available
            if (metadata.parameterCurves) {
                this.parameterCurves = new Map(Object.entries(metadata.parameterCurves));
                this._updateParameterSelector();
            }
            
            this.render();
        } catch (error) {
            console.error('Failed to set animation:', error);
            this._emitEvent('error', {
                message: `Failed to load animation data: ${error.message}`,
                animation
            });
        }
    }
    
    /**
     * Update current time
     */
    setCurrentTime(time) {
        this.currentTime = Math.max(0, Math.min(this.duration, time));
        this._updatePlayhead();
        this._updateTimeDisplay();
        this._drawCurves();
    }
    
    /**
     * Set current frame
     */
    setCurrentFrame(frame) {
        const time = (frame / this.fps);
        this.setCurrentTime(time);
    }
    
    /**
     * Step forward/backward by frames
     */
    stepFrame(step) {
        const currentFrame = Math.floor(this.currentTime * this.fps);
        const newFrame = Math.max(0, Math.min(this.totalFrames - 1, currentFrame + step));
        this.setCurrentFrame(newFrame);
        this._emitEvent('seek', { time: this.currentTime, frame: newFrame });
    }
    
    /**
     * Zoom in
     */
    zoomIn() {
        // Implement zoom functionality
        this._emitEvent('zoom', { direction: 'in' });
    }
    
    /**
     * Zoom out
     */
    zoomOut() {
        // Implement zoom functionality
        this._emitEvent('zoom', { direction: 'out' });
    }
    
    /**
     * Handle scrubbing
     */
    _handleScrub(e) {
        if (!this.timelineCanvas) return;
        
        const rect = this.timelineCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const progress = x / rect.width;
        const time = progress * this.duration;
        
        this.setCurrentTime(time);
        this._emitEvent('scrub', { time: this.currentTime });
    }
    
    /**
     * Handle hover
     */
    _handleHover(e) {
        if (!this.timelineCanvas || !this.hoverIndicator) return;
        
        const rect = this.timelineCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const progress = x / rect.width;
        this.hoverTime = progress * this.duration;
        
        // Update hover indicator
        this.hoverIndicator.style.display = 'block';
        this.hoverIndicator.style.left = `${x}px`;
        this.hoverIndicator.textContent = `${this.hoverTime.toFixed(2)}s`;
    }
    
    /**
     * Resize canvases
     */
    _resizeCanvases() {
        if (this.timelineCanvas) {
            this.timelineCanvas.width = this.timelineCanvas.offsetWidth;
            this.timelineCanvas.height = this.options.timelineHeight;
        }
        
        if (this.curvesCanvas) {
            this.curvesCanvas.width = this.curvesCanvas.offsetWidth;
            this.curvesCanvas.height = this.options.curveHeight;
        }
    }
    
    /**
     * Update playhead position
     */
    _updatePlayhead() {
        if (!this.playhead || this.duration === 0) return;
        
        const progress = this.currentTime / this.duration;
        const x = progress * this.timelineCanvas.offsetWidth;
        this.playhead.style.left = `${x}px`;
    }
    
    /**
     * Update time display
     */
    _updateTimeDisplay() {
        if (!this.timeDisplay) return;
        
        const current = this.currentTime.toFixed(2);
        const total = this.duration.toFixed(2);
        const frame = Math.floor(this.currentTime * this.fps);
        
        this.timeDisplay.textContent = `${current}s / ${total}s (Frame ${frame})`;
    }
    
    /**
     * Update parameter selector
     */
    _updateParameterSelector() {
        if (!this.parameterSelector) return;
        
        this.parameterSelector.innerHTML = '';
        
        this.parameterCurves.forEach((curve, paramName) => {
            const option = document.createElement('option');
            option.value = paramName;
            option.textContent = paramName;
            this.parameterSelector.appendChild(option);
        });
        
        // Select first few parameters by default
        const options = Array.from(this.parameterSelector.options);
        options.slice(0, this.options.maxVisibleParameters).forEach(opt => {
            opt.selected = true;
        });
        
        this.visibleParameters = options
            .slice(0, this.options.maxVisibleParameters)
            .map(opt => opt.value);
    }
    
    /**
     * Render timeline
     */
    _drawTimeline() {
        if (!this.timelineCanvas || !this.timelineCtx) return;
        
        const ctx = this.timelineCtx;
        const width = this.timelineCanvas.width;
        const height = this.timelineCanvas.height;
        
        // Clear
        ctx.clearRect(0, 0, width, height);
        
        // Background
        ctx.fillStyle = this.options.colors.background;
        ctx.fillRect(0, 0, width, height);
        
        // Show loading state if no animation data
        if (this.duration === 0 || !this.animation) {
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('No animation data loaded', width / 2, height / 2);
            return;
        }
        
        // Grid lines (every second)
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        
        const secondWidth = width / this.duration;
        for (let i = 0; i <= this.duration; i++) {
            const x = i * secondWidth;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
            
            // Time labels
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '10px monospace';
            ctx.fillText(`${i}s`, x + 2, 12);
        }
        
        // Keyframes
        if (this.options.showKeyframes && this.keyframes.length > 0) {
            ctx.fillStyle = this.options.colors.keyframe;
            
            this.keyframes.forEach(keyframe => {
                const x = (keyframe.time / this.duration) * width;
                ctx.beginPath();
                ctx.arc(x, height / 2, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        }
        
        // Current time indicator
        const currentX = (this.currentTime / this.duration) * width;
        ctx.strokeStyle = this.options.colors.playhead;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(currentX, 0);
        ctx.lineTo(currentX, height);
        ctx.stroke();
    }
    
    /**
     * Draw parameter curves
     */
    _drawCurves() {
        if (!this.curvesCanvas || !this.curvesCtx || !this.options.showParameterCurves) return;
        
        const ctx = this.curvesCtx;
        const width = this.curvesCanvas.width;
        const height = this.curvesCanvas.height;
        
        // Clear
        ctx.clearRect(0, 0, width, height);
        
        // Background
        ctx.fillStyle = this.options.colors.background;
        ctx.fillRect(0, 0, width, height);
        
        // Show loading state if no animation data
        if (this.duration === 0 || !this.animation) {
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('No parameter curve data available', width / 2, height / 2);
            return;
        }
        
        // Grid
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        
        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = (i / 4) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Vertical grid lines (every second)
        const secondWidth = width / this.duration;
        for (let i = 0; i <= this.duration; i++) {
            const x = i * secondWidth;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        
        // Draw curves for visible parameters
        const colors = ['#ff6b9d', '#00bfff', '#00ff00', '#ffa500', '#ff00ff'];
        
        this.visibleParameters.forEach((paramName, index) => {
            const curveData = this.parameterCurves.get(paramName);
            if (!curveData || curveData.length === 0) return;
            
            const color = colors[index % colors.length];
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            curveData.forEach((point, i) => {
                const x = (point.time / this.duration) * width;
                const y = height - ((point.value + 1) / 2) * height; // Map -1 to 1 to canvas height
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Draw parameter name
            ctx.fillStyle = color;
            ctx.font = '11px monospace';
            ctx.fillText(paramName, 5, 15 + index * 15);
        });
        
        // Current time indicator
        const currentX = (this.currentTime / this.duration) * width;
        ctx.strokeStyle = this.options.colors.playhead;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(currentX, 0);
        ctx.lineTo(currentX, height);
        ctx.stroke();
    }
    
    /**
     * Render all visualizations
     */
    render() {
        this._drawTimeline();
        this._drawCurves();
        this._updatePlayhead();
        this._updateTimeDisplay();
    }
    
    /**
     * Get current state
     */
    getState() {
        return {
            animation: this.animation,
            currentTime: this.currentTime,
            duration: this.duration,
            totalFrames: this.totalFrames,
            fps: this.fps,
            visibleParameters: this.visibleParameters
        };
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
     * Emit event
     */
    _emitEvent(type, data = {}) {
        const event = {
            type,
            state: this.getState(),
            ...data
        };
        
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(event));
        }
    }
    
    /**
     * Clean up
     */
    dispose() {
        this.listeners.clear();
        this.parameterCurves.clear();
        this.keyframes = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimelineVisualization;
}

// Default styles
const TIMELINE_VISUALIZATION_STYLES = `
.timeline-visualization {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #fff;
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
    padding: 12px;
}

.timeline-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.timeline-step-btn,
.timeline-zoom-btn {
    padding: 4px 8px;
    font-size: 14px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s;
}

.timeline-step-btn:hover,
.timeline-zoom-btn:hover {
    background: rgba(255,255,255,0.2);
}

.timeline-time {
    flex: 1;
    font-family: monospace;
    font-size: 11px;
    color: #aaa;
    text-align: center;
}

.timeline-canvas-container {
    position: relative;
    margin-bottom: 12px;
}

.timeline-canvas {
    width: 100%;
    display: block;
    border-radius: 4px;
    cursor: pointer;
}

.timeline-playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff6b9d;
    pointer-events: none;
    z-index: 2;
}

.timeline-hover-indicator {
    position: absolute;
    top: -20px;
    transform: translateX(-50%);
    padding: 2px 6px;
    background: rgba(0,0,0,0.8);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 3px;
    font-size: 10px;
    font-family: monospace;
    color: #fff;
    pointer-events: none;
    white-space: nowrap;
    display: none;
    z-index: 3;
}

.parameter-curves-container {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

.curves-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}

.curves-header span {
    font-size: 12px;
    font-weight: 600;
    color: #ff6b9d;
}

.parameter-selector {
    font-size: 10px;
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    padding: 4px;
    max-width: 150px;
}

.parameter-selector option {
    padding: 2px 4px;
}

.parameter-selector option:checked {
    background: rgba(255,107,157,0.3);
}

.curves-canvas {
    width: 100%;
    display: block;
    border-radius: 4px;
}
`;

// Export styles
if (typeof module !== 'undefined' && module.exports) {
    module.exports.TIMELINE_VISUALIZATION_STYLES = TIMELINE_VISUALIZATION_STYLES;
}

/**
 * PerformanceMonitor Component
 * 
 * Tracks and displays performance metrics for Live2D rendering
 * Monitors FPS, frame time, memory usage, and draw calls
 */

class PerformanceMonitor {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            updateInterval: 100, // ms
            historyLength: 60, // seconds of history
            showGraph: true,
            targetFPS: 60,
            ...options
        };
        
        // Metrics
        this.metrics = {
            fps: 0,
            frameTime: 0,
            memory: 0,
            drawCalls: 0,
            vertices: 0,
            textures: 0
        };
        
        // History for graphs
        this.history = {
            fps: [],
            frameTime: [],
            memory: []
        };
        
        // Tracking
        this.frameCount = 0;
        this.lastTime = performance.now();
        this.lastUpdateTime = performance.now();
        this.frameTimes = [];
        
        // Event listeners
        this.listeners = new Map();
        
        // Update loop
        this.updateIntervalId = null;
        
        // RAF-throttled graph rendering
        this.rafId = null;
        this.pendingGraphUpdate = false;
        
        this._initializeUI();
        this.start();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="performance-monitor">
                <div class="perf-metrics">
                    <div class="perf-metric" data-metric="fps">
                        <div class="perf-label">FPS</div>
                        <div class="perf-value">60</div>
                    </div>
                    <div class="perf-metric" data-metric="frameTime">
                        <div class="perf-label">Frame Time</div>
                        <div class="perf-value">16ms</div>
                    </div>
                    <div class="perf-metric" data-metric="memory">
                        <div class="perf-label">Memory</div>
                        <div class="perf-value">0MB</div>
                    </div>
                    <div class="perf-metric" data-metric="drawCalls">
                        <div class="perf-label">Draw Calls</div>
                        <div class="perf-value">0</div>
                    </div>
                </div>
                <div class="perf-graph" style="display: ${this.options.showGraph ? 'block' : 'none'}">
                    <canvas class="perf-canvas"></canvas>
                </div>
                <div class="perf-details">
                    <div class="perf-detail">Vertices: <span class="perf-vertices">0</span></div>
                    <div class="perf-detail">Textures: <span class="perf-textures">0</span></div>
                </div>
            </div>
        `;
        
        this.canvas = this.container.querySelector('.perf-canvas');
        this.ctx = this.canvas?.getContext('2d');
        
        if (this.canvas) {
            this._setupCanvas();
        }
    }
    
    /**
     * Setup canvas for graph
     */
    _setupCanvas() {
        const updateSize = () => {
            this.canvas.width = this.canvas.offsetWidth;
            this.canvas.height = this.canvas.offsetHeight || 100;
        };
        
        updateSize();
        
        // Watch for resize
        this.resizeObserver = new ResizeObserver(updateSize);
        this.resizeObserver.observe(this.canvas);
    }
    
    /**
     * Start monitoring
     */
    start() {
        if (this.updateIntervalId) return;
        
        this.lastTime = performance.now();
        this.lastUpdateTime = performance.now();
        
        this.updateIntervalId = setInterval(() => {
            this._update();
        }, this.options.updateInterval);
    }
    
    /**
     * Stop monitoring
     */
    stop() {
        if (this.updateIntervalId) {
            clearInterval(this.updateIntervalId);
            this.updateIntervalId = null;
        }
    }
    
    /**
     * Record a frame
     */
    recordFrame() {
        const now = performance.now();
        const deltaTime = now - this.lastTime;
        
        this.frameCount++;
        this.frameTimes.push(deltaTime);
        
        // Keep only recent frame times
        if (this.frameTimes.length > 60) {
            this.frameTimes.shift();
        }
        
        this.lastTime = now;
    }
    
    /**
     * Set draw call count
     */
    setDrawCalls(count) {
        this.metrics.drawCalls = count;
    }
    
    /**
     * Set vertex count
     */
    setVertices(count) {
        this.metrics.vertices = count;
    }
    
    /**
     * Set texture count
     */
    setTextures(count) {
        this.metrics.textures = count;
    }
    
    /**
     * Set model complexity metrics
     */
    setModelMetrics(metrics) {
        if (metrics.drawCalls !== undefined) this.metrics.drawCalls = metrics.drawCalls;
        if (metrics.vertices !== undefined) this.metrics.vertices = metrics.vertices;
        if (metrics.textures !== undefined) this.metrics.textures = metrics.textures;
    }
    
    /**
     * Update metrics
     */
    _update() {
        const now = performance.now();
        const elapsed = now - this.lastUpdateTime;
        
        // Calculate FPS
        if (this.frameCount > 0) {
            this.metrics.fps = Math.round((this.frameCount / elapsed) * 1000);
            this.frameCount = 0;
        }
        
        // Calculate average frame time
        if (this.frameTimes.length > 0) {
            const sum = this.frameTimes.reduce((a, b) => a + b, 0);
            this.metrics.frameTime = sum / this.frameTimes.length;
        }
        
        // Get memory usage
        if (performance.memory) {
            this.metrics.memory = performance.memory.usedJSHeapSize / 1024 / 1024; // MB
        }
        
        // Update history
        this.history.fps.push(this.metrics.fps);
        this.history.frameTime.push(this.metrics.frameTime);
        this.history.memory.push(this.metrics.memory);
        
        // Trim history
        const maxLength = (this.options.historyLength * 1000) / this.options.updateInterval;
        Object.keys(this.history).forEach(key => {
            if (this.history[key].length > maxLength) {
                this.history[key].shift();
            }
        });
        
        this.lastUpdateTime = now;
        
        // Update UI
        this._updateUI();
        
        // Emit update event
        this._emitEvent('update', this.metrics);
    }
    
    /**
     * Update UI display
     */
    _updateUI() {
        // Update metric values
        const fpsValue = this.container.querySelector('[data-metric="fps"] .perf-value');
        const frameTimeValue = this.container.querySelector('[data-metric="frameTime"] .perf-value');
        const memoryValue = this.container.querySelector('[data-metric="memory"] .perf-value');
        const drawCallsValue = this.container.querySelector('[data-metric="drawCalls"] .perf-value');
        
        if (fpsValue) {
            fpsValue.textContent = this.metrics.fps;
            
            // Color code FPS
            const fpsPercent = this.metrics.fps / this.options.targetFPS;
            if (fpsPercent >= 0.9) {
                fpsValue.style.color = '#4ade80'; // green
            } else if (fpsPercent >= 0.6) {
                fpsValue.style.color = '#fbbf24'; // yellow
            } else {
                fpsValue.style.color = '#f87171'; // red
            }
        }
        
        if (frameTimeValue) {
            frameTimeValue.textContent = `${this.metrics.frameTime.toFixed(1)}ms`;
        }
        
        if (memoryValue) {
            memoryValue.textContent = `${this.metrics.memory.toFixed(1)}MB`;
        }
        
        if (drawCallsValue) {
            drawCallsValue.textContent = this.metrics.drawCalls;
        }
        
        // Update details
        const verticesSpan = this.container.querySelector('.perf-vertices');
        const texturesSpan = this.container.querySelector('.perf-textures');
        
        if (verticesSpan) {
            verticesSpan.textContent = this.metrics.vertices.toLocaleString();
        }
        
        if (texturesSpan) {
            texturesSpan.textContent = this.metrics.textures;
        }
        
        // Schedule graph update using RAF throttling
        if (this.options.showGraph) {
            this._scheduleGraphUpdate();
        }
    }
    
    /**
     * Schedule graph update using requestAnimationFrame
     * Ensures graph is only redrawn once per frame, even if metrics update multiple times
     */
    _scheduleGraphUpdate() {
        if (this.rafId !== null) {
            // Already scheduled
            return;
        }
        
        this.rafId = requestAnimationFrame(() => {
            this._drawGraph();
            this.rafId = null;
        });
    }
    
    /**
     * Draw performance graph
     */
    _drawGraph() {
        if (!this.canvas || !this.ctx) return;
        
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Clear
        ctx.clearRect(0, 0, width, height);
        
        // Background
        ctx.fillStyle = 'rgba(0,0,0,0.2)';
        ctx.fillRect(0, 0, width, height);
        
        // Draw FPS graph
        this._drawLine(
            this.history.fps,
            '#ff6b9d',
            0,
            this.options.targetFPS * 1.5
        );
        
        // Draw target FPS line
        const targetY = height - (this.options.targetFPS / (this.options.targetFPS * 1.5)) * height;
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(0, targetY);
        ctx.lineTo(width, targetY);
        ctx.stroke();
        ctx.setLineDash([]);
    }
    
    /**
     * Draw line graph
     */
    _drawLine(data, color, min, max) {
        if (data.length === 0) return;
        
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const step = width / Math.max(data.length - 1, 1);
        
        data.forEach((value, index) => {
            const x = index * step;
            const normalizedValue = (value - min) / (max - min);
            const y = height - (normalizedValue * height);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
    }
    
    /**
     * Get current metrics
     */
    getMetrics() {
        return { ...this.metrics };
    }
    
    /**
     * Get metrics history
     */
    getHistory() {
        return {
            fps: [...this.history.fps],
            frameTime: [...this.history.frameTime],
            memory: [...this.history.memory]
        };
    }
    
    /**
     * Reset metrics
     */
    reset() {
        this.frameCount = 0;
        this.frameTimes = [];
        this.history.fps = [];
        this.history.frameTime = [];
        this.history.memory = [];
        
        this.metrics = {
            fps: 0,
            frameTime: 0,
            memory: 0,
            drawCalls: 0,
            vertices: 0,
            textures: 0
        };
        
        this._updateUI();
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
    _emitEvent(type, data) {
        const event = {
            type,
            metrics: this.getMetrics(),
            ...data
        };
        
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(event));
        }
    }
    
    /**
     * Export metrics as JSON
     */
    exportJSON() {
        return JSON.stringify({
            metrics: this.metrics,
            history: this.history
        }, null, 2);
    }
    
    /**
     * Clean up
     */
    dispose() {
        this.stop();
        
        // Cancel any pending RAF
        if (this.rafId !== null) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        this.listeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
}

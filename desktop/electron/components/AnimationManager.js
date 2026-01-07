/**
 * AnimationManager Component
 * 
 * Manages Live2D animations with playback controls
 * Supports play/pause/stop, speed control, looping, and timeline scrubbing
 */

class AnimationManager {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            minSpeed: 0.1,
            maxSpeed: 3.0,
            defaultSpeed: 1.0,
            showTimeline: true,
            useAdvancedTimeline: false, // Use TimelineVisualization component
            ...options
        };
        
        // Animation storage
        this.animations = new Map();
        
        // Playback state
        this.currentAnimation = null;
        this.isPlaying = false;
        this.isPaused = false;
        this.speed = this.options.defaultSpeed;
        this.loop = false;
        this.currentFrame = 0;
        this.totalFrames = 0;
        
        // Event listeners
        this.listeners = new Map();
        
        // Animation frame tracking
        this.lastFrameTime = 0;
        this.animationFrameId = null;
        
        // Advanced timeline visualization
        this.timelineVisualization = null;
        
        this._initializeUI();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="animation-manager">
                <div class="animation-controls">
                    <button class="anim-control-btn" data-action="play" title="Play">▶️</button>
                    <button class="anim-control-btn" data-action="pause" title="Pause">⏸️</button>
                    <button class="anim-control-btn" data-action="stop" title="Stop">⏹️</button>
                    <label class="anim-loop-toggle">
                        <input type="checkbox" class="anim-loop-checkbox">
                        <span>Loop</span>
                    </label>
                    <div class="anim-speed-control">
                        <label>Speed:</label>
                        <input type="range" class="anim-speed-slider" 
                            min="${this.options.minSpeed * 100}" 
                            max="${this.options.maxSpeed * 100}" 
                            value="${this.speed * 100}">
                        <span class="anim-speed-value">${this.speed.toFixed(1)}x</span>
                    </div>
                </div>
                ${this.options.useAdvancedTimeline ? `
                    <div class="advanced-timeline-container"></div>
                ` : `
                    <div class="animation-timeline" style="display: ${this.options.showTimeline ? 'block' : 'none'}">
                        <canvas class="timeline-canvas"></canvas>
                        <div class="timeline-info">
                            <span class="timeline-current">0</span> / <span class="timeline-total">0</span>
                        </div>
                    </div>
                `}
                <div class="animation-list"></div>
                <div class="animation-empty-state" style="display: none;">
                    <div style="text-align: center; padding: 20px; color: #aaa;">
                        <div style="font-size: 32px; margin-bottom: 8px;">🎬</div>
                        <div style="font-size: 12px;">No animations available</div>
                        <div style="font-size: 10px; margin-top: 4px;">Load a model with animations to get started</div>
                    </div>
                </div>
            </div>
        `;
        
        this.listContainer = this.container.querySelector('.animation-list');
        this.emptyState = this.container.querySelector('.animation-empty-state');
        this.timelineCanvas = this.container.querySelector('.timeline-canvas');
        this.timelineCtx = this.timelineCanvas?.getContext('2d');
        this.currentFrameSpan = this.container.querySelector('.timeline-current');
        this.totalFramesSpan = this.container.querySelector('.timeline-total');
        
        // Initialize advanced timeline if enabled
        if (this.options.useAdvancedTimeline) {
            this._initializeAdvancedTimeline();
        }
        
        this._setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Playback controls
        this.container.querySelectorAll('.anim-control-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this[action]();
            });
        });
        
        // Loop toggle
        const loopCheckbox = this.container.querySelector('.anim-loop-checkbox');
        loopCheckbox.addEventListener('change', (e) => {
            this.loop = e.target.checked;
            this._emitEvent('loopChanged', { loop: this.loop });
        });
        
        // Speed control
        const speedSlider = this.container.querySelector('.anim-speed-slider');
        const speedValue = this.container.querySelector('.anim-speed-value');
        
        speedSlider.addEventListener('input', (e) => {
            this.speed = parseFloat(e.target.value) / 100;
            speedValue.textContent = `${this.speed.toFixed(1)}x`;
            this._emitEvent('speedChanged', { speed: this.speed });
        });
        
        // Timeline scrubbing
        if (this.timelineCanvas) {
            this.timelineCanvas.addEventListener('click', (e) => {
                const rect = this.timelineCanvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const frame = Math.floor((x / rect.width) * this.totalFrames);
                this.seekToFrame(frame);
            });
        }
    }
    
    /**
     * Add animation
     */
    addAnimation(name, metadata = {}) {
        const anim = {
            name,
            duration: metadata.duration || 0,
            frameCount: metadata.frameCount || 0,
            fps: metadata.fps || 30,
            loop: metadata.loop !== undefined ? metadata.loop : false,
            ...metadata
        };
        
        this.animations.set(name, anim);
        this._addAnimationToUI(anim);
        this._updateEmptyState();
    }
    
    /**
     * Initialize advanced timeline visualization
     */
    _initializeAdvancedTimeline() {
        const timelineContainer = this.container.querySelector('.advanced-timeline-container');
        if (!timelineContainer) return;
        
        // Check if TimelineVisualization is available
        if (typeof TimelineVisualization === 'undefined') {
            console.warn('TimelineVisualization component not loaded');
            return;
        }
        
        this.timelineVisualization = new TimelineVisualization(timelineContainer, {
            showParameterCurves: true,
            showKeyframes: true
        });
        
        // Connect timeline events to animation manager
        this.timelineVisualization.on('scrub', (event) => {
            const frame = Math.floor(event.time * this.fps);
            this.seekToFrame(frame);
        });
        
        this.timelineVisualization.on('seek', (event) => {
            this.seekToFrame(event.frame);
        });
    }
    
    /**
     * Update advanced timeline
     */
    _updateAdvancedTimeline() {
        if (!this.timelineVisualization) return;
        
        const currentTime = this.currentFrame / this.fps;
        this.timelineVisualization.setCurrentTime(currentTime);
    }
    
    /**
     * Set animation data in advanced timeline
     */
    _setTimelineAnimation(animName) {
        if (!this.timelineVisualization) return;
        
        const anim = this.animations.get(animName);
        if (!anim) return;
        
        this.timelineVisualization.setAnimation(animName, {
            duration: anim.duration,
            frameCount: anim.frameCount,
            fps: anim.fps,
            keyframes: anim.keyframes || [],
            parameterCurves: anim.parameterCurves || {}
        });
    }
    
    /**
     * Remove animation
     */
    removeAnimation(name) {
        this.animations.delete(name);
        
        const element = this.listContainer.querySelector(`[data-anim-name="${name}"]`);
        if (element) {
            element.remove();
        }
        
        if (this.currentAnimation === name) {
            this.stop();
        }
        
        this._updateEmptyState();
    }
    
    /**
     * Clear all animations
     */
    clear() {
        this.stop();
        this.animations.clear();
        this.listContainer.innerHTML = '';
        this._updateEmptyState();
    }
    
    /**
     * Play animation
     */
    play(animationName = null) {
        if (animationName) {
            this.currentAnimation = animationName;
            this.currentFrame = 0;
        }
        
        if (!this.currentAnimation) {
            console.warn('No animation selected');
            this._emitEvent('error', { 
                message: 'No animation selected. Please select an animation first.' 
            });
            return;
        }
        
        const anim = this.animations.get(this.currentAnimation);
        if (!anim) {
            const errorMsg = `Animation '${this.currentAnimation}' not found`;
            console.error(errorMsg);
            this._emitEvent('error', { 
                message: errorMsg,
                animation: this.currentAnimation
            });
            return;
        }
        
        this.isPlaying = true;
        this.isPaused = false;
        this.totalFrames = anim.frameCount;
        this.fps = anim.fps;
        this.lastFrameTime = performance.now();
        
        // Set animation in advanced timeline
        if (this.timelineVisualization) {
            this._setTimelineAnimation(this.currentAnimation);
        }
        
        this._updateUI();
        this._startAnimationLoop();
        this._emitEvent('play', { animation: this.currentAnimation });
    }
    
    /**
     * Pause animation
     */
    pause() {
        if (!this.isPlaying) return;
        
        this.isPaused = true;
        this._stopAnimationLoop();
        this._updateUI();
        this._emitEvent('pause', { animation: this.currentAnimation, frame: this.currentFrame });
    }
    
    /**
     * Stop animation
     */
    stop() {
        this.isPlaying = false;
        this.isPaused = false;
        this.currentFrame = 0;
        
        this._stopAnimationLoop();
        this._updateUI();
        this._emitEvent('stop', { animation: this.currentAnimation });
    }
    
    /**
     * Seek to specific frame
     */
    seekToFrame(frame) {
        if (!this.currentAnimation) {
            console.warn('Cannot seek: No animation selected');
            return;
        }
        
        if (this.totalFrames === 0) {
            console.warn('Cannot seek: Animation has no frames');
            return;
        }
        
        this.currentFrame = Math.max(0, Math.min(this.totalFrames - 1, frame));
        this._updateUI();
        this._emitEvent('seek', { animation: this.currentAnimation, frame: this.currentFrame });
    }
    
    /**
     * Step forward one frame
     */
    stepForward() {
        this.seekToFrame(this.currentFrame + 1);
    }
    
    /**
     * Step backward one frame
     */
    stepBackward() {
        this.seekToFrame(this.currentFrame - 1);
    }
    
    /**
     * Start animation loop
     */
    _startAnimationLoop() {
        if (this.animationFrameId) return;
        
        const animate = () => {
            if (!this.isPlaying || this.isPaused) {
                this.animationFrameId = null;
                return;
            }
            
            const now = performance.now();
            const deltaTime = (now - this.lastFrameTime) / 1000; // seconds
            this.lastFrameTime = now;
            
            const anim = this.animations.get(this.currentAnimation);
            if (!anim) {
                this.stop();
                return;
            }
            
            // Calculate frame increment based on speed and FPS
            const frameIncrement = deltaTime * anim.fps * this.speed;
            this.currentFrame += frameIncrement;
            
            // Handle loop or stop at end
            if (this.currentFrame >= this.totalFrames) {
                if (this.loop) {
                    this.currentFrame = this.currentFrame % this.totalFrames;
                    this._emitEvent('loop', { animation: this.currentAnimation });
                } else {
                    this.currentFrame = this.totalFrames - 1;
                    this.stop();
                    this._emitEvent('complete', { animation: this.currentAnimation });
                    return;
                }
            }
            
            this._updateUI();
            this._emitEvent('frame', { 
                animation: this.currentAnimation, 
                frame: Math.floor(this.currentFrame),
                progress: this.currentFrame / this.totalFrames
            });
            
            this.animationFrameId = requestAnimationFrame(animate);
        };
        
        this.animationFrameId = requestAnimationFrame(animate);
    }
    
    /**
     * Stop animation loop
     */
    _stopAnimationLoop() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }
    
    /**
     * Add animation to UI
     */
    _addAnimationToUI(anim) {
        const item = document.createElement('div');
        item.className = 'animation-item';
        item.dataset.animName = anim.name;
        
        item.innerHTML = `
            <div class="animation-info">
                <span class="animation-name">${anim.name}</span>
                <span class="animation-duration">${anim.duration.toFixed(1)}s</span>
            </div>
            <div class="animation-actions">
                <button class="anim-play-btn" data-anim="${anim.name}">▶️</button>
            </div>
        `;
        
        const playBtn = item.querySelector('.anim-play-btn');
        playBtn.addEventListener('click', () => {
            this.play(anim.name);
        });
        
        this.listContainer.appendChild(item);
    }
    
    /**
     * Update empty state visibility
     */
    _updateEmptyState() {
        if (!this.emptyState || !this.listContainer) return;
        
        const hasAnimations = this.animations.size > 0;
        this.emptyState.style.display = hasAnimations ? 'none' : 'block';
        this.listContainer.style.display = hasAnimations ? 'block' : 'none';
    }
    
    /**
     * Update UI state
     */
    _updateUI() {
        // Update control buttons
        const playBtn = this.container.querySelector('[data-action="play"]');
        const pauseBtn = this.container.querySelector('[data-action="pause"]');
        
        if (playBtn) playBtn.disabled = this.isPlaying && !this.isPaused;
        if (pauseBtn) pauseBtn.disabled = !this.isPlaying || this.isPaused;
        
        // Update timeline
        if (this.currentFrameSpan) {
            this.currentFrameSpan.textContent = Math.floor(this.currentFrame);
        }
        if (this.totalFramesSpan) {
            this.totalFramesSpan.textContent = this.totalFrames;
        }
        
        // Update timeline canvas (basic timeline)
        this._drawTimeline();
        
        // Update advanced timeline
        this._updateAdvancedTimeline();
        
        // Highlight current animation
        this.listContainer.querySelectorAll('.animation-item').forEach(item => {
            const isActive = item.dataset.animName === this.currentAnimation;
            item.classList.toggle('active', isActive);
        });
    }
    
    /**
     * Draw timeline visualization
     */
    _drawTimeline() {
        if (!this.timelineCanvas || !this.timelineCtx) return;
        
        const canvas = this.timelineCanvas;
        const ctx = this.timelineCtx;
        
        // Set canvas size
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight || 40;
        
        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.totalFrames === 0) return;
        
        // Draw background
        ctx.fillStyle = 'rgba(0,0,0,0.2)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw progress
        const progress = this.currentFrame / this.totalFrames;
        ctx.fillStyle = '#ff6b9d';
        ctx.fillRect(0, 0, canvas.width * progress, canvas.height);
        
        // Draw playhead
        const playheadX = canvas.width * progress;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(playheadX, 0);
        ctx.lineTo(playheadX, canvas.height);
        ctx.stroke();
    }
    
    /**
     * Get current state
     */
    getState() {
        return {
            currentAnimation: this.currentAnimation,
            isPlaying: this.isPlaying,
            isPaused: this.isPaused,
            currentFrame: Math.floor(this.currentFrame),
            totalFrames: this.totalFrames,
            speed: this.speed,
            loop: this.loop
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
        this.stop();
        this.listeners.clear();
        this.clear();
        
        // Dispose advanced timeline
        if (this.timelineVisualization) {
            this.timelineVisualization.dispose();
            this.timelineVisualization = null;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationManager;
}

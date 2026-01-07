/**
 * LipSyncAnalyzer - Real-time audio analysis for lip sync
 * 
 * Analyzes audio streams and converts volume to mouth parameters
 * for natural-looking Live2D lip sync animation
 */

class LipSyncAnalyzer {
    constructor(options = {}) {
        this.options = {
            smoothing: 0.7,
            sensitivity: 1.2,
            minVolume: 0.01,
            maxMouthOpen: 0.9,
            fftSize: 2048,
            ...options
        };
        
        // Audio context and analyzer
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.source = null;
        
        // State
        this.isActive = false;
        this.currentVolume = 0.0;
        this.smoothedVolume = 0.0;
        this.mouthOpenValue = 0.0;
        
        // Animation frame
        this.rafId = null;
        
        // Callbacks
        this.onMouthUpdate = null;
        this.onVolumeUpdate = null;
    }
    
    /**
     * Initialize audio context
     */
    async initialize() {
        if (this.audioContext) return;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🎤 LipSyncAnalyzer initialized');
        } catch (error) {
            console.error('Failed to initialize audio context:', error);
            throw error;
        }
    }
    
    /**
     * Connect to an audio stream for analysis
     * 
     * @param {MediaStream} stream - Audio stream to analyze
     */
    async connectStream(stream) {
        if (!this.audioContext) {
            await this.initialize();
        }
        
        try {
            // Create analyzer node
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = this.options.fftSize;
            this.analyser.smoothingTimeConstant = 0.8;
            
            // Create data array for frequency data
            const bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(bufferLength);
            
            // Connect stream to analyzer
            this.source = this.audioContext.createMediaStreamSource(stream);
            this.source.connect(this.analyser);
            
            // Start analysis loop
            this.isActive = true;
            this._startAnalysis();
            
            console.log('🎤 Connected to audio stream for lip sync');
            
        } catch (error) {
            console.error('Failed to connect audio stream:', error);
            throw error;
        }
    }
    
    /**
     * Connect to an HTML audio element
     * 
     * @param {HTMLAudioElement} audioElement - Audio element to analyze
     */
    async connectAudioElement(audioElement) {
        if (!this.audioContext) {
            await this.initialize();
        }
        
        try {
            // Create analyzer node
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = this.options.fftSize;
            this.analyser.smoothingTimeConstant = 0.8;
            
            // Create data array
            const bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(bufferLength);
            
            // Connect audio element to analyzer
            this.source = this.audioContext.createMediaElementSource(audioElement);
            this.source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination); // Also output to speakers
            
            // Start analysis loop
            this.isActive = true;
            this._startAnalysis();
            
            console.log('🎤 Connected to audio element for lip sync');
            
        } catch (error) {
            console.error('Failed to connect audio element:', error);
            throw error;
        }
    }
    
    /**
     * Start the analysis loop
     */
    _startAnalysis() {
        if (!this.isActive || !this.analyser) return;
        
        const analyze = () => {
            if (!this.isActive) return;
            
            // Get frequency data
            this.analyser.getByteFrequencyData(this.dataArray);
            
            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < this.dataArray.length; i++) {
                sum += this.dataArray[i];
            }
            const avgVolume = sum / this.dataArray.length / 255.0;
            
            // Apply smoothing
            this.currentVolume = avgVolume;
            this.smoothedVolume = this.smoothedVolume * this.options.smoothing + 
                                  avgVolume * (1.0 - this.options.smoothing);
            
            // Convert to mouth opening with curve for natural movement
            this.mouthOpenValue = this._volumeToMouthOpen(this.smoothedVolume);
            
            // Trigger callbacks
            if (this.onMouthUpdate) {
                this.onMouthUpdate(this.mouthOpenValue);
            }
            
            if (this.onVolumeUpdate) {
                this.onVolumeUpdate(this.smoothedVolume);
            }
            
            // Continue loop
            this.rafId = requestAnimationFrame(analyze);
        };
        
        analyze();
    }
    
    /**
     * Convert volume level to mouth opening value
     * 
     * @param {number} volume - Volume level (0.0 to 1.0)
     * @returns {number} Mouth opening value (0.0 to 1.0)
     */
    _volumeToMouthOpen(volume) {
        // Apply minimum threshold
        if (volume < this.options.minVolume) {
            return 0.0;
        }
        
        // Apply sensitivity
        let adjusted = volume * this.options.sensitivity;
        
        // Apply power curve for more natural movement
        // Lower power = more sensitive to quiet sounds
        const power = 0.6;
        let mouthOpen = Math.pow(adjusted, power);
        
        // Clamp to max mouth opening
        mouthOpen = Math.min(mouthOpen, this.options.maxMouthOpen);
        
        return Math.max(0.0, Math.min(1.0, mouthOpen));
    }
    
    /**
     * Stop analysis and disconnect
     */
    stop() {
        this.isActive = false;
        
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        
        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }
        
        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }
        
        this.currentVolume = 0.0;
        this.smoothedVolume = 0.0;
        this.mouthOpenValue = 0.0;
        
        console.log('🎤 LipSyncAnalyzer stopped');
    }
    
    /**
     * Get current mouth opening value
     * 
     * @returns {number} Current mouth opening (0.0 to 1.0)
     */
    getMouthOpen() {
        return this.mouthOpenValue;
    }
    
    /**
     * Get current volume level
     * 
     * @returns {number} Current volume (0.0 to 1.0)
     */
    getVolume() {
        return this.smoothedVolume;
    }
    
    /**
     * Check if voice is currently active
     * 
     * @returns {boolean} True if speaking
     */
    isVoiceActive() {
        return this.smoothedVolume > this.options.minVolume;
    }
    
    /**
     * Update options
     * 
     * @param {Object} options - Options to update
     */
    setOptions(options) {
        Object.assign(this.options, options);
    }
    
    /**
     * Clean up resources
     */
    dispose() {
        this.stop();
        
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.dataArray = null;
        this.onMouthUpdate = null;
        this.onVolumeUpdate = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LipSyncAnalyzer;
}

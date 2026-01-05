/**
 * Live2D Frontend Renderer for Aria Maid System
 * 
 * Integrates Live2D Cubism SDK with LiveKit for real-time avatar rendering.
 * Handles model loading, parameter updates, and audio synchronization.
 */

import { Live2DCubismFramework } from '@framework/live2dcubismframework';
import { CubismDefaultParameterId } from '@framework/cubismdefaultparameterid';
import { CubismModelSettingJson } from '@framework/cubismmodelsettingjson';
import { CubismUserModel } from '@framework/cubismusermodel';
import { Room, Track, TrackKind } from 'livekit-client';

/**
 * Live2D Avatar Renderer for LiveKit integration
 */
class LiveKitLive2DAvatar {
    constructor(canvasId, liveKitRoom) {
        this.canvas = document.getElementById(canvasId);
        this.gl = this.canvas.getContext('webgl2') || this.canvas.getContext('webgl');
        this.room = liveKitRoom;
        
        // Live2D components
        this.model = null;
        this.modelSetting = null;
        this.framework = null;
        
        // Animation state
        this.currentExpression = 'idle';
        this.parameters = new Map();
        this.animationTasks = new Map();
        
        // Audio analysis
        this.audioContext = null;
        this.audioAnalyzer = null;
        this.lipSyncValue = 0.0;
        this.isInitialized = false;
        
        // Maid configuration
        this.maidName = '';
        this.maidConfig = {};
        
        console.log('🎭 Live2D Avatar renderer created');
    }
    
    /**
     * Initialize Live2D framework and set up LiveKit integration
     */
    async initialize() {
        try {
            // Initialize Live2D Cubism Framework
            this.framework = Live2DCubismFramework.getInstance();
            await this.framework.initialize();
            
            // Set up canvas and WebGL
            this._setupCanvas();
            
            // Set up LiveKit event handlers
            this._setupLiveKitHandlers();
            
            // Set up audio analysis
            await this._setupAudioAnalysis();
            
            this.isInitialized = true;
            console.log('✨ Live2D Avatar renderer initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize Live2D renderer:', error);
            throw error;
        }
    }
    
    /**
     * Load a Live2D model for a specific maid
     */
    async loadMaidModel(maidName, modelPath, config) {
        if (!this.isInitialized) {
            throw new Error('Renderer not initialized');
        }
        
        this.maidName = maidName;
        this.maidConfig = config;
        
        try {
            // Load model setting JSON
            const settingResponse = await fetch(`${modelPath}/${maidName}.model3.json`);
            const settingJson = await settingResponse.json();
            this.modelSetting = new CubismModelSettingJson(settingJson);
            
            // Create and load model
            this.model = new CubismUserModel();
            await this.model.loadModel(this.modelSetting, modelPath);
            
            // Set up model parameters
            this._initializeModelParameters();
            
            // Start animation loop
            this._startAnimationLoop();
            
            // Set initial expression
            await this.setExpression(config.default_expression || 'idle');
            
            console.log(`🎭 ${maidName} model loaded successfully`);
            
        } catch (error) {
            console.error(`❌ Failed to load model for ${maidName}:`, error);
            throw error;
        }
    }
    
    /**
     * Set facial expression
     */
    async setExpression(expressionName, duration = 0.5) {
        if (!this.model || !this.maidConfig.expressions) {
            return;
        }
        
        const expression = this.maidConfig.expressions[expressionName];
        if (!expression) {
            console.warn(`⚠️ Unknown expression '${expressionName}' for ${this.maidName}`);
            return;
        }
        
        // Cancel existing expression animation
        if (this.animationTasks.has('expression')) {
            this.animationTasks.get('expression').cancel();
        }
        
        // Start new expression animation
        const animationTask = this._animateToParameters(expression, duration);
        this.animationTasks.set('expression', animationTask);
        
        this.currentExpression = expressionName;
        console.log(`😊 ${this.maidName} expression changed to '${expressionName}'`);
    }
    
    /**
     * Update parameter value with smooth animation
     */
    async updateParameter(parameterName, targetValue, duration = 0.1) {
        if (!this.model) return;
        
        const currentValue = this.parameters.get(parameterName) || 0.0;
        
        // Create smooth animation
        const startTime = performance.now();
        const animate = () => {
            const elapsed = (performance.now() - startTime) / 1000;
            const progress = Math.min(elapsed / duration, 1.0);
            
            // Easing function (ease-in-out cubic)
            const easedProgress = progress < 0.5 
                ? 4 * progress * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 3) / 2;
            
            const currentValue = this.parameters.get(parameterName) || 0.0;
            const newValue = currentValue + (targetValue - currentValue) * easedProgress;
            
            this._setParameter(parameterName, newValue);
            
            if (progress < 1.0) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    /**
     * Set up canvas and WebGL context
     */
    _setupCanvas() {
        if (!this.gl) {
            throw new Error('WebGL not supported');
        }
        
        // Set canvas size
        this.canvas.width = 800;
        this.canvas.height = 600;
        
        // Configure WebGL
        this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        this.gl.clearColor(0.0, 0.0, 0.0, 0.0); // Transparent background
        this.gl.enable(this.gl.BLEND);
        this.gl.blendFunc(this.gl.SRC_ALPHA, this.gl.ONE_MINUS_SRC_ALPHA);
    }
    
    /**
     * Set up LiveKit event handlers
     */
    _setupLiveKitHandlers() {
        // Handle data messages from backend
        this.room.on('dataReceived', (data, participant) => {
            try {
                const message = JSON.parse(new TextDecoder().decode(data));
                this._handleBackendMessage(message);
            } catch (error) {
                console.error('❌ Failed to parse data message:', error);
            }
        });
        
        // Handle audio tracks for lip sync
        this.room.on('trackSubscribed', (track, participant) => {
            if (track.kind === TrackKind.Audio) {
                this._handleAudioTrack(track, participant);
            }
        });
        
        console.log('🔗 LiveKit handlers set up');
    }
    
    /**
     * Handle messages from Python backend
     */
    _handleBackendMessage(message) {
        switch (message.type) {
            case 'live2d_init':
                this.loadMaidModel(
                    message.maid_name,
                    message.model_path,
                    {
                        expressions: message.expressions,
                        animation_speed: message.animation_speed,
                        default_expression: 'idle'
                    }
                );
                break;
                
            case 'live2d_parameter':
                if (message.maid_name === this.maidName) {
                    this.updateParameter(message.parameter, message.value);
                }
                break;
                
            case 'live2d_expression':
                if (message.maid_name === this.maidName) {
                    this.setExpression(message.expression, message.duration || 0.5);
                }
                break;
                
            default:
                console.log('📨 Unknown message type:', message.type);
        }
    }
    
    /**
     * Set up audio analysis for lip sync
     */
    async _setupAudioAnalysis() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.audioAnalyzer = this.audioContext.createAnalyser();
            this.audioAnalyzer.fftSize = 256;
            
            console.log('🎤 Audio analysis set up');
        } catch (error) {
            console.error('❌ Failed to set up audio analysis:', error);
        }
    }
    
    /**
     * Handle audio track for lip sync
     */
    _handleAudioTrack(track, participant) {
        if (!this.audioContext || !this.audioAnalyzer) {
            return;
        }
        
        // Check if this is a maid's audio track
        if (participant.identity.includes('live2d-')) {
            const maidName = participant.identity.replace('live2d-', '');
            
            if (maidName === this.maidName.toLowerCase()) {
                // Connect audio track to analyzer
                const mediaStream = new MediaStream([track.mediaStreamTrack]);
                const source = this.audioContext.createMediaStreamSource(mediaStream);
                source.connect(this.audioAnalyzer);
                
                // Start lip sync analysis
                this._startLipSyncAnalysis();
                
                console.log(`🎤 Connected audio track for ${this.maidName}`);
            }
        }
    }
    
    /**
     * Start real-time lip sync analysis
     */
    _startLipSyncAnalysis() {
        const bufferLength = this.audioAnalyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const analyze = () => {
            if (!this.model) {
                requestAnimationFrame(analyze);
                return;
            }
            
            // Get audio data
            this.audioAnalyzer.getByteFrequencyData(dataArray);
            
            // Calculate volume level
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const averageVolume = sum / bufferLength / 255.0;
            
            // Convert to mouth opening (with curve for natural movement)
            this.lipSyncValue = Math.pow(averageVolume, 0.5) * 0.9;
            
            // Update mouth parameter
            this._setParameter('ParamMouthOpenY', this.lipSyncValue);
            
            requestAnimationFrame(analyze);
        };
        
        analyze();
    }
    
    /**
     * Initialize model parameters
     */
    _initializeModelParameters() {
        if (!this.model) return;
        
        // Set default parameter values
        const defaultParams = {
            'ParamEyeLOpen': 1.0,
            'ParamEyeROpen': 1.0,
            'ParamEyeBallX': 0.0,
            'ParamEyeBallY': 0.0,
            'ParamMouthOpenY': 0.0,
            'ParamMouthForm': 0.0,
            'ParamAngleX': 0.0,
            'ParamAngleY': 0.0,
            'ParamAngleZ': 0.0,
            'ParamBodyAngleX': 0.0,
            'ParamBodyAngleY': 0.0,
            'ParamBodyAngleZ': 0.0,
            'ParamBreath': 0.7
        };
        
        for (const [paramName, value] of Object.entries(defaultParams)) {
            this._setParameter(paramName, value);
        }
        
        console.log('🎛️ Model parameters initialized');
    }
    
    /**
     * Set a single parameter value
     */
    _setParameter(parameterName, value) {
        if (!this.model) return;
        
        // Clamp value to valid range
        const clampedValue = Math.max(-1.0, Math.min(1.0, value));
        
        // Update model parameter
        this.model.setParameterValueById(parameterName, clampedValue);
        
        // Cache value
        this.parameters.set(parameterName, clampedValue);
    }
    
    /**
     * Animate to target parameters
     */
    async _animateToParameters(targetParams, duration) {
        const startTime = performance.now();
        const startParams = new Map();
        
        // Store starting values
        for (const paramName of Object.keys(targetParams)) {
            startParams.set(paramName, this.parameters.get(paramName) || 0.0);
        }
        
        return new Promise((resolve) => {
            const animate = () => {
                const elapsed = (performance.now() - startTime) / 1000;
                const progress = Math.min(elapsed / duration, 1.0);
                
                // Easing function
                const easedProgress = progress < 0.5 
                    ? 4 * progress * progress * progress
                    : 1 - Math.pow(-2 * progress + 2, 3) / 2;
                
                // Interpolate parameters
                for (const [paramName, targetValue] of Object.entries(targetParams)) {
                    const startValue = startParams.get(paramName);
                    const currentValue = startValue + (targetValue - startValue) * easedProgress;
                    this._setParameter(paramName, currentValue);
                }
                
                if (progress < 1.0) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            };
            
            animate();
        });
    }
    
    /**
     * Start main animation loop
     */
    _startAnimationLoop() {
        const render = () => {
            if (!this.model) {
                requestAnimationFrame(render);
                return;
            }
            
            // Clear canvas
            this.gl.clear(this.gl.COLOR_BUFFER_BIT);
            
            // Update model
            this.model.update();
            
            // Render model
            this.model.draw(this.gl);
            
            requestAnimationFrame(render);
        };
        
        render();
        console.log('🎬 Animation loop started');
    }
    
    /**
     * Start idle animations (breathing, blinking)
     */
    startIdleAnimations() {
        // Breathing animation
        const breathingAnimation = () => {
            if (!this.model) return;
            
            const time = performance.now() / 1000;
            const breathValue = Math.sin(time * Math.PI / 2) * 0.3 + 0.7;
            this._setParameter('ParamBreath', breathValue);
            
            setTimeout(breathingAnimation, 1000 / 30); // 30 FPS
        };
        
        // Blinking animation
        const blinkingAnimation = () => {
            if (!this.model) return;
            
            // Random blink interval (2-6 seconds)
            const nextBlink = Math.random() * 4000 + 2000;
            
            setTimeout(() => {
                // Quick blink
                this._setParameter('ParamEyeLOpen', 0.0);
                this._setParameter('ParamEyeROpen', 0.0);
                
                setTimeout(() => {
                    this._setParameter('ParamEyeLOpen', 1.0);
                    this._setParameter('ParamEyeROpen', 1.0);
                    blinkingAnimation(); // Schedule next blink
                }, 100);
            }, nextBlink);
        };
        
        breathingAnimation();
        blinkingAnimation();
        
        console.log('💫 Idle animations started');
    }
    
    /**
     * Clean up resources
     */
    dispose() {
        if (this.model) {
            this.model.release();
            this.model = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        // Cancel all animations
        for (const task of this.animationTasks.values()) {
            if (task.cancel) task.cancel();
        }
        this.animationTasks.clear();
        
        console.log('🧹 Live2D renderer disposed');
    }
}

/**
 * Factory function to create Live2D avatar renderer
 */
export function createLive2DAvatar(canvasId, liveKitRoom) {
    return new LiveKitLive2DAvatar(canvasId, liveKitRoom);
}

/**
 * Utility function to check Live2D support
 */
export function isLive2DSupported() {
    // Check for WebGL support
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    
    if (!gl) {
        return { supported: false, reason: 'WebGL not supported' };
    }
    
    // Check for required APIs
    if (!window.AudioContext && !window.webkitAudioContext) {
        return { supported: false, reason: 'Web Audio API not supported' };
    }
    
    return { supported: true };
}

export default LiveKitLive2DAvatar;
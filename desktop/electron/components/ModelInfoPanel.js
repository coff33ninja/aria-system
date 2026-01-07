/**
 * ModelInfoPanel Component
 * 
 * Displays comprehensive metadata about the loaded Live2D model including:
 * - Model name, version, author
 * - Parameter count and names
 * - Available animations
 * - Texture information
 * - Physics settings
 */

export class ModelInfoPanel {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.modelInfo = null;
        
        if (!this.container) {
            throw new Error(`Container element '${containerId}' not found`);
        }
        
        this.render();
    }
    
    /**
     * Update model information
     */
    updateModelInfo(modelInfo) {
        this.modelInfo = modelInfo;
        this.render();
    }
    
    /**
     * Get model information from Live2D model instance
     */
    extractModelInfo(live2dModel) {
        if (!live2dModel) {
            return null;
        }
        
        const info = {
            name: 'Unknown',
            version: 'Unknown',
            author: 'Unknown',
            parameters: [],
            animations: [],
            textures: [],
            physics: null
        };
        
        try {
            // Get model settings
            if (live2dModel.internalModel && live2dModel.internalModel.settings) {
                const settings = live2dModel.internalModel.settings;
                info.name = settings.name || live2dModel.internalModel.modelName || 'Unknown';
            }
            
            // Get parameters
            if (live2dModel.internalModel && live2dModel.internalModel.coreModel) {
                const coreModel = live2dModel.internalModel.coreModel;
                const paramCount = coreModel.getParameterCount();
                
                for (let i = 0; i < paramCount; i++) {
                    const paramId = coreModel.getParameterId(i);
                    const value = coreModel.getParameterValueByIndex(i);
                    const min = coreModel.getParameterMinimumValue(i);
                    const max = coreModel.getParameterMaximumValue(i);
                    const defaultValue = coreModel.getParameterDefaultValue(i);
                    
                    info.parameters.push({
                        id: paramId,
                        value: value,
                        min: min,
                        max: max,
                        default: defaultValue
                    });
                }
            }
            
            // Get animations
            if (live2dModel.internalModel && live2dModel.internalModel.settings) {
                const settings = live2dModel.internalModel.settings;
                const motions = settings.motions || {};
                
                for (const [group, motionList] of Object.entries(motions)) {
                    motionList.forEach((motion, index) => {
                        info.animations.push({
                            group: group,
                            index: index,
                            file: motion.File || motion.file || 'Unknown'
                        });
                    });
                }
            }
            
            // Get textures
            if (live2dModel.internalModel && live2dModel.internalModel.textures) {
                info.textures = live2dModel.internalModel.textures.map((tex, index) => ({
                    index: index,
                    width: tex.width || 0,
                    height: tex.height || 0
                }));
            }
            
            // Get physics info
            if (live2dModel.internalModel && live2dModel.internalModel.settings) {
                const settings = live2dModel.internalModel.settings;
                if (settings.physics) {
                    info.physics = {
                        file: settings.physics,
                        enabled: true
                    };
                }
            }
            
        } catch (error) {
            console.error('Failed to extract model info:', error);
        }
        
        return info;
    }
    
    /**
     * Render the panel
     */
    render() {
        if (!this.modelInfo) {
            this.container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #888;">
                    <p>No model loaded</p>
                </div>
            `;
            return;
        }
        
        const info = this.modelInfo;
        
        this.container.innerHTML = `
            <div class="model-info-panel">
                <div class="info-section">
                    <h3 class="info-section-title">Basic Information</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">Name:</span>
                            <span class="info-value">${this.escapeHtml(info.name)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Version:</span>
                            <span class="info-value">${this.escapeHtml(info.version)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Author:</span>
                            <span class="info-value">${this.escapeHtml(info.author)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="info-section">
                    <h3 class="info-section-title">Statistics</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">Parameters:</span>
                            <span class="info-value">${info.parameters.length}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Animations:</span>
                            <span class="info-value">${info.animations.length}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Textures:</span>
                            <span class="info-value">${info.textures.length}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Physics:</span>
                            <span class="info-value">${info.physics ? 'Enabled' : 'Disabled'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="info-section">
                    <h3 class="info-section-title">Parameters (${info.parameters.length})</h3>
                    <div class="info-list">
                        ${info.parameters.slice(0, 10).map(param => `
                            <div class="info-list-item">
                                <span class="param-id">${this.escapeHtml(param.id)}</span>
                                <span class="param-range">[${param.min.toFixed(1)} - ${param.max.toFixed(1)}]</span>
                            </div>
                        `).join('')}
                        ${info.parameters.length > 10 ? `
                            <div class="info-list-item" style="color: #888; font-style: italic;">
                                ... and ${info.parameters.length - 10} more
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="info-section">
                    <h3 class="info-section-title">Animations (${info.animations.length})</h3>
                    <div class="info-list">
                        ${info.animations.slice(0, 10).map(anim => `
                            <div class="info-list-item">
                                <span class="anim-name">${this.escapeHtml(anim.group)}</span>
                                <span class="anim-file">${this.escapeHtml(anim.file)}</span>
                            </div>
                        `).join('')}
                        ${info.animations.length > 10 ? `
                            <div class="info-list-item" style="color: #888; font-style: italic;">
                                ... and ${info.animations.length - 10} more
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="info-section">
                    <h3 class="info-section-title">Textures (${info.textures.length})</h3>
                    <div class="info-list">
                        ${info.textures.map(tex => `
                            <div class="info-list-item">
                                <span class="tex-index">Texture ${tex.index}</span>
                                <span class="tex-size">${tex.width}x${tex.height}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                ${info.physics ? `
                    <div class="info-section">
                        <h3 class="info-section-title">Physics</h3>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">File:</span>
                                <span class="info-value">${this.escapeHtml(info.physics.file)}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Status:</span>
                                <span class="info-value">Enabled</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Get current model info
     */
    getModelInfo() {
        return this.modelInfo;
    }
    
    /**
     * Clear model info
     */
    clear() {
        this.modelInfo = null;
        this.render();
    }
    
    /**
     * Clean up
     */
    dispose() {
        this.container.innerHTML = '';
        this.modelInfo = null;
    }
}

// Default styles (can be overridden)
export const MODEL_INFO_PANEL_STYLES = `
.model-info-panel {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #fff;
}

.info-section {
    margin-bottom: 20px;
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
}

.info-section-title {
    font-size: 13px;
    font-weight: 600;
    color: #ff6b9d;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 8px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
}

.info-label {
    color: #aaa;
    font-weight: 500;
}

.info-value {
    color: #fff;
    font-weight: 600;
}

.info-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 200px;
    overflow-y: auto;
}

.info-list-item {
    display: flex;
    justify-content: space-between;
    padding: 4px 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
    font-size: 11px;
}

.param-id, .anim-name, .tex-index {
    color: #fff;
    font-weight: 500;
}

.param-range, .anim-file, .tex-size {
    color: #aaa;
    font-family: monospace;
}
`;

export default ModelInfoPanel;

/**
 * ExpressionManager Component
 * 
 * Manages Live2D expressions with preview, blending, and custom creation
 * Supports expression listing, hover preview, blending controls, and saving custom expressions
 */

class ExpressionManager {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            showThumbnails: true,
            enableBlending: true,
            enableCustomExpressions: true,
            blendDuration: 500, // ms
            previewDelay: 200, // ms before preview on hover
            ...options
        };
        
        // Expression storage
        this.expressions = new Map();
        this.customExpressions = new Map();
        
        // Blending state
        this.currentExpression = null;
        this.blendingFrom = null;
        this.blendingTo = null;
        this.blendProgress = 0;
        this.blendAnimationId = null;
        
        // Preview state
        this.previewTimeout = null;
        this.previewExpression = null;
        this.previousExpression = null;
        
        // Event listeners
        this.listeners = new Map();
        
        this._initializeUI();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="expression-manager">
                <div class="expression-header">
                    <h3>Expressions</h3>
                    <div class="expression-actions">
                        ${this.options.enableCustomExpressions ? `
                            <button class="expr-save-btn" title="Save current parameters as expression">
                                💾 Save
                            </button>
                        ` : ''}
                        <button class="expr-clear-btn" title="Clear expression">
                            ✖️ Clear
                        </button>
                    </div>
                </div>
                
                ${this.options.enableBlending ? `
                    <div class="expression-blending">
                        <label>Blend Intensity:</label>
                        <input type="range" class="blend-slider" min="0" max="100" value="100">
                        <span class="blend-value">100%</span>
                    </div>
                ` : ''}
                
                <div class="expression-list"></div>
                
                ${this.options.enableCustomExpressions ? `
                    <div class="custom-expressions">
                        <h4>Custom Expressions</h4>
                        <div class="custom-expression-list"></div>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.listContainer = this.container.querySelector('.expression-list');
        this.customListContainer = this.container.querySelector('.custom-expression-list');
        
        this._setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Save button
        const saveBtn = this.container.querySelector('.expr-save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this._showSaveDialog();
            });
        }
        
        // Clear button
        const clearBtn = this.container.querySelector('.expr-clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearExpression();
            });
        }
        
        // Blend slider
        const blendSlider = this.container.querySelector('.blend-slider');
        const blendValue = this.container.querySelector('.blend-value');
        
        if (blendSlider && blendValue) {
            blendSlider.addEventListener('input', (e) => {
                const intensity = parseFloat(e.target.value) / 100;
                blendValue.textContent = `${e.target.value}%`;
                this._emitEvent('blendIntensityChanged', { intensity });
            });
        }
    }
    
    /**
     * Add expression
     */
    addExpression(name, parameters, metadata = {}) {
        // Validate parameters
        if (!parameters || typeof parameters !== 'object') {
            console.error(`Invalid parameters for expression '${name}'`);
            this._emitEvent('error', {
                message: `Invalid parameters for expression '${name}'`,
                expression: name
            });
            return;
        }
        
        const expr = {
            name,
            parameters: { ...parameters },
            thumbnail: metadata.thumbnail || null,
            description: metadata.description || '',
            group: metadata.group || 'default',
            isCustom: false
        };
        
        this.expressions.set(name, expr);
        this._addExpressionToUI(expr);
    }
    
    /**
     * Add custom expression
     */
    addCustomExpression(name, parameters, metadata = {}) {
        // Validate parameters
        if (!parameters || typeof parameters !== 'object') {
            console.error(`Invalid parameters for custom expression '${name}'`);
            this._emitEvent('error', {
                message: `Invalid parameters for custom expression '${name}'`,
                expression: name
            });
            return;
        }
        
        // Validate name
        if (!name || name.trim() === '') {
            console.error('Custom expression name cannot be empty');
            this._emitEvent('error', {
                message: 'Expression name cannot be empty'
            });
            return;
        }
        
        const expr = {
            name,
            parameters: { ...parameters },
            thumbnail: metadata.thumbnail || null,
            description: metadata.description || '',
            group: 'custom',
            isCustom: true
        };
        
        this.customExpressions.set(name, expr);
        
        if (this.customListContainer) {
            this._addExpressionToUI(expr, this.customListContainer);
        }
        
        this._emitEvent('customExpressionAdded', { name, expression: expr });
    }
    
    /**
     * Remove expression
     */
    removeExpression(name) {
        const expr = this.expressions.get(name) || this.customExpressions.get(name);
        if (!expr) return;
        
        if (expr.isCustom) {
            this.customExpressions.delete(name);
        } else {
            this.expressions.delete(name);
        }
        
        const element = this.container.querySelector(`[data-expr-name="${name}"]`);
        if (element) {
            element.remove();
        }
        
        if (this.currentExpression === name) {
            this.clearExpression();
        }
    }
    
    /**
     * Clear all expressions
     */
    clear() {
        this.expressions.clear();
        this.customExpressions.clear();
        this.listContainer.innerHTML = '';
        if (this.customListContainer) {
            this.customListContainer.innerHTML = '';
        }
        this.clearExpression();
    }
    
    /**
     * Apply expression
     */
    applyExpression(name, blend = true) {
        const expr = this.expressions.get(name) || this.customExpressions.get(name);
        if (!expr) {
            const errorMsg = `Expression '${name}' not found`;
            console.warn(errorMsg);
            this._emitEvent('error', {
                message: errorMsg,
                expression: name
            });
            return;
        }
        
        // Validate expression parameters
        if (!expr.parameters || typeof expr.parameters !== 'object') {
            const errorMsg = `Expression '${name}' has invalid parameters`;
            console.error(errorMsg);
            this._emitEvent('error', {
                message: errorMsg,
                expression: name
            });
            return;
        }
        
        if (blend && this.options.enableBlending && this.currentExpression) {
            this._startBlending(this.currentExpression, name);
        } else {
            this.currentExpression = name;
            this._emitEvent('expressionApplied', { 
                name, 
                parameters: expr.parameters 
            });
        }
        
        this._updateUI();
    }
    
    /**
     * Clear current expression
     */
    clearExpression() {
        this.currentExpression = null;
        this.blendingFrom = null;
        this.blendingTo = null;
        this._stopBlending();
        this._updateUI();
        this._emitEvent('expressionCleared', {});
    }
    
    /**
     * Preview expression on hover
     */
    previewExpression(name) {
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
        }
        
        this.previewTimeout = setTimeout(() => {
            const expr = this.expressions.get(name) || this.customExpressions.get(name);
            if (!expr) return;
            
            this.previousExpression = this.currentExpression;
            this.previewExpression = name;
            
            this._emitEvent('expressionPreviewed', { 
                name, 
                parameters: expr.parameters 
            });
        }, this.options.previewDelay);
    }
    
    /**
     * Cancel preview
     */
    cancelPreview() {
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
            this.previewTimeout = null;
        }
        
        if (this.previewExpression) {
            this.previewExpression = null;
            
            if (this.previousExpression) {
                const expr = this.expressions.get(this.previousExpression) || 
                             this.customExpressions.get(this.previousExpression);
                if (expr) {
                    this._emitEvent('expressionApplied', { 
                        name: this.previousExpression, 
                        parameters: expr.parameters 
                    });
                }
            } else {
                this._emitEvent('expressionCleared', {});
            }
            
            this.previousExpression = null;
        }
    }
    
    /**
     * Start blending between expressions
     */
    _startBlending(fromName, toName) {
        const fromExpr = this.expressions.get(fromName) || this.customExpressions.get(fromName);
        const toExpr = this.expressions.get(toName) || this.customExpressions.get(toName);
        
        if (!fromExpr || !toExpr) return;
        
        this.blendingFrom = fromName;
        this.blendingTo = toName;
        this.blendProgress = 0;
        
        const startTime = performance.now();
        const duration = this.options.blendDuration;
        
        const animate = () => {
            const elapsed = performance.now() - startTime;
            this.blendProgress = Math.min(elapsed / duration, 1.0);
            
            // Interpolate parameters
            const blendedParams = this._interpolateParameters(
                fromExpr.parameters,
                toExpr.parameters,
                this.blendProgress
            );
            
            this._emitEvent('expressionBlending', {
                from: fromName,
                to: toName,
                progress: this.blendProgress,
                parameters: blendedParams
            });
            
            if (this.blendProgress < 1.0) {
                this.blendAnimationId = requestAnimationFrame(animate);
            } else {
                this.currentExpression = toName;
                this.blendingFrom = null;
                this.blendingTo = null;
                this._stopBlending();
                
                this._emitEvent('expressionApplied', { 
                    name: toName, 
                    parameters: toExpr.parameters 
                });
            }
        };
        
        this.blendAnimationId = requestAnimationFrame(animate);
    }
    
    /**
     * Stop blending animation
     */
    _stopBlending() {
        if (this.blendAnimationId) {
            cancelAnimationFrame(this.blendAnimationId);
            this.blendAnimationId = null;
        }
    }
    
    /**
     * Interpolate between two parameter sets
     */
    _interpolateParameters(fromParams, toParams, progress) {
        const result = {};
        
        // Get all unique parameter names
        const allParams = new Set([
            ...Object.keys(fromParams),
            ...Object.keys(toParams)
        ]);
        
        allParams.forEach(param => {
            const fromValue = fromParams[param] !== undefined ? fromParams[param] : 0;
            const toValue = toParams[param] !== undefined ? toParams[param] : 0;
            
            // Linear interpolation
            result[param] = fromValue + (toValue - fromValue) * progress;
        });
        
        return result;
    }
    
    /**
     * Add expression to UI
     */
    _addExpressionToUI(expr, targetContainer = null) {
        const container = targetContainer || this.listContainer;
        
        const item = document.createElement('div');
        item.className = 'expression-item';
        item.dataset.exprName = expr.name;
        item.dataset.exprGroup = expr.group;
        
        item.innerHTML = `
            ${this.options.showThumbnails && expr.thumbnail ? `
                <div class="expression-thumbnail">
                    <img src="${expr.thumbnail}" alt="${expr.name}">
                </div>
            ` : ''}
            <div class="expression-info">
                <span class="expression-name">${expr.name}</span>
                ${expr.description ? `
                    <span class="expression-description">${expr.description}</span>
                ` : ''}
            </div>
            ${expr.isCustom ? `
                <button class="expression-delete-btn" title="Delete custom expression">
                    🗑️
                </button>
            ` : ''}
        `;
        
        // Click to apply
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('expression-delete-btn')) {
                this.applyExpression(expr.name);
            }
        });
        
        // Hover to preview
        item.addEventListener('mouseenter', () => {
            this.previewExpression(expr.name);
        });
        
        item.addEventListener('mouseleave', () => {
            this.cancelPreview();
        });
        
        // Delete custom expression
        if (expr.isCustom) {
            const deleteBtn = item.querySelector('.expression-delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeExpression(expr.name);
            });
        }
        
        container.appendChild(item);
    }
    
    /**
     * Show save dialog for custom expression
     */
    _showSaveDialog() {
        const name = prompt('Enter a name for this expression:');
        if (!name || name.trim() === '') return;
        
        // Request current parameters from parent
        this._emitEvent('requestCurrentParameters', { 
            callback: (parameters) => {
                this.addCustomExpression(name.trim(), parameters, {
                    description: 'Custom expression'
                });
            }
        });
    }
    
    /**
     * Update UI state
     */
    _updateUI() {
        // Highlight current expression
        this.container.querySelectorAll('.expression-item').forEach(item => {
            const isActive = item.dataset.exprName === this.currentExpression;
            item.classList.toggle('active', isActive);
        });
        
        // Update blending indicator
        if (this.blendingFrom && this.blendingTo) {
            const fromItem = this.container.querySelector(`[data-expr-name="${this.blendingFrom}"]`);
            const toItem = this.container.querySelector(`[data-expr-name="${this.blendingTo}"]`);
            
            if (fromItem) fromItem.classList.add('blending-from');
            if (toItem) toItem.classList.add('blending-to');
        } else {
            this.container.querySelectorAll('.blending-from, .blending-to').forEach(item => {
                item.classList.remove('blending-from', 'blending-to');
            });
        }
    }
    
    /**
     * Get current state
     */
    getState() {
        return {
            currentExpression: this.currentExpression,
            expressionCount: this.expressions.size,
            customExpressionCount: this.customExpressions.size,
            isBlending: this.blendAnimationId !== null,
            blendProgress: this.blendProgress
        };
    }
    
    /**
     * Export expressions as JSON
     */
    exportJSON() {
        const data = {
            expressions: {},
            customExpressions: {}
        };
        
        this.expressions.forEach((expr, name) => {
            data.expressions[name] = {
                parameters: expr.parameters,
                description: expr.description,
                group: expr.group
            };
        });
        
        this.customExpressions.forEach((expr, name) => {
            data.customExpressions[name] = {
                parameters: expr.parameters,
                description: expr.description
            };
        });
        
        return JSON.stringify(data, null, 2);
    }
    
    /**
     * Import expressions from JSON
     */
    importJSON(json) {
        try {
            const data = typeof json === 'string' ? JSON.parse(json) : json;
            
            // Validate data structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid import data: must be an object');
            }
            
            let importedCount = 0;
            
            if (data.expressions && typeof data.expressions === 'object') {
                Object.entries(data.expressions).forEach(([name, expr]) => {
                    if (expr.parameters && typeof expr.parameters === 'object') {
                        this.addExpression(name, expr.parameters, {
                            description: expr.description,
                            group: expr.group
                        });
                        importedCount++;
                    } else {
                        console.warn(`Skipping expression '${name}': invalid parameters`);
                    }
                });
            }
            
            if (data.customExpressions && typeof data.customExpressions === 'object') {
                Object.entries(data.customExpressions).forEach(([name, expr]) => {
                    if (expr.parameters && typeof expr.parameters === 'object') {
                        this.addCustomExpression(name, expr.parameters, {
                            description: expr.description
                        });
                        importedCount++;
                    } else {
                        console.warn(`Skipping custom expression '${name}': invalid parameters`);
                    }
                });
            }
            
            if (importedCount === 0) {
                console.warn('No valid expressions found in import data');
            }
            
            return true;
        } catch (error) {
            console.error('Failed to import expressions:', error);
            this._emitEvent('error', {
                message: `Failed to import expressions: ${error.message}`
            });
            return false;
        }
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
        this._stopBlending();
        
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
        }
        
        this.listeners.clear();
        this.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExpressionManager;
}

// Default styles
const EXPRESSION_MANAGER_STYLES = `
.expression-manager {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #fff;
}

.expression-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.expression-header h3 {
    font-size: 13px;
    font-weight: 600;
    color: #ff6b9d;
    margin: 0;
}

.expression-actions {
    display: flex;
    gap: 8px;
}

.expr-save-btn,
.expr-clear-btn {
    padding: 4px 8px;
    font-size: 11px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s;
}

.expr-save-btn:hover,
.expr-clear-btn:hover {
    background: rgba(255,255,255,0.2);
}

.expression-blending {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
}

.expression-blending label {
    font-size: 11px;
    color: #aaa;
}

.blend-slider {
    flex: 1;
    height: 4px;
}

.blend-value {
    font-size: 11px;
    color: #fff;
    font-weight: 600;
    min-width: 40px;
    text-align: right;
}

.expression-list,
.custom-expression-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 300px;
    overflow-y: auto;
}

.expression-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.expression-item:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.2);
}

.expression-item.active {
    background: rgba(255,107,157,0.2);
    border-color: #ff6b9d;
}

.expression-item.blending-from {
    border-color: #ffa500;
    animation: pulse-from 1s infinite;
}

.expression-item.blending-to {
    border-color: #00ff00;
    animation: pulse-to 1s infinite;
}

@keyframes pulse-from {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

@keyframes pulse-to {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

.expression-thumbnail {
    width: 40px;
    height: 40px;
    border-radius: 4px;
    overflow: hidden;
    flex-shrink: 0;
}

.expression-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.expression-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.expression-name {
    font-size: 12px;
    font-weight: 600;
    color: #fff;
}

.expression-description {
    font-size: 10px;
    color: #aaa;
}

.expression-delete-btn {
    padding: 4px 8px;
    font-size: 14px;
    background: rgba(255,0,0,0.2);
    border: 1px solid rgba(255,0,0,0.3);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.expression-delete-btn:hover {
    background: rgba(255,0,0,0.4);
}

.custom-expressions {
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

.custom-expressions h4 {
    font-size: 12px;
    font-weight: 600;
    color: #ff6b9d;
    margin: 0 0 12px 0;
}
`;

// Export styles
if (typeof module !== 'undefined' && module.exports) {
    module.exports.EXPRESSION_MANAGER_STYLES = EXPRESSION_MANAGER_STYLES;
}

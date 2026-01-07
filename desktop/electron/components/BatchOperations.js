/**
 * BatchOperations Component
 * 
 * Provides batch operations for Live2D model parameters
 * Supports applying presets, resetting parameters, and randomization
 */

class BatchOperations {
    constructor(container, parameterPanel, options = {}) {
        this.container = container;
        this.parameterPanel = parameterPanel;
        this.options = {
            enableRandomization: true,
            enablePresets: true,
            randomizationRange: { min: -1.0, max: 1.0 },
            ...options
        };
        
        // Presets storage
        this.presets = new Map();
        
        // Selection state
        this.selectedParameters = new Set();
        
        // Event listeners
        this.listeners = new Map();
        
        this._initializeUI();
        this._loadDefaultPresets();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="batch-operations">
                <div class="batch-header">
                    <h3>Batch Operations</h3>
                    <button class="batch-select-all-btn">Select All</button>
                    <button class="batch-deselect-all-btn">Deselect All</button>
                </div>
                
                <div class="batch-selection-info">
                    <span class="selection-count">0 parameters selected</span>
                </div>
                
                <div class="batch-actions">
                    <div class="batch-action-group">
                        <h4>Reset</h4>
                        <button class="batch-reset-btn" title="Reset selected parameters to default">
                            🔄 Reset Selected
                        </button>
                        <button class="batch-reset-all-btn" title="Reset all parameters to default">
                            🔄 Reset All
                        </button>
                    </div>
                    
                    ${this.options.enableRandomization ? `
                        <div class="batch-action-group">
                            <h4>Randomize</h4>
                            <div class="randomize-controls">
                                <label>
                                    Min: <input type="number" class="random-min" 
                                        value="${this.options.randomizationRange.min}" 
                                        step="0.1" min="-1" max="1">
                                </label>
                                <label>
                                    Max: <input type="number" class="random-max" 
                                        value="${this.options.randomizationRange.max}" 
                                        step="0.1" min="-1" max="1">
                                </label>
                            </div>
                            <button class="batch-randomize-btn" title="Randomize selected parameters">
                                🎲 Randomize Selected
                            </button>
                            <button class="batch-randomize-all-btn" title="Randomize all parameters">
                                🎲 Randomize All
                            </button>
                        </div>
                    ` : ''}
                    
                    ${this.options.enablePresets ? `
                        <div class="batch-action-group">
                            <h4>Presets</h4>
                            <select class="preset-selector">
                                <option value="">Select preset...</option>
                            </select>
                            <button class="preset-apply-btn" title="Apply preset to selected parameters">
                                ✓ Apply to Selected
                            </button>
                            <button class="preset-apply-all-btn" title="Apply preset to all parameters">
                                ✓ Apply to All
                            </button>
                            <div class="preset-management">
                                <button class="preset-save-btn" title="Save current values as preset">
                                    💾 Save Preset
                                </button>
                                <button class="preset-delete-btn" title="Delete selected preset">
                                    🗑️ Delete Preset
                                </button>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="batch-action-group">
                        <h4>Copy/Paste</h4>
                        <button class="batch-copy-btn" title="Copy selected parameter values">
                            📋 Copy Selected
                        </button>
                        <button class="batch-paste-btn" title="Paste parameter values">
                            📄 Paste
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.selectionCount = this.container.querySelector('.selection-count');
        this.presetSelector = this.container.querySelector('.preset-selector');
        
        this._setupEventListeners();
        this._setupParameterSelection();
    }
    
    /**
     * Setup event listeners
     */
    _setupEventListeners() {
        // Selection controls
        const selectAllBtn = this.container.querySelector('.batch-select-all-btn');
        const deselectAllBtn = this.container.querySelector('.batch-deselect-all-btn');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAll());
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }
        
        // Reset operations
        const resetBtn = this.container.querySelector('.batch-reset-btn');
        const resetAllBtn = this.container.querySelector('.batch-reset-all-btn');
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetSelected());
        }
        
        if (resetAllBtn) {
            resetAllBtn.addEventListener('click', () => this.resetAll());
        }
        
        // Randomization
        const randomizeBtn = this.container.querySelector('.batch-randomize-btn');
        const randomizeAllBtn = this.container.querySelector('.batch-randomize-all-btn');
        
        if (randomizeBtn) {
            randomizeBtn.addEventListener('click', () => this.randomizeSelected());
        }
        
        if (randomizeAllBtn) {
            randomizeAllBtn.addEventListener('click', () => this.randomizeAll());
        }
        
        // Preset operations
        const applyBtn = this.container.querySelector('.preset-apply-btn');
        const applyAllBtn = this.container.querySelector('.preset-apply-all-btn');
        const saveBtn = this.container.querySelector('.preset-save-btn');
        const deleteBtn = this.container.querySelector('.preset-delete-btn');
        
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyPresetToSelected());
        }
        
        if (applyAllBtn) {
            applyAllBtn.addEventListener('click', () => this.applyPresetToAll());
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePreset());
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deletePreset());
        }
        
        // Copy/Paste
        const copyBtn = this.container.querySelector('.batch-copy-btn');
        const pasteBtn = this.container.querySelector('.batch-paste-btn');
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copySelected());
        }
        
        if (pasteBtn) {
            pasteBtn.addEventListener('click', () => this.paste());
        }
    }
    
    /**
     * Setup parameter selection in ParameterPanel
     */
    _setupParameterSelection() {
        if (!this.parameterPanel || !this.parameterPanel.listContainer) return;
        
        // Add checkboxes to parameter items
        const observer = new MutationObserver(() => {
            this._addCheckboxesToParameters();
        });
        
        observer.observe(this.parameterPanel.listContainer, {
            childList: true,
            subtree: true
        });
        
        this._addCheckboxesToParameters();
    }
    
    /**
     * Add checkboxes to parameter items
     */
    _addCheckboxesToParameters() {
        if (!this.parameterPanel || !this.parameterPanel.listContainer) return;
        
        const items = this.parameterPanel.listContainer.querySelectorAll('.parameter-item');
        
        items.forEach(item => {
            if (item.querySelector('.param-checkbox')) return; // Already has checkbox
            
            const paramName = item.dataset.paramName;
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'param-checkbox';
            checkbox.checked = this.selectedParameters.has(paramName);
            
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedParameters.add(paramName);
                } else {
                    this.selectedParameters.delete(paramName);
                }
                this._updateSelectionCount();
            });
            
            const info = item.querySelector('.parameter-info');
            if (info) {
                info.insertBefore(checkbox, info.firstChild);
            }
        });
    }
    
    /**
     * Update selection count display
     */
    _updateSelectionCount() {
        if (this.selectionCount) {
            this.selectionCount.textContent = `${this.selectedParameters.size} parameters selected`;
        }
    }
    
    /**
     * Select all parameters
     */
    selectAll() {
        if (!this.parameterPanel) return;
        
        this.selectedParameters.clear();
        this.parameterPanel.parameters.forEach((param, name) => {
            this.selectedParameters.add(name);
        });
        
        // Update checkboxes
        const checkboxes = this.parameterPanel.listContainer.querySelectorAll('.param-checkbox');
        checkboxes.forEach(cb => cb.checked = true);
        
        this._updateSelectionCount();
        this._emitEvent('selectionChanged', { selected: Array.from(this.selectedParameters) });
    }
    
    /**
     * Deselect all parameters
     */
    deselectAll() {
        this.selectedParameters.clear();
        
        // Update checkboxes
        if (this.parameterPanel && this.parameterPanel.listContainer) {
            const checkboxes = this.parameterPanel.listContainer.querySelectorAll('.param-checkbox');
            checkboxes.forEach(cb => cb.checked = false);
        }
        
        this._updateSelectionCount();
        this._emitEvent('selectionChanged', { selected: [] });
    }
    
    /**
     * Reset selected parameters
     */
    resetSelected() {
        if (!this.parameterPanel) return;
        
        this.selectedParameters.forEach(paramName => {
            this.parameterPanel.resetParameter(paramName);
        });
        
        this._emitEvent('resetSelected', { parameters: Array.from(this.selectedParameters) });
    }
    
    /**
     * Reset all parameters
     */
    resetAll() {
        if (!this.parameterPanel) return;
        
        this.parameterPanel.resetAll();
        this._emitEvent('resetAll', {});
    }
    
    /**
     * Randomize selected parameters
     */
    randomizeSelected() {
        if (!this.parameterPanel) return;
        
        const minInput = this.container.querySelector('.random-min');
        const maxInput = this.container.querySelector('.random-max');
        
        const min = minInput ? parseFloat(minInput.value) : this.options.randomizationRange.min;
        const max = maxInput ? parseFloat(maxInput.value) : this.options.randomizationRange.max;
        
        this.selectedParameters.forEach(paramName => {
            const randomValue = min + Math.random() * (max - min);
            this.parameterPanel.updateParameter(paramName, randomValue);
        });
        
        this._emitEvent('randomizeSelected', { 
            parameters: Array.from(this.selectedParameters),
            range: { min, max }
        });
    }
    
    /**
     * Randomize all parameters
     */
    randomizeAll() {
        if (!this.parameterPanel) return;
        
        const minInput = this.container.querySelector('.random-min');
        const maxInput = this.container.querySelector('.random-max');
        
        const min = minInput ? parseFloat(minInput.value) : this.options.randomizationRange.min;
        const max = maxInput ? parseFloat(maxInput.value) : this.options.randomizationRange.max;
        
        this.parameterPanel.parameters.forEach((_, name) => {
            const param = this.parameterPanel.parameters.get(name);
            if (param && !param.readonly) {
                const randomValue = min + Math.random() * (max - min);
                this.parameterPanel.updateParameter(name, randomValue);
            }
        });
        
        this._emitEvent('randomizeAll', { range: { min, max } });
    }
    
    /**
     * Apply preset to selected parameters
     */
    applyPresetToSelected() {
        if (!this.presetSelector || !this.parameterPanel) return;
        
        const presetName = this.presetSelector.value;
        if (!presetName) return;
        
        const preset = this.presets.get(presetName);
        if (!preset) return;
        
        this.selectedParameters.forEach(paramName => {
            if (preset.parameters[paramName] !== undefined) {
                this.parameterPanel.updateParameter(paramName, preset.parameters[paramName]);
            }
        });
        
        this._emitEvent('presetApplied', { 
            preset: presetName,
            parameters: Array.from(this.selectedParameters)
        });
    }
    
    /**
     * Apply preset to all parameters
     */
    applyPresetToAll() {
        if (!this.presetSelector || !this.parameterPanel) return;
        
        const presetName = this.presetSelector.value;
        if (!presetName) return;
        
        const preset = this.presets.get(presetName);
        if (!preset) return;
        
        Object.entries(preset.parameters).forEach(([name, value]) => {
            this.parameterPanel.updateParameter(name, value);
        });
        
        this._emitEvent('presetApplied', { preset: presetName, parameters: 'all' });
    }
    
    /**
     * Save current parameters as preset
     */
    savePreset() {
        if (!this.parameterPanel) return;
        
        const name = prompt('Enter preset name:');
        if (!name || name.trim() === '') return;
        
        const parameters = this.parameterPanel.getAllParameters();
        
        this.presets.set(name.trim(), {
            name: name.trim(),
            parameters,
            timestamp: Date.now()
        });
        
        this._updatePresetSelector();
        this._emitEvent('presetSaved', { name: name.trim() });
    }
    
    /**
     * Delete selected preset
     */
    deletePreset() {
        if (!this.presetSelector) return;
        
        const presetName = this.presetSelector.value;
        if (!presetName) return;
        
        if (confirm(`Delete preset "${presetName}"?`)) {
            this.presets.delete(presetName);
            this._updatePresetSelector();
            this._emitEvent('presetDeleted', { name: presetName });
        }
    }
    
    /**
     * Copy selected parameter values
     */
    copySelected() {
        if (!this.parameterPanel) return;
        
        const values = {};
        this.selectedParameters.forEach(paramName => {
            values[paramName] = this.parameterPanel.getParameter(paramName);
        });
        
        // Store in clipboard
        this.clipboard = values;
        
        // Try to use system clipboard if available
        if (navigator.clipboard) {
            navigator.clipboard.writeText(JSON.stringify(values, null, 2))
                .catch(err => console.warn('Failed to copy to clipboard:', err));
        }
        
        this._emitEvent('copied', { parameters: values });
    }
    
    /**
     * Paste parameter values
     */
    paste() {
        if (!this.parameterPanel) return;
        
        if (this.clipboard) {
            Object.entries(this.clipboard).forEach(([name, value]) => {
                this.parameterPanel.updateParameter(name, value);
            });
            
            this._emitEvent('pasted', { parameters: this.clipboard });
        }
    }
    
    /**
     * Load default presets
     */
    _loadDefaultPresets() {
        // Add some default presets
        this.presets.set('Neutral', {
            name: 'Neutral',
            parameters: {},
            timestamp: Date.now()
        });
        
        this._updatePresetSelector();
    }
    
    /**
     * Update preset selector
     */
    _updatePresetSelector() {
        if (!this.presetSelector) return;
        
        this.presetSelector.innerHTML = '<option value="">Select preset...</option>';
        
        this.presets.forEach((preset, name) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            this.presetSelector.appendChild(option);
        });
    }
    
    /**
     * Export presets as JSON
     */
    exportPresets() {
        const data = {};
        this.presets.forEach((preset, name) => {
            data[name] = preset;
        });
        return JSON.stringify(data, null, 2);
    }
    
    /**
     * Import presets from JSON
     */
    importPresets(json) {
        try {
            const data = typeof json === 'string' ? JSON.parse(json) : json;
            
            Object.entries(data).forEach(([name, preset]) => {
                this.presets.set(name, preset);
            });
            
            this._updatePresetSelector();
            return true;
        } catch (error) {
            console.error('Failed to import presets:', error);
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
            selectedCount: this.selectedParameters.size,
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
        this.selectedParameters.clear();
        this.presets.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BatchOperations;
}

// Default styles
const BATCH_OPERATIONS_STYLES = `
.batch-operations {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #fff;
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
    padding: 12px;
}

.batch-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.batch-header h3 {
    flex: 1;
    font-size: 13px;
    font-weight: 600;
    color: #ff6b9d;
    margin: 0;
}

.batch-select-all-btn,
.batch-deselect-all-btn {
    padding: 4px 8px;
    font-size: 10px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s;
}

.batch-select-all-btn:hover,
.batch-deselect-all-btn:hover {
    background: rgba(255,255,255,0.2);
}

.batch-selection-info {
    margin-bottom: 12px;
    padding: 6px 8px;
    background: rgba(0,0,0,0.3);
    border-radius: 4px;
    text-align: center;
}

.selection-count {
    font-size: 11px;
    color: #aaa;
    font-weight: 500;
}

.batch-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.batch-action-group {
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border-radius: 6px;
}

.batch-action-group h4 {
    font-size: 11px;
    font-weight: 600;
    color: #ff6b9d;
    margin: 0 0 8px 0;
    text-transform: uppercase;
}

.batch-action-group button {
    width: 100%;
    padding: 6px 12px;
    margin-bottom: 6px;
    font-size: 11px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s;
}

.batch-action-group button:hover {
    background: rgba(255,255,255,0.2);
}

.batch-action-group button:last-child {
    margin-bottom: 0;
}

.randomize-controls {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}

.randomize-controls label {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 10px;
    color: #aaa;
}

.randomize-controls input {
    padding: 4px;
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 3px;
    color: #fff;
    font-size: 11px;
}

.preset-selector {
    width: 100%;
    padding: 6px;
    margin-bottom: 8px;
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #fff;
    font-size: 11px;
}

.preset-management {
    display: flex;
    gap: 6px;
    margin-top: 8px;
}

.preset-management button {
    flex: 1;
    margin-bottom: 0;
}

.param-checkbox {
    margin-right: 8px;
    cursor: pointer;
}
`;

// Export styles
if (typeof module !== 'undefined' && module.exports) {
    module.exports.BATCH_OPERATIONS_STYLES = BATCH_OPERATIONS_STYLES;
}

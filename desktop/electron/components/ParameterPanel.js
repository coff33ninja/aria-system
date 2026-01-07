/**
 * ParameterPanel Component
 * 
 * Displays and controls Live2D model parameters
 * Supports real-time adjustment, search/filter, and grouping
 */

class ParameterPanel {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            minValue: -1.0,
            maxValue: 1.0,
            step: 0.01,
            updateDelay: 16, // ms delay for updates (16ms = ~60fps max)
            showGroups: true,
            defaultGroup: 'Other',
            ...options
        };
        
        // Parameters storage
        this.parameters = new Map();
        this.groups = new Map();
        
        // Event listeners
        this.listeners = new Map();
        
        // Debounced update functions per parameter
        this.debouncedUpdates = new Map();
        
        // Search state
        this.searchQuery = '';
        
        this._initializeUI();
    }
    
    /**
     * Initialize UI structure
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="parameter-panel">
                <div class="parameter-header">
                    <input type="text" class="parameter-search" placeholder="Search parameters...">
                    <button class="parameter-reset-btn">Reset All</button>
                </div>
                <div class="parameter-list"></div>
                <div class="parameter-empty-state" style="display: none;">
                    <div class="empty-icon">📊</div>
                    <div class="empty-message">No parameters available</div>
                    <div class="empty-hint">Load a model to see parameters</div>
                </div>
            </div>
        `;
        
        this.searchInput = this.container.querySelector('.parameter-search');
        this.resetBtn = this.container.querySelector('.parameter-reset-btn');
        this.listContainer = this.container.querySelector('.parameter-list');
        this.emptyState = this.container.querySelector('.parameter-empty-state');
        
        // Event listeners
        this.searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this._filterParameters();
        });
        
        this.resetBtn.addEventListener('click', () => {
            this.resetAll();
        });
        
        this._updateEmptyState();
    }
    
    /**
     * Add or update a parameter
     */
    setParameter(name, value, metadata = {}) {
        // Validate parameter name
        if (!name || typeof name !== 'string') {
            console.warn('Invalid parameter name:', name);
            return;
        }
        
        // Validate value
        if (typeof value !== 'number' || isNaN(value)) {
            console.warn(`Invalid parameter value for ${name}:`, value);
            value = 0.0;
        }
        
        const param = {
            name,
            value: this._clampValue(value),
            group: metadata.group || this._inferGroup(name),
            min: metadata.min !== undefined ? metadata.min : this.options.minValue,
            max: metadata.max !== undefined ? metadata.max : this.options.maxValue,
            defaultValue: metadata.defaultValue !== undefined ? metadata.defaultValue : 0.0,
            description: metadata.description || '',
            readonly: metadata.readonly || false
        };
        
        const isNew = !this.parameters.has(name);
        this.parameters.set(name, param);
        
        if (isNew) {
            this._addParameterToUI(param);
            this._updateGroups();
            this._updateEmptyState();
        } else {
            this._updateParameterUI(param);
        }
    }
    
    /**
     * Get parameter value
     */
    getParameter(name) {
        const param = this.parameters.get(name);
        return param ? param.value : null;
    }
    
    /**
     * Get all parameters
     */
    getAllParameters() {
        const result = {};
        this.parameters.forEach((param, name) => {
            result[name] = param.value;
        });
        return result;
    }
    
    /**
     * Update parameter value
     */
    updateParameter(name, value) {
        const param = this.parameters.get(name);
        if (!param || param.readonly) return;
        
        param.value = this._clampValue(value);
        this._updateParameterUI(param);
        this._emitChange(name, param.value);
    }
    
    /**
     * Reset parameter to default
     */
    resetParameter(name) {
        const param = this.parameters.get(name);
        if (!param) return;
        
        this.updateParameter(name, param.defaultValue);
    }
    
    /**
     * Reset all parameters to defaults
     */
    resetAll() {
        this.parameters.forEach((param, name) => {
            if (!param.readonly) {
                this.updateParameter(name, param.defaultValue);
            }
        });
    }
    
    /**
     * Remove parameter
     */
    removeParameter(name) {
        const param = this.parameters.get(name);
        if (!param) return;
        
        this.parameters.delete(name);
        
        const element = this.listContainer.querySelector(`[data-param-name="${name}"]`);
        if (element) {
            element.remove();
        }
        
        this._updateGroups();
    }
    
    /**
     * Clear all parameters
     */
    clear() {
        this.parameters.clear();
        this.groups.clear();
        this.listContainer.innerHTML = '';
        this._updateEmptyState();
    }
    
    /**
     * Update empty state visibility
     */
    _updateEmptyState() {
        if (this.emptyState) {
            this.emptyState.style.display = this.parameters.size === 0 ? 'flex' : 'none';
        }
    }
    
    /**
     * Add parameter to UI
     */
    _addParameterToUI(param) {
        const item = document.createElement('div');
        item.className = 'parameter-item';
        item.dataset.paramName = param.name;
        item.dataset.paramGroup = param.group;
        
        item.innerHTML = `
            <div class="parameter-info">
                <span class="parameter-name" title="${param.description || param.name}">${param.name}</span>
                <span class="parameter-value">${param.value.toFixed(2)}</span>
            </div>
            <div class="parameter-control">
                <input type="range" 
                    class="parameter-slider" 
                    min="${param.min * 100}" 
                    max="${param.max * 100}" 
                    value="${param.value * 100}"
                    step="${this.options.step * 100}"
                    ${param.readonly ? 'disabled' : ''}>
            </div>
        `;
        
        const slider = item.querySelector('.parameter-slider');
        const valueSpan = item.querySelector('.parameter-value');
        
        // Create debounced update function for this parameter
        if (!this.debouncedUpdates.has(param.name)) {
            this.debouncedUpdates.set(param.name, this._createDebouncedUpdate(param.name));
        }
        
        const debouncedUpdate = this.debouncedUpdates.get(param.name);
        
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value) / 100;
            
            // Update UI immediately for responsive feel
            valueSpan.textContent = value.toFixed(2);
            
            // Debounce the actual parameter update to limit frequency
            debouncedUpdate(value);
        });
        
        this.listContainer.appendChild(item);
    }
    
    /**
     * Update parameter UI
     */
    _updateParameterUI(param) {
        const element = this.listContainer.querySelector(`[data-param-name="${param.name}"]`);
        if (!element) return;
        
        const slider = element.querySelector('.parameter-slider');
        const valueSpan = element.querySelector('.parameter-value');
        
        if (slider && !slider.matches(':focus')) {
            slider.value = param.value * 100;
        }
        
        if (valueSpan) {
            valueSpan.textContent = param.value.toFixed(2);
        }
    }
    
    /**
     * Filter parameters by search query
     */
    _filterParameters() {
        const items = this.listContainer.querySelectorAll('.parameter-item');
        
        items.forEach(item => {
            const name = item.dataset.paramName.toLowerCase();
            const matches = name.includes(this.searchQuery);
            item.style.display = matches ? '' : 'none';
        });
    }
    
    /**
     * Update groups
     */
    _updateGroups() {
        this.groups.clear();
        
        this.parameters.forEach((param) => {
            if (!this.groups.has(param.group)) {
                this.groups.set(param.group, []);
            }
            this.groups.get(param.group).push(param.name);
        });
        
        if (this.options.showGroups) {
            this._renderGroups();
        }
    }
    
    /**
     * Render grouped parameters
     */
    _renderGroups() {
        // Sort items by group
        const items = Array.from(this.listContainer.querySelectorAll('.parameter-item'));
        
        items.sort((a, b) => {
            const groupA = a.dataset.paramGroup;
            const groupB = b.dataset.paramGroup;
            
            if (groupA === groupB) {
                return a.dataset.paramName.localeCompare(b.dataset.paramName);
            }
            
            return groupA.localeCompare(groupB);
        });
        
        // Re-append in sorted order
        items.forEach(item => this.listContainer.appendChild(item));
    }
    
    /**
     * Infer parameter group from name
     */
    _inferGroup(name) {
        const nameLower = name.toLowerCase();
        
        if (nameLower.includes('eye')) return 'Eyes';
        if (nameLower.includes('mouth')) return 'Mouth';
        if (nameLower.includes('brow') || nameLower.includes('eyebrow')) return 'Eyebrows';
        if (nameLower.includes('angle') || nameLower.includes('body')) return 'Body';
        if (nameLower.includes('breath')) return 'Animation';
        if (nameLower.includes('hair')) return 'Hair';
        
        return this.options.defaultGroup;
    }
    
    /**
     * Create debounced update function for a parameter
     * Uses simple debounce implementation to limit update frequency
     */
    _createDebouncedUpdate(paramName) {
        let timeoutId = null;
        
        return (value) => {
            // Clear any pending update
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
            }
            
            // Schedule new update
            timeoutId = setTimeout(() => {
                this.updateParameter(paramName, value);
                timeoutId = null;
            }, this.options.updateDelay);
        };
    }
    
    /**
     * Clamp value to valid range
     */
    _clampValue(value) {
        return Math.max(
            this.options.minValue,
            Math.min(this.options.maxValue, value)
        );
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
    _emitChange(name, value) {
        const event = {
            parameter: name,
            value: value,
            allParameters: this.getAllParameters()
        };
        
        // Emit specific parameter change
        if (this.listeners.has(`change:${name}`)) {
            this.listeners.get(`change:${name}`).forEach(callback => callback(event));
        }
        
        // Emit general change event
        if (this.listeners.has('change')) {
            this.listeners.get('change').forEach(callback => callback(event));
        }
    }
    
    /**
     * Export parameters as JSON
     */
    exportJSON() {
        const data = {
            parameters: {},
            metadata: {}
        };
        
        this.parameters.forEach((param, name) => {
            data.parameters[name] = param.value;
            data.metadata[name] = {
                group: param.group,
                min: param.min,
                max: param.max,
                defaultValue: param.defaultValue,
                description: param.description
            };
        });
        
        return JSON.stringify(data, null, 2);
    }
    
    /**
     * Import parameters from JSON
     */
    importJSON(json) {
        try {
            const data = typeof json === 'string' ? JSON.parse(json) : json;
            
            if (data.parameters) {
                Object.entries(data.parameters).forEach(([name, value]) => {
                    const metadata = data.metadata?.[name] || {};
                    this.setParameter(name, value, metadata);
                });
            }
            
            return true;
        } catch (error) {
            console.error('Failed to import parameters:', error);
            return false;
        }
    }
    
    /**
     * Clean up
     */
    dispose() {
        // Clear debounced update functions
        this.debouncedUpdates.clear();
        
        // Clear listeners
        this.listeners.clear();
        
        // Clear parameters
        this.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParameterPanel;
}

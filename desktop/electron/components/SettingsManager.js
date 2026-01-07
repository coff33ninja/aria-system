/**
 * SettingsManager Module
 * 
 * Manages settings persistence for Live2D controls
 * Supports localStorage for web, file system for Electron
 * Includes validation, import/export, and preset management
 */

class SettingsManager {
    constructor(options = {}) {
        this.options = {
            storageKey: 'live2d-controls-settings',
            autoSave: true,
            autoSaveDelay: 1000, // ms
            validateOnLoad: true,
            useElectron: typeof window !== 'undefined' && window.electronAPI,
            ...options
        };
        
        // Settings storage
        this.settings = {};
        
        // Schema for validation
        this.schema = {
            viewport: {
                x: { type: 'number', default: 0 },
                y: { type: 'number', default: 0 },
                zoom: { type: 'number', default: 1.0, min: 0.1, max: 5.0 },
                rotation: { type: 'number', default: 0, min: 0, max: 360 }
            },
            grid: {
                enabled: { type: 'boolean', default: false },
                type: { type: 'string', default: 'lines', enum: ['lines', 'dots', 'crosshair'] },
                spacing: { type: 'number', default: 50, min: 10, max: 200 },
                color: { type: 'string', default: '#ffffff' },
                opacity: { type: 'number', default: 0.3, min: 0, max: 1 },
                lineWidth: { type: 'number', default: 1, min: 0.5, max: 5 },
                dotSize: { type: 'number', default: 2, min: 1, max: 10 }
            },
            performance: {
                showGraph: { type: 'boolean', default: true },
                updateInterval: { type: 'number', default: 100, min: 50, max: 1000 },
                historyLength: { type: 'number', default: 60, min: 10, max: 300 }
            },
            parameters: {
                values: { type: 'object', default: {} },
                groups: { type: 'object', default: {} }
            },
            animations: {
                speed: { type: 'number', default: 1.0, min: 0.1, max: 3.0 },
                loop: { type: 'boolean', default: false }
            },
            debug: {
                panelDocked: { type: 'boolean', default: false },
                activeTab: { type: 'string', default: 'parameters' }
            }
        };
        
        // Presets storage
        this.presets = new Map();
        
        // Auto-save timer
        this.autoSaveTimer = null;
        
        // Event listeners
        this.listeners = new Map();
        
        // Load settings on initialization
        this.load();
    }
    
    /**
     * Get setting value
     */
    get(path, defaultValue = undefined) {
        const keys = path.split('.');
        let value = this.settings;
        
        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return defaultValue !== undefined ? defaultValue : this._getDefaultValue(path);
            }
        }
        
        return value;
    }
    
    /**
     * Set setting value
     */
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        let target = this.settings;
        
        // Navigate to parent object
        for (const key of keys) {
            if (!(key in target)) {
                target[key] = {};
            }
            target = target[key];
        }
        
        // Validate value
        const validatedValue = this._validateValue(path, value);
        
        // Set value
        target[lastKey] = validatedValue;
        
        // Trigger auto-save
        if (this.options.autoSave) {
            this._scheduleAutoSave();
        }
        
        // Emit change event
        this._emitChange(path, validatedValue);
        
        return validatedValue;
    }
    
    /**
     * Update multiple settings at once
     */
    update(updates) {
        Object.entries(updates).forEach(([path, value]) => {
            this.set(path, value);
        });
    }
    
    /**
     * Get all settings
     */
    getAll() {
        return JSON.parse(JSON.stringify(this.settings));
    }
    
    /**
     * Reset to defaults
     */
    reset() {
        this.settings = this._getDefaultSettings();
        this.save();
        this._emitChange('*', this.settings);
    }
    
    /**
     * Reset specific section
     */
    resetSection(section) {
        if (this.schema[section]) {
            this.settings[section] = this._getDefaultSection(section);
            this.save();
            this._emitChange(section, this.settings[section]);
        }
    }
    
    /**
     * Load settings from storage
     */
    async load() {
        try {
            let data;
            
            if (this.options.useElectron) {
                // Load from Electron settings
                data = await this._loadFromElectron();
            } else {
                // Load from localStorage
                data = this._loadFromLocalStorage();
            }
            
            if (data) {
                if (this.options.validateOnLoad) {
                    this.settings = this._validateSettings(data);
                } else {
                    this.settings = data;
                }
            } else {
                this.settings = this._getDefaultSettings();
            }
            
            this._emitEvent('loaded', this.settings);
            return true;
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.settings = this._getDefaultSettings();
            return false;
        }
    }
    
    /**
     * Save settings to storage
     */
    async save() {
        try {
            if (this.options.useElectron) {
                await this._saveToElectron();
            } else {
                this._saveToLocalStorage();
            }
            
            this._emitEvent('saved', this.settings);
            return true;
        } catch (error) {
            console.error('Failed to save settings:', error);
            return false;
        }
    }
    
    /**
     * Load from localStorage
     */
    _loadFromLocalStorage() {
        const json = localStorage.getItem(this.options.storageKey);
        return json ? JSON.parse(json) : null;
    }
    
    /**
     * Save to localStorage
     */
    _saveToLocalStorage() {
        localStorage.setItem(this.options.storageKey, JSON.stringify(this.settings));
    }
    
    /**
     * Load from Electron settings
     */
    async _loadFromElectron() {
        if (!window.electronAPI) return null;
        
        const electronSettings = await window.electronAPI.getSettings();
        return electronSettings?.live2dControls || null;
    }
    
    /**
     * Save to Electron settings
     */
    async _saveToElectron() {
        if (!window.electronAPI) return;
        
        const electronSettings = await window.electronAPI.getSettings();
        electronSettings.live2dControls = this.settings;
        await window.electronAPI.saveSettings(electronSettings);
    }
    
    /**
     * Schedule auto-save
     */
    _scheduleAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.autoSaveTimer = setTimeout(() => {
            this.save();
            this.autoSaveTimer = null;
        }, this.options.autoSaveDelay);
    }
    
    /**
     * Export settings as JSON
     */
    export() {
        return JSON.stringify(this.settings, null, 2);
    }
    
    /**
     * Import settings from JSON
     */
    import(json) {
        try {
            const data = typeof json === 'string' ? JSON.parse(json) : json;
            this.settings = this._validateSettings(data);
            this.save();
            this._emitChange('*', this.settings);
            return true;
        } catch (error) {
            console.error('Failed to import settings:', error);
            return false;
        }
    }
    
    /**
     * Save preset
     */
    savePreset(name, description = '') {
        const preset = {
            name,
            description,
            settings: this.getAll(),
            timestamp: Date.now()
        };
        
        this.presets.set(name, preset);
        this._savePresets();
        this._emitEvent('presetSaved', preset);
        
        return preset;
    }
    
    /**
     * Load preset
     */
    loadPreset(name) {
        const preset = this.presets.get(name);
        if (!preset) {
            console.warn(`Preset '${name}' not found`);
            return false;
        }
        
        this.settings = JSON.parse(JSON.stringify(preset.settings));
        this.save();
        this._emitChange('*', this.settings);
        this._emitEvent('presetLoaded', preset);
        
        return true;
    }
    
    /**
     * Delete preset
     */
    deletePreset(name) {
        const deleted = this.presets.delete(name);
        if (deleted) {
            this._savePresets();
            this._emitEvent('presetDeleted', { name });
        }
        return deleted;
    }
    
    /**
     * Get all presets
     */
    getPresets() {
        return Array.from(this.presets.values());
    }
    
    /**
     * Save presets to storage
     */
    _savePresets() {
        const presetsArray = Array.from(this.presets.entries());
        const json = JSON.stringify(presetsArray);
        
        if (this.options.useElectron) {
            // Save to Electron
            localStorage.setItem(`${this.options.storageKey}-presets`, json);
        } else {
            localStorage.setItem(`${this.options.storageKey}-presets`, json);
        }
    }
    
    /**
     * Load presets from storage
     */
    _loadPresets() {
        try {
            const json = localStorage.getItem(`${this.options.storageKey}-presets`);
            if (json) {
                const presetsArray = JSON.parse(json);
                this.presets = new Map(presetsArray);
            }
        } catch (error) {
            console.error('Failed to load presets:', error);
        }
    }
    
    /**
     * Get default settings
     */
    _getDefaultSettings() {
        const defaults = {};
        
        Object.entries(this.schema).forEach(([section, fields]) => {
            defaults[section] = this._getDefaultSection(section);
        });
        
        return defaults;
    }
    
    /**
     * Get default section
     */
    _getDefaultSection(section) {
        const defaults = {};
        const fields = this.schema[section];
        
        if (fields) {
            Object.entries(fields).forEach(([key, config]) => {
                defaults[key] = config.default;
            });
        }
        
        return defaults;
    }
    
    /**
     * Get default value for path
     */
    _getDefaultValue(path) {
        const keys = path.split('.');
        const section = keys[0];
        const field = keys[1];
        
        if (this.schema[section] && this.schema[section][field]) {
            return this.schema[section][field].default;
        }
        
        return undefined;
    }
    
    /**
     * Validate settings object
     */
    _validateSettings(settings) {
        const validated = {};
        
        Object.entries(this.schema).forEach(([section, fields]) => {
            validated[section] = {};
            
            Object.entries(fields).forEach(([key, config]) => {
                const value = settings[section]?.[key];
                validated[section][key] = this._validateValue(`${section}.${key}`, value);
            });
        });
        
        return validated;
    }
    
    /**
     * Validate single value
     */
    _validateValue(path, value) {
        const keys = path.split('.');
        const section = keys[0];
        const field = keys[1];
        
        if (!this.schema[section] || !this.schema[section][field]) {
            return value;
        }
        
        const config = this.schema[section][field];
        
        // Use default if value is undefined
        if (value === undefined || value === null) {
            return config.default;
        }
        
        // Type validation
        if (config.type === 'number') {
            const num = Number(value);
            if (isNaN(num)) return config.default;
            
            // Range validation
            if (config.min !== undefined && num < config.min) return config.min;
            if (config.max !== undefined && num > config.max) return config.max;
            
            return num;
        }
        
        if (config.type === 'boolean') {
            return Boolean(value);
        }
        
        if (config.type === 'string') {
            const str = String(value);
            
            // Enum validation
            if (config.enum && !config.enum.includes(str)) {
                return config.default;
            }
            
            return str;
        }
        
        if (config.type === 'object') {
            return typeof value === 'object' ? value : config.default;
        }
        
        return value;
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
    _emitChange(path, value) {
        const event = {
            path,
            value,
            settings: this.getAll()
        };
        
        // Emit specific path change
        if (this.listeners.has(`change:${path}`)) {
            this.listeners.get(`change:${path}`).forEach(callback => callback(event));
        }
        
        // Emit general change event
        if (this.listeners.has('change')) {
            this.listeners.get('change').forEach(callback => callback(event));
        }
    }
    
    /**
     * Emit general event
     */
    _emitEvent(type, data) {
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(data));
        }
    }
    
    /**
     * Clean up
     */
    dispose() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.listeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SettingsManager;
}

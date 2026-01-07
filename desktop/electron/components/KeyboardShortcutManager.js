/**
 * KeyboardShortcutManager
 * 
 * Manages keyboard shortcuts for Live2D controls
 * Supports customization, modifier keys, and conflict detection
 */

class KeyboardShortcutManager {
    constructor(options = {}) {
        this.options = {
            preventDefault: true,
            stopPropagation: true,
            enableInInputs: false, // Allow shortcuts in input fields
            ...options
        };
        
        // Shortcut registry
        this.shortcuts = new Map();
        
        // Active modifiers
        this.activeModifiers = {
            ctrl: false,
            shift: false,
            alt: false,
            meta: false
        };
        
        // Event listeners
        this.listeners = new Map();
        
        // Enabled state
        this.enabled = true;
        
        // Setup event listeners
        this._setupEventListeners();
    }
    
    /**
     * Setup keyboard event listeners
     */
    _setupEventListeners() {
        this.keydownHandler = this._onKeyDown.bind(this);
        this.keyupHandler = this._onKeyUp.bind(this);
        
        document.addEventListener('keydown', this.keydownHandler);
        document.addEventListener('keyup', this.keyupHandler);
    }
    
    /**
     * Register a keyboard shortcut
     */
    register(shortcut, callback, options = {}) {
        const normalized = this._normalizeShortcut(shortcut);
        
        // Check for conflicts
        if (this.shortcuts.has(normalized) && !options.override) {
            console.warn(`Shortcut '${shortcut}' is already registered`);
            return false;
        }
        
        this.shortcuts.set(normalized, {
            original: shortcut,
            callback,
            description: options.description || '',
            enabled: options.enabled !== false,
            preventDefault: options.preventDefault !== false,
            stopPropagation: options.stopPropagation !== false
        });
        
        this._emitEvent('registered', { shortcut: normalized });
        return true;
    }
    
    /**
     * Unregister a keyboard shortcut
     */
    unregister(shortcut) {
        const normalized = this._normalizeShortcut(shortcut);
        const deleted = this.shortcuts.delete(normalized);
        
        if (deleted) {
            this._emitEvent('unregistered', { shortcut: normalized });
        }
        
        return deleted;
    }
    
    /**
     * Enable a specific shortcut
     */
    enableShortcut(shortcut) {
        const normalized = this._normalizeShortcut(shortcut);
        const entry = this.shortcuts.get(normalized);
        
        if (entry) {
            entry.enabled = true;
            return true;
        }
        
        return false;
    }
    
    /**
     * Disable a specific shortcut
     */
    disableShortcut(shortcut) {
        const normalized = this._normalizeShortcut(shortcut);
        const entry = this.shortcuts.get(normalized);
        
        if (entry) {
            entry.enabled = false;
            return true;
        }
        
        return false;
    }
    
    /**
     * Enable all shortcuts
     */
    enable() {
        this.enabled = true;
    }
    
    /**
     * Disable all shortcuts
     */
    disable() {
        this.enabled = false;
    }
    
    /**
     * Get all registered shortcuts
     */
    getShortcuts() {
        const result = [];
        
        this.shortcuts.forEach((entry, key) => {
            result.push({
                shortcut: entry.original,
                normalized: key,
                description: entry.description,
                enabled: entry.enabled
            });
        });
        
        return result;
    }
    
    /**
     * Check if shortcut is registered
     */
    isRegistered(shortcut) {
        const normalized = this._normalizeShortcut(shortcut);
        return this.shortcuts.has(normalized);
    }
    
    /**
     * Handle keydown event
     */
    _onKeyDown(event) {
        if (!this.enabled) return;
        
        // Skip if in input field (unless enabled)
        if (!this.options.enableInInputs && this._isInputElement(event.target)) {
            return;
        }
        
        // Update modifier state
        this._updateModifiers(event);
        
        // Build shortcut string
        const shortcut = this._buildShortcutString(event);
        
        // Find matching shortcut
        const entry = this.shortcuts.get(shortcut);
        
        if (entry && entry.enabled) {
            // Prevent default if configured
            if (entry.preventDefault || this.options.preventDefault) {
                event.preventDefault();
            }
            
            // Stop propagation if configured
            if (entry.stopPropagation || this.options.stopPropagation) {
                event.stopPropagation();
            }
            
            // Execute callback
            try {
                entry.callback(event);
                this._emitEvent('triggered', { shortcut, event });
            } catch (error) {
                console.error(`Error executing shortcut '${shortcut}':`, error);
            }
        }
    }
    
    /**
     * Handle keyup event
     */
    _onKeyUp(event) {
        this._updateModifiers(event);
    }
    
    /**
     * Update modifier key state
     */
    _updateModifiers(event) {
        this.activeModifiers.ctrl = event.ctrlKey;
        this.activeModifiers.shift = event.shiftKey;
        this.activeModifiers.alt = event.altKey;
        this.activeModifiers.meta = event.metaKey;
    }
    
    /**
     * Build shortcut string from event
     */
    _buildShortcutString(event) {
        const parts = [];
        
        // Add modifiers in consistent order
        if (event.ctrlKey || event.metaKey) parts.push('Ctrl');
        if (event.shiftKey) parts.push('Shift');
        if (event.altKey) parts.push('Alt');
        
        // Add key
        const key = this._normalizeKey(event.key);
        if (key && !['Control', 'Shift', 'Alt', 'Meta'].includes(key)) {
            parts.push(key);
        }
        
        return parts.join('+');
    }
    
    /**
     * Normalize shortcut string
     */
    _normalizeShortcut(shortcut) {
        const parts = shortcut.split('+').map(p => p.trim());
        const normalized = [];
        
        // Extract modifiers
        const hasCtrl = parts.some(p => ['Ctrl', 'Control', 'Cmd', 'Command', 'Meta'].includes(p));
        const hasShift = parts.some(p => p === 'Shift');
        const hasAlt = parts.some(p => p === 'Alt');
        
        // Add modifiers in consistent order
        if (hasCtrl) normalized.push('Ctrl');
        if (hasShift) normalized.push('Shift');
        if (hasAlt) normalized.push('Alt');
        
        // Add key (last non-modifier part)
        const key = parts.find(p => !['Ctrl', 'Control', 'Cmd', 'Command', 'Meta', 'Shift', 'Alt'].includes(p));
        if (key) {
            normalized.push(this._normalizeKey(key));
        }
        
        return normalized.join('+');
    }
    
    /**
     * Normalize key name
     */
    _normalizeKey(key) {
        // Convert to uppercase for letters
        if (key.length === 1) {
            return key.toUpperCase();
        }
        
        // Special key mappings
        const keyMap = {
            'ArrowUp': 'Up',
            'ArrowDown': 'Down',
            'ArrowLeft': 'Left',
            'ArrowRight': 'Right',
            ' ': 'Space',
            'Escape': 'Esc'
        };
        
        return keyMap[key] || key;
    }
    
    /**
     * Check if element is an input
     */
    _isInputElement(element) {
        const tagName = element.tagName.toLowerCase();
        return (
            tagName === 'input' ||
            tagName === 'textarea' ||
            tagName === 'select' ||
            element.isContentEditable
        );
    }
    
    /**
     * Get shortcut hint text
     */
    getHintText(shortcut) {
        const normalized = this._normalizeShortcut(shortcut);
        const entry = this.shortcuts.get(normalized);
        
        if (!entry) return '';
        
        // Format for display
        const parts = normalized.split('+');
        const formatted = parts.map(part => {
            if (part === 'Ctrl') return '⌃';
            if (part === 'Shift') return '⇧';
            if (part === 'Alt') return '⌥';
            return part;
        });
        
        return formatted.join('');
    }
    
    /**
     * Export shortcuts as JSON
     */
    exportJSON() {
        const data = {};
        
        this.shortcuts.forEach((entry, key) => {
            data[key] = {
                original: entry.original,
                description: entry.description,
                enabled: entry.enabled
            };
        });
        
        return JSON.stringify(data, null, 2);
    }
    
    /**
     * Import shortcuts from JSON
     */
    importJSON(json) {
        try {
            const data = typeof json === 'string' ? JSON.parse(json) : json;
            
            Object.entries(data).forEach(([key, config]) => {
                if (this.shortcuts.has(key)) {
                    const entry = this.shortcuts.get(key);
                    entry.enabled = config.enabled !== false;
                }
            });
            
            return true;
        } catch (error) {
            console.error('Failed to import shortcuts:', error);
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
    _emitEvent(type, data) {
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(data));
        }
    }
    
    /**
     * Clean up
     */
    dispose() {
        document.removeEventListener('keydown', this.keydownHandler);
        document.removeEventListener('keyup', this.keyupHandler);
        
        this.shortcuts.clear();
        this.listeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardShortcutManager;
}

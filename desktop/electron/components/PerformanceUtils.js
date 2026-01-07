/**
 * Performance Utilities
 * 
 * Utility functions for optimizing performance in Live2D controls
 * Includes debounce, throttle, and RAF-based throttling
 */

/**
 * Debounce function - delays execution until after wait time has elapsed since last call
 * Perfect for input handlers that should only fire after user stops typing/dragging
 * 
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @param {boolean} immediate - Execute on leading edge instead of trailing
 * @returns {Function} Debounced function
 */
function debounce(func, wait, immediate = false) {
    let timeout;
    
    return function executedFunction(...args) {
        const context = this;
        
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Throttle function - ensures function is called at most once per wait period
 * Perfect for scroll/resize handlers that should fire regularly but not too often
 * 
 * @param {Function} func - Function to throttle
 * @param {number} wait - Milliseconds between calls
 * @returns {Function} Throttled function
 */
function throttle(func, wait) {
    let inThrottle;
    let lastFunc;
    let lastTime;
    
    return function executedFunction(...args) {
        const context = this;
        
        if (!inThrottle) {
            func.apply(context, args);
            lastTime = Date.now();
            inThrottle = true;
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(() => {
                if (Date.now() - lastTime >= wait) {
                    func.apply(context, args);
                    lastTime = Date.now();
                }
            }, Math.max(wait - (Date.now() - lastTime), 0));
        }
    };
}

/**
 * RequestAnimationFrame-based throttle
 * Ensures function is called at most once per animation frame (60fps max)
 * Perfect for rendering operations that should sync with browser paint
 * 
 * @param {Function} func - Function to throttle
 * @returns {Function} RAF-throttled function
 */
function rafThrottle(func) {
    let rafId = null;
    let lastArgs = null;
    
    return function executedFunction(...args) {
        lastArgs = args;
        
        if (rafId === null) {
            rafId = requestAnimationFrame(() => {
                func.apply(this, lastArgs);
                rafId = null;
            });
        }
    };
}

/**
 * Cache manager for expensive operations
 * Caches results based on a key and only recomputes when key changes
 */
class CacheManager {
    constructor() {
        this.cache = new Map();
    }
    
    /**
     * Get cached value or compute and cache it
     * 
     * @param {string} key - Cache key
     * @param {Function} computeFn - Function to compute value if not cached
     * @returns {*} Cached or computed value
     */
    get(key, computeFn) {
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        
        const value = computeFn();
        this.cache.set(key, value);
        return value;
    }
    
    /**
     * Check if key exists in cache
     */
    has(key) {
        return this.cache.has(key);
    }
    
    /**
     * Set cache value directly
     */
    set(key, value) {
        this.cache.set(key, value);
    }
    
    /**
     * Invalidate specific cache entry
     */
    invalidate(key) {
        this.cache.delete(key);
    }
    
    /**
     * Clear all cache
     */
    clear() {
        this.cache.clear();
    }
    
    /**
     * Get cache size
     */
    size() {
        return this.cache.size;
    }
}

/**
 * Batch update manager
 * Collects multiple updates and applies them in a single batch
 */
class BatchUpdateManager {
    constructor(applyFn, delay = 16) {
        this.applyFn = applyFn;
        this.delay = delay;
        this.pending = new Map();
        this.timeoutId = null;
    }
    
    /**
     * Schedule an update
     */
    schedule(key, value) {
        this.pending.set(key, value);
        
        if (!this.timeoutId) {
            this.timeoutId = setTimeout(() => {
                this.flush();
            }, this.delay);
        }
    }
    
    /**
     * Flush all pending updates immediately
     */
    flush() {
        if (this.pending.size > 0) {
            this.applyFn(this.pending);
            this.pending.clear();
        }
        
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }
    
    /**
     * Cancel all pending updates
     */
    cancel() {
        this.pending.clear();
        
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        throttle,
        rafThrottle,
        CacheManager,
        BatchUpdateManager
    };
}

/**
 * LoadingErrorHandler Utility
 * 
 * Provides loading states, error handling, and user feedback
 * Shared utility for all Live2D control components
 */

class LoadingErrorHandler {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            spinnerColor: '#ff6b9d',
            errorColor: '#f87171',
            successColor: '#4ade80',
            autoHideSuccess: true,
            successDuration: 3000, // ms
            ...options
        };
        
        this.loadingOverlay = null;
        this.errorContainer = null;
        this.isLoading = false;
        
        this._initializeElements();
    }
    
    /**
     * Initialize loading and error elements
     */
    _initializeElements() {
        // Create loading overlay
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.className = 'loading-overlay';
        this.loadingOverlay.style.display = 'none';
        this.loadingOverlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-message">Loading...</div>
        `;
        
        // Create error container
        this.errorContainer = document.createElement('div');
        this.errorContainer.className = 'error-container';
        this.errorContainer.style.display = 'none';
        this.errorContainer.innerHTML = `
            <div class="error-icon">⚠️</div>
            <div class="error-message"></div>
            <div class="error-actions">
                <button class="error-retry-btn">Retry</button>
                <button class="error-dismiss-btn">Dismiss</button>
            </div>
        `;
        
        // Append to container
        if (this.container) {
            this.container.style.position = 'relative';
            this.container.appendChild(this.loadingOverlay);
            this.container.appendChild(this.errorContainer);
        }
    }
    
    /**
     * Show loading state
     */
    showLoading(message = 'Loading...') {
        if (!this.loadingOverlay) return;
        
        this.isLoading = true;
        this.hideError();
        
        const messageEl = this.loadingOverlay.querySelector('.loading-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        this.loadingOverlay.style.display = 'flex';
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        if (!this.loadingOverlay) return;
        
        this.isLoading = false;
        this.loadingOverlay.style.display = 'none';
    }
    
    /**
     * Show error message
     */
    showError(error, options = {}) {
        if (!this.errorContainer) return;
        
        this.hideLoading();
        
        const {
            message = this._getErrorMessage(error),
            retryCallback = null,
            dismissCallback = null
        } = options;
        
        const messageEl = this.errorContainer.querySelector('.error-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        // Setup retry button
        const retryBtn = this.errorContainer.querySelector('.error-retry-btn');
        if (retryBtn) {
            retryBtn.style.display = retryCallback ? 'block' : 'none';
            retryBtn.onclick = () => {
                this.hideError();
                if (retryCallback) retryCallback();
            };
        }
        
        // Setup dismiss button
        const dismissBtn = this.errorContainer.querySelector('.error-dismiss-btn');
        if (dismissBtn) {
            dismissBtn.onclick = () => {
                this.hideError();
                if (dismissCallback) dismissCallback();
            };
        }
        
        this.errorContainer.style.display = 'flex';
        
        // Log to console for debugging
        console.error('LoadingErrorHandler:', error);
    }
    
    /**
     * Hide error message
     */
    hideError() {
        if (!this.errorContainer) return;
        this.errorContainer.style.display = 'none';
    }
    
    /**
     * Show success message
     */
    showSuccess(message = 'Success!') {
        if (!this.container) return;
        
        this.hideLoading();
        this.hideError();
        
        const successEl = document.createElement('div');
        successEl.className = 'success-message';
        successEl.innerHTML = `
            <div class="success-icon">✓</div>
            <div class="success-text">${message}</div>
        `;
        
        this.container.appendChild(successEl);
        
        // Auto-hide after duration
        if (this.options.autoHideSuccess) {
            setTimeout(() => {
                successEl.remove();
            }, this.options.successDuration);
        }
    }
    
    /**
     * Extract user-friendly error message
     */
    _getErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        
        if (error instanceof Error) {
            // Check for specific error types
            if (error.message.includes('texture')) {
                return 'Failed to load model textures. Please check that all texture files are present.';
            }
            
            if (error.message.includes('JSON')) {
                return 'Invalid model file format. Please select a valid Live2D model JSON file.';
            }
            
            if (error.message.includes('network') || error.message.includes('fetch')) {
                return 'Network error. Please check your connection and try again.';
            }
            
            if (error.message.includes('permission')) {
                return 'Permission denied. Please check file access permissions.';
            }
            
            return error.message || 'An unexpected error occurred.';
        }
        
        return 'An unexpected error occurred. Please try again.';
    }
    
    /**
     * Wrap async operation with loading and error handling
     */
    async wrapAsync(operation, options = {}) {
        const {
            loadingMessage = 'Loading...',
            successMessage = null,
            errorMessage = null,
            retryCallback = null
        } = options;
        
        try {
            this.showLoading(loadingMessage);
            const result = await operation();
            this.hideLoading();
            
            if (successMessage) {
                this.showSuccess(successMessage);
            }
            
            return result;
        } catch (error) {
            this.showError(error, {
                message: errorMessage || this._getErrorMessage(error),
                retryCallback: retryCallback ? () => this.wrapAsync(operation, options) : null
            });
            throw error;
        }
    }
    
    /**
     * Check if currently loading
     */
    isLoadingState() {
        return this.isLoading;
    }
    
    /**
     * Clean up
     */
    dispose() {
        if (this.loadingOverlay) {
            this.loadingOverlay.remove();
        }
        
        if (this.errorContainer) {
            this.errorContainer.remove();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingErrorHandler;
}

// Default styles
const LOADING_ERROR_HANDLER_STYLES = `
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    border-radius: inherit;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #ff6b9d;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-message {
    margin-top: 16px;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
}

.error-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(248, 113, 113, 0.95);
    border: 2px solid #f87171;
    border-radius: 8px;
    padding: 20px;
    max-width: 400px;
    z-index: 1001;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.error-icon {
    font-size: 32px;
    margin-bottom: 12px;
}

.error-message {
    color: #fff;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 16px;
}

.error-actions {
    display: flex;
    gap: 8px;
}

.error-retry-btn,
.error-dismiss-btn {
    padding: 8px 16px;
    font-size: 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 600;
}

.error-retry-btn {
    background: #fff;
    color: #f87171;
}

.error-retry-btn:hover {
    background: #f0f0f0;
}

.error-dismiss-btn {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
}

.error-dismiss-btn:hover {
    background: rgba(255, 255, 255, 0.3);
}

.success-message {
    position: absolute;
    top: 16px;
    right: 16px;
    background: rgba(74, 222, 128, 0.95);
    border: 2px solid #4ade80;
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    z-index: 1002;
    animation: slideIn 0.3s ease-out;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.success-icon {
    font-size: 20px;
    color: #fff;
    font-weight: bold;
}

.success-text {
    color: #fff;
    font-size: 13px;
    font-weight: 500;
}
`;

// Export styles
if (typeof module !== 'undefined' && module.exports) {
    module.exports.LOADING_ERROR_HANDLER_STYLES = LOADING_ERROR_HANDLER_STYLES;
}

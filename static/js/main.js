// Main JavaScript for ExamPortal

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Setup HTMX configuration
    setupHTMX();
    
    // Initialize common UI components
    initializeTooltips();
    initializeModals();
    initializeNotifications();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Initialize lazy loading
    initializeLazyLoading();
}

// HTMX Configuration
function setupHTMX() {
    // Configure HTMX defaults
    htmx.config.historyCacheSize = 20;
    htmx.config.refreshOnHistoryMiss = true;
    
    // Add loading indicators
    document.body.addEventListener('htmx:beforeRequest', function(e) {
        showLoadingIndicator(e.target);
    });
    
    document.body.addEventListener('htmx:afterRequest', function(e) {
        hideLoadingIndicator(e.target);
        
        // Re-initialize components on new content
        if (e.detail.successful) {
            initializeTooltips();
        }
    });
    
    // Handle errors
    document.body.addEventListener('htmx:responseError', function(e) {
        showNotification('An error occurred. Please try again.', 'error');
    });
}

// Loading Indicators
function showLoadingIndicator(element) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'htmx-loading-indicator absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center';
    loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
    
    const parent = element.closest('.relative') || element.parentElement;
    if (parent && !parent.classList.contains('relative')) {
        parent.classList.add('relative');
    }
    parent.appendChild(loadingDiv);
}

function hideLoadingIndicator(element) {
    const indicators = document.querySelectorAll('.htmx-loading-indicator');
    indicators.forEach(indicator => indicator.remove());
}

// Tooltip functionality
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        if (element.hasTooltip) return; // Already initialized
        
        element.hasTooltip = true;
        
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.dataset.tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg';
    tooltip.textContent = text;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Modal functionality
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modalTarget;
            openModal(modalId);
        });
    });
    
    // Close modal on backdrop click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });
    document.body.style.overflow = '';
}

// Notification system
function initializeNotifications() {
    // Auto-hide notifications after 5 seconds
    const notifications = document.querySelectorAll('.notification[data-auto-hide="true"]');
    notifications.forEach(notification => {
        setTimeout(() => {
            hideNotification(notification);
        }, 5000);
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg max-w-sm fade-in ${getNotificationClasses(type)}`;
    
    notification.innerHTML = `
        <div class="flex">
            <div class="flex-shrink-0">
                ${getNotificationIcon(type)}
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button onclick="hideNotification(this.closest('.notification'))" class="inline-flex text-gray-400 hover:text-gray-600">
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideNotification(notification);
    }, 5000);
}

function hideNotification(notification) {
    if (notification) {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

function getNotificationClasses(type) {
    const classes = {
        'success': 'bg-green-50 text-green-800 border border-green-200',
        'error': 'bg-red-50 text-red-800 border border-red-200',
        'warning': 'bg-yellow-50 text-yellow-800 border border-yellow-200',
        'info': 'bg-blue-50 text-blue-800 border border-blue-200'
    };
    return classes[type] || classes.info;
}

function getNotificationIcon(type) {
    const icons = {
        'success': '<svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>',
        'error': '<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>',
        'warning': '<svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>',
        'info': '<svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" /></svg>'
    };
    return icons[type] || icons.info;
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('global-search');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals/dropdowns
        if (e.key === 'Escape') {
            closeModal();
            closeDropdowns();
        }
    });
}

function closeDropdowns() {
    const dropdowns = document.querySelectorAll('[x-data]');
    dropdowns.forEach(dropdown => {
        if (dropdown._x_dataStack) {
            const data = dropdown._x_dataStack[0];
            if (data.open !== undefined) {
                data.open = false;
            }
        }
    });
}

// Lazy loading for images and content
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Form validation helpers
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else {
            hideFieldError(input);
        }
    });
    
    return isValid;
}

function showFieldError(input, message) {
    const errorDiv = input.parentElement.querySelector('.field-error') || createErrorDiv();
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    input.classList.add('border-red-500');
    
    if (!input.parentElement.contains(errorDiv)) {
        input.parentElement.appendChild(errorDiv);
    }
}

function hideFieldError(input) {
    const errorDiv = input.parentElement.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
    input.classList.remove('border-red-500');
}

function createErrorDiv() {
    const div = document.createElement('div');
    div.className = 'field-error text-sm text-red-600 mt-1';
    return div;
}

// Export functions for global access
window.ExamPortal = {
    showNotification,
    hideNotification,
    openModal,
    closeModal,
    validateForm,
    debounce,
    throttle
};
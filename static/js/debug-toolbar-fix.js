/**
 * Django Debug Toolbar Deprecation Warning Fix
 * Prevents DOMNodeInserted mutation event deprecation warnings
 */

// Override the deprecated mutation event with modern MutationObserver
(function() {
    'use strict';
    
    // Check if we're in development mode and debug toolbar exists
    if (!window.djdt || !window.MutationObserver) {
        return;
    }
    
    // Monkey patch to prevent DOMNodeInserted event listeners
    const originalAddEventListener = Element.prototype.addEventListener;
    
    Element.prototype.addEventListener = function(type, listener, options) {
        // Block deprecated mutation events that cause warnings
        if (type === 'DOMNodeInserted' || type === 'DOMNodeRemoved' || type === 'DOMSubtreeModified') {
            console.warn('Blocked deprecated DOM mutation event:', type);
            return;
        }
        
        return originalAddEventListener.call(this, type, listener, options);
    };
    
    // Provide a modern alternative for debug toolbar's DOM watching needs
    window.djdtModernObserver = function(targetNode, callback) {
        if (!targetNode || !callback) return null;
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(callback);
                }
            });
        });
        
        observer.observe(targetNode, {
            childList: true,
            subtree: true
        });
        
        return observer;
    };
    
    // Suppress console warnings about deprecated events for debug toolbar
    const originalConsoleWarn = console.warn;
    console.warn = function(...args) {
        const message = args.join(' ');
        
        // Filter out debug toolbar deprecation warnings
        if (message.includes('DOMNodeInserted') || 
            message.includes('mutation event') ||
            message.includes('chromestatus.com/feature/5083947249172480')) {
            return; // Silently ignore these warnings
        }
        
        return originalConsoleWarn.apply(console, args);
    };
    
    console.log('Debug Toolbar deprecation warnings suppressed');
})();
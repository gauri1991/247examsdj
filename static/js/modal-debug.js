// Debug script to test modal functionality
window.debugMathModal = function() {
    console.log('=== Math Modal Debug Information ===');
    
    // Check if modal elements exist
    const modal = document.getElementById('math-equation-modal');
    const toolbar = document.getElementById('math-symbol-toolbar');
    const input = document.getElementById('math-latex-input');
    const preview = document.getElementById('math-preview-pane');
    
    console.log('Modal elements found:');
    console.log('- Modal:', !!modal);
    console.log('- Toolbar:', !!toolbar);
    console.log('- Input:', !!input);
    console.log('- Preview:', !!preview);
    
    if (modal) {
        console.log('Modal display style:', modal.style.display);
        console.log('Modal visibility:', modal.style.visibility);
        console.log('Modal opacity:', modal.style.opacity);
        console.log('Modal classes:', modal.className);
        console.log('Modal computed display:', getComputedStyle(modal).display);
        console.log('Modal computed visibility:', getComputedStyle(modal).visibility);
        console.log('Modal has math-modal-shown class:', modal.classList.contains('math-modal-shown'));
    }
    
    if (toolbar) {
        console.log('Toolbar children count:', toolbar.children.length);
        console.log('Toolbar display style:', getComputedStyle(toolbar).display);
        console.log('Toolbar visibility:', getComputedStyle(toolbar).visibility);
    }
    
    // Check body state
    console.log('Body has math-modal-open class:', document.body.classList.contains('math-modal-open'));
    console.log('Body overflow style:', document.body.style.overflow);
    console.log('Body pointer-events:', document.body.style.pointerEvents);
    
    // Check if MathEquationModal is loaded
    console.log('MathEquationModal available:', !!window.MathEquationModal);
    
    if (window.MathEquationModal) {
        console.log('Available methods:', Object.keys(window.MathEquationModal));
    }
    
    console.log('=== End Debug Information ===');
};

// Test modal opening/closing
window.testMathModalOpen = function() {
    console.log('Testing modal open...');
    if (window.MathEquationModal) {
        window.MathEquationModal.openModal();
    } else {
        console.error('MathEquationModal not available');
    }
};

window.testMathModalClose = function() {
    console.log('Testing modal close...');
    if (window.MathEquationModal) {
        window.MathEquationModal.closeModal();
    } else {
        console.error('MathEquationModal not available');
    }
};

// Auto-run debug when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(window.debugMathModal, 1000);
    
    // Check for any auto-opening issues
    setTimeout(() => {
        const modal = document.getElementById('math-equation-modal');
        if (modal && (getComputedStyle(modal).display !== 'none' || modal.style.display === 'flex')) {
            console.error('⚠️ CRITICAL: Modal is showing when it should be hidden!');
            console.log('Forcing modal to hide...');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            modal.style.opacity = '0';
            modal.style.pointerEvents = 'none';
            modal.classList.remove('math-modal-shown');
            document.body.classList.remove('math-modal-open');
            document.body.style.overflow = '';
            document.body.style.pointerEvents = '';
        }
    }, 500);
});
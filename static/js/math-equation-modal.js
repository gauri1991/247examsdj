/**
 * Mathematical Equation Panel JavaScript
 * Enterprise-grade implementation with Google-level standards
 */

// Global variables for math equation panel
let mathModal, mathLatexInput, mathPreviewPane, mathStatusText, mathStatus;
let currentQuillEditor = null;
let storedCursorPosition = null;

// Comprehensive Math Symbol Toolbar - All 8 Categories
const mathSymbols = {
    'Basic': ['\\frac{a}{b}', 'x^{a}', 'x_{a}', '\\sqrt{x}', '\\sqrt[n]{x}', '\\sum', '\\prod', '\\int', '\\lim'],
    'Greek': ['\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\theta', '\\lambda', '\\mu', '\\pi', '\\sigma', '\\phi', '\\omega', '\\Gamma', '\\Delta', '\\Theta', '\\Lambda', '\\Pi', '\\Sigma', '\\Phi', '\\Omega'],
    'Operators': ['+', '-', '\\times', '\\div', '\\pm', '\\mp', '\\cdot', '\\ast', '\\star', '\\bullet', '\\circ', '\\oplus', '\\ominus', '\\otimes', '\\oslash'],
    'Relations': ['=', '\\neq', '<', '>', '\\leq', '\\geq', '\\ll', '\\gg', '\\equiv', '\\approx', '\\sim', '\\simeq', '\\cong', '\\propto', '\\parallel', '\\perp'],
    'Logic': ['\\land', '\\lor', '\\lnot', '\\implies', '\\iff', '\\forall', '\\exists', '\\nexists', '\\therefore', '\\because'],
    'Sets': ['\\in', '\\notin', '\\subset', '\\supset', '\\subseteq', '\\supseteq', '\\cup', '\\cap', '\\setminus', '\\emptyset', '\\mathbb{N}', '\\mathbb{Z}', '\\mathbb{Q}', '\\mathbb{R}', '\\mathbb{C}'],
    'Arrows': ['\\rightarrow', '\\leftarrow', '\\leftrightarrow', '\\Rightarrow', '\\Leftarrow', '\\Leftrightarrow', '\\uparrow', '\\downarrow', '\\updownarrow', '\\nearrow', '\\searrow', '\\swarrow', '\\nwarrow'],
    'Misc': ['\\infty', '\\partial', '\\nabla', '\\degree', '\\angle', '\\triangle', '\\square', '\\diamond', '\\clubsuit', '\\heartsuit', '\\spadesuit', '\\diamondsuit', '\\checkmark', '\\times', '\\rupee']
};

/**
 * Initialize Mathematical Equation Panel
 */
function initializeMathEquationPanel() {
    console.log('Initializing math equation panel...');
    
    // Prevent debug toolbar interference
    try {
        // Ensure debug toolbar doesn't interfere with modal initialization
        const debugToolbar = document.getElementById('djDebug');
        if (debugToolbar) {
            // Store original position
            window.originalDebugToolbarZIndex = debugToolbar.style.zIndex || '';
            debugToolbar.setAttribute('data-math-modal-compatible', 'true');
        }
    } catch (debugError) {
        console.log('Debug toolbar compatibility check failed (non-critical):', debugError);
    }
    
    // Get DOM elements
    mathModal = document.getElementById('math-equation-modal');
    mathLatexInput = document.getElementById('math-latex-input');
    mathPreviewPane = document.getElementById('math-preview-pane');
    mathStatusText = document.getElementById('math-status-text');
    mathStatus = document.getElementById('math-status');
    
    // Debug element finding
    console.log('Math modal elements found:', {
        mathModal: !!mathModal,
        mathLatexInput: !!mathLatexInput,
        mathPreviewPane: !!mathPreviewPane,
        mathStatusText: !!mathStatusText,
        mathStatus: !!mathStatus
    });
    
    // Continue even if some elements are missing - we'll handle it gracefully
    if (!mathModal) {
        console.error('Critical: Math modal element not found!');
        console.log('Available elements with math- prefix:', 
            Array.from(document.querySelectorAll('[id*="math"]')).map(el => el.id));
        return false;
    }
    
    // CRITICAL: Ensure modal is hidden on initialization
    mathModal.style.display = 'none';
    mathModal.style.visibility = 'hidden';
    mathModal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('math-modal-open');
    document.body.style.overflow = '';
    document.body.style.pointerEvents = '';
    
    console.log('Modal properly hidden on initialization');
    
    setupEventListeners();
    return true;
}

/**
 * Populate Comprehensive Symbol Toolbar with Categories
 */
function populateSymbolToolbar() {
    console.log('Populating symbol toolbar...');
    
    const toolbar = document.getElementById('math-symbol-toolbar');
    if (!toolbar) {
        console.error('Math toolbar element not found');
        return;
    }
    
    toolbar.innerHTML = '';
    
    try {
        let totalButtons = 0;
        
        Object.keys(mathSymbols).forEach(category => {
            console.log(`Adding category: ${category} with ${mathSymbols[category].length} symbols`);
            
            const section = document.createElement('div');
            section.className = 'math-toolbar-section';
            
            const label = document.createElement('span');
            label.className = 'math-toolbar-label';
            label.textContent = category;
            section.appendChild(label);
            
            mathSymbols[category].forEach(symbol => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'math-symbol-btn';
                btn.setAttribute('data-symbol', symbol);
                
                // For special symbols, show them directly, otherwise use LaTeX rendering
                const simpleSymbols = ['+', '-', '=', '<', '>', '\\times', '\\div', '\\pm', '\\mp'];
                if (simpleSymbols.includes(symbol)) {
                    const displaySymbol = symbol.replace('\\times', '×').replace('\\div', '÷').replace('\\pm', '±').replace('\\mp', '∓');
                    btn.textContent = displaySymbol;
                } else {
                    // Use a more readable format for LaTeX symbols
                    const displayText = symbol.replace('\\', '').replace('{', '').replace('}', '');
                    btn.innerHTML = `<span style="font-family: serif; font-size: 12px;">${displayText}</span>`;
                }
                
                btn.title = `Insert ${symbol}`;
                
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log(`Inserting symbol: ${symbol}`);
                    insertSymbol(symbol);
                });
                
                section.appendChild(btn);
                totalButtons++;
            });
            
            toolbar.appendChild(section);
        });
        
        console.log(`Symbol toolbar populated successfully with ${totalButtons} buttons in ${Object.keys(mathSymbols).length} categories`);
        
        // Make toolbar visible
        toolbar.style.display = 'flex';
        toolbar.style.visibility = 'visible';
        
        // Optional: Render math symbols with MathJax if available
        setTimeout(() => {
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise([toolbar]).then(() => {
                    console.log('MathJax toolbar rendering complete');
                }).catch(function (err) {
                    console.log('MathJax toolbar typeset failed: ' + err.message);
                });
            }
        }, 100);
        
    } catch (error) {
        console.error('Error populating toolbar:', error);
        toolbar.innerHTML = '<div style="padding: 10px; color: red;">Error loading symbols. Please refresh and try again.</div>';
    }
}

/**
 * FIXED Quill Formula Handler Override - Focus on the core issue
 */
function overrideQuillFormulaHandler(questionEditor) {
    console.log('🔧 Setting up Quill formula handler...');
    
    if (!questionEditor) {
        console.error('❌ No Quill editor provided');
        return false;
    }
    
    // DIRECT APPROACH: Find the formula button and override its click
    setTimeout(() => {
        const formulaButton = document.querySelector('.ql-formula');
        console.log('🔍 Looking for formula button...', !!formulaButton);
        
        if (formulaButton) {
            console.log('✅ Found formula button, overriding click...');
            
            // Remove any existing click listeners
            const newButton = formulaButton.cloneNode(true);
            formulaButton.parentNode.replaceChild(newButton, formulaButton);
            
            // Add our custom click handler
            newButton.addEventListener('click', function(e) {
                console.log('🎯 FORMULA BUTTON CLICKED - OPENING MODAL');
                e.preventDefault();
                e.stopPropagation();
                
                // Store editor reference
                currentQuillEditor = questionEditor;
                storedCursorPosition = 0;
                
                // Open modal
                openMathModal();
            });
            
            console.log('✅ Formula button override complete');
            return true;
        } else {
            console.error('❌ Could not find formula button');
            return false;
        }
    }, 500);
    
    return true;
}

/**
 * FIXED Modal Opening - Focus on making it work
 */
function openMathModal() {
    console.log('🎯 OPENING MATH MODAL - START');
    
    // EMERGENCY FIX: Force find modal if not found
    if (!mathModal) {
        console.log('🔍 Modal not found, searching...');
        mathModal = document.getElementById('math-equation-modal');
        if (!mathModal) {
            console.error('❌ CRITICAL: Cannot find math modal element');
            alert('Math modal not found. Please refresh the page.');
            return false;
        }
    }
    
    console.log('✅ Modal element found');
    
    // STEP 1: Hide debug toolbar immediately
    const debugToolbar = document.getElementById('djDebug');
    if (debugToolbar) {
        debugToolbar.style.display = 'none';
    }
    
    // STEP 2: Set body state for modal
    document.body.classList.add('math-modal-open');
    document.body.style.overflow = 'hidden';
    console.log('✅ Body state set');
    
    // STEP 3: Force modal visible with maximum priority
    mathModal.classList.add('math-modal-shown');
    mathModal.style.cssText = `
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important;
        background: rgba(0, 0, 0, 0.5) !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 20px !important;
        box-sizing: border-box !important;
    `;
    
    console.log('✅ Modal forced visible');
    
    // STEP 4: Set ARIA attributes
    mathModal.setAttribute('aria-hidden', 'false');
    mathModal.setAttribute('role', 'dialog');
    mathModal.setAttribute('aria-modal', 'true');
    
    // STEP 5: Initialize content (with error handling)
    try {
        // Clear and setup input
        if (mathLatexInput) {
            mathLatexInput.value = '';
        }
        
        // Clear preview
        if (mathPreviewPane) {
            mathPreviewPane.innerHTML = '<div class="math-preview-empty">Enter LaTeX equation to see preview</div>';
        }
        
        // Populate symbols
        populateSymbolToolbar();
        console.log('✅ Content initialized');
        
    } catch (initError) {
        console.error('⚠️ Content initialization failed:', initError);
        // Continue anyway - modal should still be usable
    }
    
    // STEP 6: Setup event listeners
    setupEventListeners();
    
    console.log('🎉 MODAL OPENED SUCCESSFULLY');
    return true;
}

/**
 * Initialize modal state with enterprise-grade validation
 */
function initializeModalState() {
    try {
        // Reset input with validation
        if (mathLatexInput && typeof mathLatexInput.value !== 'undefined') {
            mathLatexInput.value = '';
            mathLatexInput.setAttribute('aria-describedby', 'math-status-text');
        }
        
        // Reset preview pane with accessibility
        if (mathPreviewPane) {
            mathPreviewPane.innerHTML = '<div class="math-preview-empty" role="status" aria-live="polite">Enter LaTeX equation to see preview</div>';
            mathPreviewPane.setAttribute('aria-label', 'Mathematical equation preview');
        }
        
        // Update status with validation
        if (typeof updateStatus === 'function') {
            updateStatus('Ready for mathematical input', 'neutral');
        }
        
        // Focus management with accessibility
        setTimeout(() => {
            if (mathLatexInput && typeof mathLatexInput.focus === 'function') {
                mathLatexInput.focus();
                mathLatexInput.setAttribute('aria-label', 'Enter mathematical equation using LaTeX syntax');
            }
        }, 150); // Allow for animation completion
        
    } catch (error) {
        console.error('Modal state initialization error:', error);
    }
}

/**
 * Setup keyboard navigation following Google accessibility standards
 */
function setupModalKeyboardNavigation() {
    // Remove existing listener to prevent duplicates
    document.removeEventListener('keydown', modalKeydownHandler);
    document.addEventListener('keydown', modalKeydownHandler);
}

/**
 * Enterprise-grade keyboard event handler
 */
function modalKeydownHandler(event) {
    if (!mathModal || mathModal.style.display === 'none') return;
    
    switch (event.key) {
        case 'Escape':
            event.preventDefault();
            closeMathModal();
            break;
        case 'Tab':
            // Trap focus within modal
            trapFocusInModal(event);
            break;
    }
}

/**
 * Focus trap implementation for accessibility
 */
function trapFocusInModal(event) {
    const focusableElements = mathModal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (event.shiftKey) {
        if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
        }
    } else {
        if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
        }
    }
}

/**
 * FIXED Modal Closing - Restore page functionality
 */
function closeMathModal() {
    console.log('🔒 CLOSING MATH MODAL');
    
    // STEP 1: Immediately restore page functionality
    document.body.classList.remove('math-modal-open');
    document.body.style.overflow = '';
    document.body.style.pointerEvents = '';
    console.log('✅ Page functionality restored');
    
    // STEP 2: Hide modal
    if (mathModal) {
        mathModal.classList.remove('math-modal-shown');
        mathModal.style.display = 'none';
        mathModal.style.visibility = 'hidden';
        mathModal.style.opacity = '0';
        mathModal.style.pointerEvents = 'none';
        
        // Reset ARIA
        mathModal.setAttribute('aria-hidden', 'true');
        mathModal.removeAttribute('role');
        mathModal.removeAttribute('aria-modal');
        
        console.log('✅ Modal hidden');
    }
    
    // STEP 3: Restore debug toolbar
    const debugToolbar = document.getElementById('djDebug');
    if (debugToolbar) {
        debugToolbar.style.display = '';
        debugToolbar.style.zIndex = '';
    }
    
    // STEP 4: Clean up event listeners
    document.removeEventListener('keydown', modalKeydownHandler);
    
    // STEP 5: Reset variables
    currentQuillEditor = null;
    storedCursorPosition = null;
    window.mathModalOpening = false;
    
    console.log('🎉 MODAL CLOSED - PAGE RESTORED');
}

/**
 * Insert Symbol into LaTeX Input
 */
function insertSymbol(symbol) {
    if (!mathLatexInput) return;
    
    const cursorPos = mathLatexInput.selectionStart;
    const currentValue = mathLatexInput.value;
    const newValue = currentValue.substring(0, cursorPos) + symbol + currentValue.substring(mathLatexInput.selectionEnd);
    
    mathLatexInput.value = newValue;
    mathLatexInput.focus();
    mathLatexInput.setSelectionRange(cursorPos + symbol.length, cursorPos + symbol.length);
    
    // Update preview after inserting symbol
    updatePreview();
}

/**
 * Update Live Preview with MathJax rendering
 */
function updatePreview() {
    const latex = mathLatexInput.value.trim();
    
    if (!latex) {
        mathPreviewPane.innerHTML = '<div class="math-preview-empty">Enter LaTeX equation to see preview</div>';
        updateStatus('Ready for mathematical input', 'neutral');
        return;
    }
    
    try {
        // Wrap latex in display math delimiters
        const displayLatex = `$$${latex}$$`;
        mathPreviewPane.innerHTML = displayLatex;
        
        if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([mathPreviewPane]).then(() => {
                updateStatus('Equation rendered successfully', 'valid');
            }).catch((err) => {
                mathPreviewPane.innerHTML = `<div class="text-red-600 text-sm">Error: ${err.message}</div>`;
                updateStatus('LaTeX syntax error', 'invalid');
            });
        } else {
            updateStatus('MathJax not loaded', 'invalid');
        }
    } catch (error) {
        mathPreviewPane.innerHTML = `<div class="text-red-600 text-sm">Error: ${error.message}</div>`;
        updateStatus('LaTeX syntax error', 'invalid');
    }
}

/**
 * Update Status Display with Visual Indicators
 */
function updateStatus(message, type) {
    if (mathStatusText) {
        mathStatusText.textContent = message;
    }
    if (mathStatus) {
        mathStatus.className = `math-status ${type}`;
    }
}

/**
 * Insert Equation into Quill Editor with Smart Positioning and Fallbacks
 */
function insertEquation() {
    const latex = mathLatexInput.value.trim();
    
    if (!latex) {
        alert('Please enter a LaTeX equation');
        return;
    }
    
    if (!currentQuillEditor) {
        alert('Error: Editor not available. Please try refreshing the page.');
        closeMathModal();
        return;
    }
    
    // Get current editor state and validate position
    currentQuillEditor.focus();
    const currentLength = currentQuillEditor.getLength();
    console.log('Current editor length:', currentLength);
    console.log('Stored cursor position:', storedCursorPosition);
    
    // Use fresh selection if stored position is invalid
    let insertPosition = storedCursorPosition;
    if (insertPosition === null || insertPosition > currentLength) {
        const currentSelection = currentQuillEditor.getSelection();
        insertPosition = currentSelection ? currentSelection.index : Math.max(0, currentLength - 1);
        console.log('Using fresh selection position:', insertPosition);
    }
    
    // Ensure position is within bounds
    insertPosition = Math.min(Math.max(0, insertPosition), currentLength);
    console.log('Final insert position:', insertPosition);
    
    // Use special text markers that Quill won't strip
    const mathText = ` [EQUATION:${latex}] `;
    let inserted = false;
    
    // Method 1: Simple text insertion with special markers
    try {
        currentQuillEditor.insertText(insertPosition, mathText, 'user');
        
        // Set cursor after inserted content
        setTimeout(() => {
            try {
                const newPosition = Math.min(insertPosition + mathText.length, currentQuillEditor.getLength());
                currentQuillEditor.setSelection(newPosition, 0, 'user');
            } catch (selectionError) {
                console.log('Selection setting failed, but text was inserted');
            }
        }, 50);
        
        inserted = true;
        console.log('Text insertion successful at position:', insertPosition);
        
    } catch (error) {
        console.log('Text method failed:', error.message, 'trying fallback...');
        
        // Method 2: Fallback to dollar format
        try {
            const dollarText = ` $$${latex}$$ `;
            currentQuillEditor.insertText(insertPosition, dollarText, 'user');
            
            setTimeout(() => {
                try {
                    const newPos = Math.min(insertPosition + dollarText.length, currentQuillEditor.getLength());
                    currentQuillEditor.setSelection(newPos, 0, 'user');
                } catch (selErr) {
                    console.log('Selection failed but text inserted');
                }
            }, 50);
            
            inserted = true;
            console.log('Dollar format fallback successful');
            
        } catch (dollarError) {
            alert('Unable to insert equation. Please type it manually: $$' + latex + '$$');
        }
    }
    
    if (inserted) {
        // Update the hidden textarea (this needs to be passed from template)
        const hiddenTextarea = document.getElementById(window.mathModalConfig?.hiddenTextareaId);
        if (hiddenTextarea) {
            hiddenTextarea.value = currentQuillEditor.root.innerHTML;
        }
        
        // Style the equation markers in the editor
        setTimeout(() => {
            styleEquationMarkers();
        }, 100);
        
        console.log('Equation inserted successfully:', mathText);
    }
    
    // Clear stored position
    storedCursorPosition = null;
    closeMathModal();
}

/**
 * Style equation markers in the editor - for visual enhancement
 */
function styleEquationMarkers() {
    // Enhanced equation styling for better visual presentation
    console.log('Styling equation markers for better visual presentation');
    
    // This function can be expanded to add visual styling to equation markers
    // For now, we keep equations as text markers to avoid Quill sanitization issues
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    console.log('Setting up math modal event listeners...');
    
    const closeMathBtn = document.getElementById('close-math-modal');
    const cancelMathBtn = document.getElementById('cancel-math-input');
    const clearMathBtn = document.getElementById('clear-math-input');
    const insertMathBtn = document.getElementById('insert-math-equation');
    
    console.log('Button elements found:', {
        closeMathBtn: !!closeMathBtn,
        cancelMathBtn: !!cancelMathBtn,
        clearMathBtn: !!clearMathBtn,
        insertMathBtn: !!insertMathBtn
    });
    
    if (closeMathBtn) {
        closeMathBtn.addEventListener('click', function(e) {
            console.log('Close button clicked');
            e.preventDefault();
            closeMathModal();
        });
    }
    
    if (cancelMathBtn) {
        cancelMathBtn.addEventListener('click', function(e) {
            console.log('Cancel button clicked');
            e.preventDefault();
            closeMathModal();
        });
    }
    
    if (clearMathBtn) {
        clearMathBtn.addEventListener('click', function(e) {
            console.log('Clear button clicked');
            e.preventDefault();
            if (mathLatexInput) mathLatexInput.value = '';
            if (mathPreviewPane) mathPreviewPane.innerHTML = '<div class="math-preview-empty">Enter LaTeX equation to see preview</div>';
            updateStatus('Ready for mathematical input', 'neutral');
            if (mathLatexInput) mathLatexInput.focus();
        });
    }
    
    if (insertMathBtn) {
        insertMathBtn.addEventListener('click', function(e) {
            console.log('Insert button clicked');
            e.preventDefault();
            insertEquation();
        });
    }
    
    // Live Preview Updates with Enhanced Keyboard Support
    if (mathLatexInput) {
        mathLatexInput.addEventListener('input', updatePreview);
        mathLatexInput.addEventListener('keydown', function(e) {
            // Ctrl+Enter to insert equation
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                insertEquation();
            }
            // Escape to cancel
            if (e.key === 'Escape') {
                closeMathModal();
            }
        });
    }
    
    // Close modal when clicking outside
    if (mathModal) {
        mathModal.addEventListener('click', function(e) {
            if (e.target === mathModal) {
                console.log('Clicked outside modal, closing...');
                closeMathModal();
            }
        });
    }
}


// Export functions for global access
window.MathEquationModal = {
    initialize: initializeMathEquationPanel,
    overrideQuillHandler: overrideQuillFormulaHandler,
    openModal: openMathModal,
    closeModal: closeMathModal,
    populateToolbar: populateSymbolToolbar,
    insertSymbol: insertSymbol,
    updatePreview: updatePreview,
    insertEquation: insertEquation
};

// Global debug function
window.debugMathModalState = function() {
    console.log('=== Math Modal Global State ===');
    console.log('currentQuillEditor:', !!currentQuillEditor);
    console.log('storedCursorPosition:', storedCursorPosition);
    console.log('mathModal exists:', !!mathModal);
    console.log('mathModalOpening flag:', window.mathModalOpening);
    
    if (mathModal) {
        console.log('Modal display:', mathModal.style.display);
        console.log('Modal visibility:', mathModal.style.visibility);
        console.log('Modal has show class:', mathModal.classList.contains('math-modal-shown'));
    }
    
    console.log('Body has modal-open class:', document.body.classList.contains('math-modal-open'));
    console.log('=== End State Debug ===');
};

console.log('🚀 Math Equation Modal JavaScript loaded successfully');
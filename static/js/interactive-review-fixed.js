// Fixed Interactive PDF Reviewer
class InteractivePDFReviewer {
    constructor() {
        this.documentId = document.querySelector('[data-document-id]').dataset.documentId;
        this.currentPage = parseInt(document.querySelector('[data-current-page]').dataset.currentPage);
        this.totalPages = parseInt(document.querySelector('[data-total-pages]').dataset.totalPages);
        this.regions = [];
        this.selectedRegions = [];
        this.extractedQuestions = [];
        this.isManualSelecting = false;  // Will be toggled to true after initialization
        this.selectionStart = null;
        
        console.log('Initializing InteractivePDFReviewer with:', {
            documentId: this.documentId,
            currentPage: this.currentPage,
            totalPages: this.totalPages
        });
        
        this.initializeEventListeners();
        this.initializeGoToTopButton();
        
        // Enable manual selection by default after initialization
        setTimeout(() => {
            this.enableManualSelectionByDefault();
        }, 100);
    }
    
    initializeEventListeners() {
        console.log('Setting up event listeners...');
        
        // Manual selection button
        const manualBtn = document.getElementById('manualSelectBtn');
        if (manualBtn) {
            manualBtn.addEventListener('click', () => {
                console.log('Manual selection button clicked');
                this.toggleManualSelection();
            });
            console.log('Manual selection button listener added');
        } else {
            console.error('Manual selection button not found');
        }
        
        // Process regions button
        const processBtn = document.getElementById('processRegionsBtn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.processSelectedRegions());
        }
        
        // Clear regions button
        const clearBtn = document.getElementById('clearRegionsBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearRegions());
            console.log('Clear regions button listener added');
        } else {
            console.error('Clear regions button not found');
        }
        
        // Auto detect button
        const autoDetectBtn = document.getElementById('autoDetectBtn');
        if (autoDetectBtn) {
            autoDetectBtn.addEventListener('click', () => this.autoDetectRegions());
        }
        
        // Select all / Deselect all buttons
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllRegions());
        }
        
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAllRegions());
        }
        
        // Save questions button
        const saveQuestionsBtn = document.getElementById('saveQuestionsBtn');
        if (saveQuestionsBtn) {
            saveQuestionsBtn.addEventListener('click', () => this.saveQuestions());
            console.log('Save questions button listener added');
        } else {
            console.error('Save questions button not found');
        }
        
        // Save and finish button
        const saveAndFinishBtn = document.getElementById('saveAndFinish');
        if (saveAndFinishBtn) {
            saveAndFinishBtn.addEventListener('click', () => this.saveAndFinishReview());
        }
        
        // Page navigation buttons
        const prevPageBtn = document.getElementById('prevPage');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => this.goToPreviousPage());
            console.log('Previous page button listener added');
        }
        
        const nextPageBtn = document.getElementById('nextPage');
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => this.goToNextPage());
            console.log('Next page button listener added');
        }
        
        // Page action buttons
        const markPageCompleteBtn = document.getElementById('markPageCompleteBtn');
        if (markPageCompleteBtn) {
            markPageCompleteBtn.addEventListener('click', () => this.markPageAsComplete());
            console.log('Mark page complete button listener added');
        }
        
        const markNoQuestionsBtn = document.getElementById('markNoQuestionsBtn');
        if (markNoQuestionsBtn) {
            markNoQuestionsBtn.addEventListener('click', () => this.markPageAsNoQuestions());
            console.log('Mark page no questions button listener added');
        }
        
        const markForLaterBtn = document.getElementById('markForLaterBtn');
        if (markForLaterBtn) {
            markForLaterBtn.addEventListener('click', () => this.markPageAsUnsupported());
            console.log('Mark page unsupported button listener added');
        }
        
        // Mark selected regions as unsupported button
        const markSelectedUnsupportedBtn = document.getElementById('markSelectedUnsupportedBtn');
        if (markSelectedUnsupportedBtn) {
            markSelectedUnsupportedBtn.addEventListener('click', () => this.markSelectedRegionsAsUnsupported());
            console.log('Mark selected regions as unsupported button listener added');
        }
        
        // PDF viewer interactions
        const pdfImage = document.getElementById('pdfImage');
        if (pdfImage) {
            pdfImage.addEventListener('mousedown', (e) => this.onMouseDown(e));
            pdfImage.addEventListener('mousemove', (e) => this.onMouseMove(e));
            pdfImage.addEventListener('mouseup', (e) => this.onMouseUp(e));
            console.log('PDF image event listeners added');
        } else {
            console.error('PDF image not found');
        }
    }
    
    initializeGoToTopButton() {
        console.log('Initializing Go to Top button...');
        
        const goToTopBtn = document.getElementById('goToTopBtn');
        if (!goToTopBtn) {
            console.error('Go to Top button not found');
            return;
        }
        
        // Show/hide button based on scroll position
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (window.pageYOffset > 300) {
                    goToTopBtn.classList.remove('hidden');
                    setTimeout(() => {
                        goToTopBtn.classList.add('show');
                    }, 10);
                } else {
                    goToTopBtn.classList.remove('show');
                    setTimeout(() => {
                        goToTopBtn.classList.add('hidden');
                    }, 300);
                }
            }, 100);
        });
        
        // Scroll to top when button is clicked
        goToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        console.log('Go to Top button initialized');
    }
    
    enableManualSelectionByDefault() {
        console.log('Enabling manual selection by default...');
        
        const btn = document.getElementById('manualSelectBtn');
        const pdfImage = document.getElementById('pdfImage');
        
        if (!btn || !pdfImage) {
            console.error('Required elements not found for default manual selection:', { btn, pdfImage });
            // Retry after a short delay if elements aren't ready
            setTimeout(() => this.enableManualSelectionByDefault(), 200);
            return;
        }
        
        // Enable manual selection
        this.isManualSelecting = true;
        btn.textContent = 'Stop Manual Selection';
        btn.classList.add('btn-warning');
        btn.classList.remove('btn-secondary');
        pdfImage.style.cursor = 'crosshair';
        
        console.log('Manual selection ENABLED by default');
        console.log('Button text:', btn.textContent);
        console.log('PDF cursor:', pdfImage.style.cursor);
    }
    
    toggleManualSelection() {
        console.log('toggleManualSelection called, current state:', this.isManualSelecting);
        
        this.isManualSelecting = !this.isManualSelecting;
        const btn = document.getElementById('manualSelectBtn');
        const pdfImage = document.getElementById('pdfImage');
        
        if (!btn || !pdfImage) {
            console.error('Required elements not found:', { btn, pdfImage });
            return;
        }
        
        if (this.isManualSelecting) {
            btn.textContent = 'Stop Manual Selection';
            btn.classList.add('btn-warning');
            btn.classList.remove('btn-secondary');
            pdfImage.style.cursor = 'crosshair';
            console.log('Manual selection ENABLED');
        } else {
            btn.textContent = 'Manual Selection';
            btn.classList.remove('btn-warning');
            btn.classList.add('btn-secondary');
            pdfImage.style.cursor = 'default';
            console.log('Manual selection DISABLED');
        }
        
        console.log('Button text:', btn.textContent);
        console.log('Button classes:', btn.className);
        console.log('PDF cursor:', pdfImage.style.cursor);
    }
    
    onMouseDown(e) {
        if (!this.isManualSelecting) return;
        
        console.log('Mouse down - starting selection');
        e.preventDefault();
        const rect = e.target.getBoundingClientRect();
        this.selectionStart = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        console.log('Selection start:', this.selectionStart);
    }
    
    onMouseMove(e) {
        if (!this.isManualSelecting || !this.selectionStart) return;
        
        e.preventDefault();
        const rect = e.target.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        // Remove existing preview
        const existingPreview = document.getElementById('selectionPreview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Create selection preview
        const preview = document.createElement('div');
        preview.id = 'selectionPreview';
        preview.style.position = 'absolute';
        preview.style.left = Math.min(this.selectionStart.x, currentX) + 'px';
        preview.style.top = Math.min(this.selectionStart.y, currentY) + 'px';
        preview.style.width = Math.abs(currentX - this.selectionStart.x) + 'px';
        preview.style.height = Math.abs(currentY - this.selectionStart.y) + 'px';
        preview.style.border = '2px dashed #3b82f6';
        preview.style.background = 'rgba(59, 130, 246, 0.1)';
        preview.style.pointerEvents = 'none';
        preview.style.zIndex = '15';
        
        document.getElementById('regionOverlays').appendChild(preview);
    }
    
    onMouseUp(e) {
        if (!this.isManualSelecting || !this.selectionStart) return;
        
        console.log('Mouse up - finishing selection');
        
        // Clean up selection preview
        const existingPreview = document.getElementById('selectionPreview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        const rect = e.target.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;
        
        const coords = {
            x: Math.min(this.selectionStart.x, endX),
            y: Math.min(this.selectionStart.y, endY),
            width: Math.abs(endX - this.selectionStart.x),
            height: Math.abs(endY - this.selectionStart.y)
        };
        
        // Get scaling ratios for coordinate conversion
        const pdfImage = document.getElementById('pdfImage');
        const actualWidth = pdfImage.naturalWidth;
        const actualHeight = pdfImage.naturalHeight;
        const displayWidth = rect.width;
        const displayHeight = rect.height;
        const scaleX = actualWidth / displayWidth;
        const scaleY = actualHeight / displayHeight;
        
        const actualCoords = {
            x: Math.round(coords.x * scaleX),
            y: Math.round(coords.y * scaleY),
            width: Math.round(coords.width * scaleX),
            height: Math.round(coords.height * scaleY)
        };
        
        const region = {
            id: `manual_region_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'question',
            source: 'manual',
            coordinates: actualCoords,
            display_coordinates: coords,
            confidence: 1.0,
            text_preview: 'Manual selection',
            needs_review: false
        };
        
        // Only add if selection is large enough
        if (region.coordinates.width > 10 && region.coordinates.height > 10) {
            console.log('Adding region:', region);
            this.regions.push(region);
            this.renderRegions();
            this.updateRegionsList();
            this.updateProcessButton();
        }
        
        this.selectionStart = null;
    }
    
    renderRegions() {
        console.log('Rendering regions:', this.regions.length);
        const overlaysContainer = document.getElementById('regionOverlays');
        overlaysContainer.innerHTML = '';
        
        this.regions.forEach((region, index) => {
            const overlay = document.createElement('div');
            overlay.className = `region-overlay ${region.type}`;
            overlay.id = `region_${index}`;
            
            const coords = region.display_coordinates || region.coordinates;
            overlay.style.left = coords.x + 'px';
            overlay.style.top = coords.y + 'px';
            overlay.style.width = coords.width + 'px';
            overlay.style.height = coords.height + 'px';
            
            const label = document.createElement('div');
            label.className = 'region-label';
            label.textContent = `${region.type.toUpperCase()} ${index + 1} (${Math.round(region.confidence * 100)}%)`;
            overlay.appendChild(label);
            
            overlay.addEventListener('click', () => this.toggleRegionSelection(index));
            overlaysContainer.appendChild(overlay);
        });
    }
    
    toggleRegionSelection(regionIndex) {
        const overlay = document.getElementById(`region_${regionIndex}`);
        
        if (this.selectedRegions.includes(regionIndex)) {
            this.selectedRegions = this.selectedRegions.filter(i => i !== regionIndex);
            if (overlay) overlay.classList.remove('selected');
        } else {
            this.selectedRegions.push(regionIndex);
            if (overlay) overlay.classList.add('selected');
        }
        
        this.updateProcessButton();
        this.updateRegionsList(); // Update the checkbox states
    }
    
    updateRegionsList() {
        const container = document.getElementById('regionsList');
        const selectAllButtons = document.getElementById('selectAllButtons');
        
        if (this.regions.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No regions detected</p>';
            selectAllButtons.style.display = 'none';
            return;
        }
        
        // Show select all buttons when regions are available
        selectAllButtons.style.display = 'flex';
        
        container.innerHTML = this.regions.map((region, index) => `
            <div class="region-info ${region.type}">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-2">
                        <input type="checkbox" 
                               id="region-checkbox-${index}"
                               class="region-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                               ${this.selectedRegions.includes(index) ? 'checked' : ''}
                               onchange="reviewer.toggleRegionSelection(${index})">
                        <label for="region-checkbox-${index}" class="flex items-center cursor-pointer">
                            <span class="font-medium">${region.type.replace('_', ' ').toUpperCase()} ${index + 1}</span>
                            <span class="text-sm text-gray-600 ml-2">${Math.round(region.confidence * 100)}%</span>
                        </label>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateProcessButton() {
        const processBtn = document.getElementById('processRegionsBtn');
        const markUnsupportedBtn = document.getElementById('markSelectedUnsupportedBtn');
        const hasSelection = this.selectedRegions.length > 0;
        
        if (processBtn) {
            processBtn.disabled = !hasSelection;
            processBtn.textContent = hasSelection ? 
                `Process ${this.selectedRegions.length} Selected Region(s)` : 
                'Process & Extract Text';
                
            // Update button style based on selection
            if (hasSelection) {
                processBtn.classList.remove('btn-secondary');
                processBtn.classList.add('btn-primary');
            } else {
                processBtn.classList.remove('btn-primary');
                processBtn.classList.add('btn-secondary');
            }
        }
        
        // Also update the mark unsupported button
        if (markUnsupportedBtn) {
            markUnsupportedBtn.disabled = !hasSelection;
            if (hasSelection) {
                markUnsupportedBtn.textContent = `Mark ${this.selectedRegions.length} Selected as Unsupported`;
            } else {
                markUnsupportedBtn.textContent = 'Mark Selected as Unsupported';
            }
        }
    }
    
    clearRegions() {
        console.log('Clearing all regions...');
        
        // Confirm action
        if (this.regions.length > 0) {
            const confirmed = confirm(`Clear all ${this.regions.length} regions? This action cannot be undone.`);
            if (!confirmed) {
                console.log('Clear regions cancelled by user');
                return;
            }
        }
        
        // Clear all data
        this.regions = [];
        this.selectedRegions = [];
        this.extractedQuestions = [];
        
        // Clear visual elements
        const overlaysContainer = document.getElementById('regionOverlays');
        if (overlaysContainer) {
            overlaysContainer.innerHTML = '';
        }
        
        // Hide question editor
        const questionEditor = document.getElementById('questionEditor');
        if (questionEditor) {
            questionEditor.style.display = 'none';
        }
        
        // Update UI
        this.updateRegionsList();
        this.updateProcessButton();
        
        console.log('All regions cleared successfully');
    }
    
    selectAllRegions() {
        console.log('Selecting all regions...');
        this.selectedRegions = [...Array(this.regions.length).keys()]; // [0, 1, 2, ...]
        
        // Update visual overlays
        this.regions.forEach((region, index) => {
            const overlay = document.getElementById(`region_${index}`);
            if (overlay) overlay.classList.add('selected');
        });
        
        this.updateProcessButton();
        this.updateRegionsList();
    }
    
    deselectAllRegions() {
        console.log('Deselecting all regions...');
        this.selectedRegions = [];
        
        // Update visual overlays
        this.regions.forEach((region, index) => {
            const overlay = document.getElementById(`region_${index}`);
            if (overlay) overlay.classList.remove('selected');
        });
        
        this.updateProcessButton();
        this.updateRegionsList();
    }
    
    async autoDetectRegions() {
        console.log('Auto-detecting regions...');
        
        try {
            this.showLoading('Auto-detecting regions...');
            
            const response = await fetch(`/pdf-extractor/api/auto-detect-regions/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Auto-detect response:', data);
            
            if (data.success && data.regions) {
                // Clear existing regions first
                this.regions = [];
                this.selectedRegions = [];
                
                // Add detected regions
                this.regions = data.regions.map(region => ({
                    id: region.id || `auto_region_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    type: region.type || 'question',
                    source: 'auto_detect',
                    coordinates: region.coordinates,
                    display_coordinates: region.display_coordinates || this.convertToDisplayCoords(region.coordinates),
                    confidence: region.confidence || 0.8,
                    text_preview: region.text_preview || 'Auto-detected',
                    needs_review: true
                }));
                
                console.log('Added', this.regions.length, 'auto-detected regions');
                
                // Update UI
                this.renderRegions();
                this.updateRegionsList();
                this.updateProcessButton();
            } else {
                throw new Error(data.error || 'No regions detected');
            }
            
        } catch (error) {
            console.error('Error auto-detecting regions:', error);
            alert(`Auto-detection failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    convertToDisplayCoords(actualCoords) {
        const pdfImage = document.getElementById('pdfImage');
        if (!pdfImage) return actualCoords;
        
        const actualWidth = pdfImage.naturalWidth;
        const actualHeight = pdfImage.naturalHeight;
        const displayWidth = pdfImage.clientWidth;
        const displayHeight = pdfImage.clientHeight;
        
        if (!actualWidth || !actualHeight) return actualCoords;
        
        const scaleX = displayWidth / actualWidth;
        const scaleY = displayHeight / actualHeight;
        
        return {
            x: Math.round(actualCoords.x * scaleX),
            y: Math.round(actualCoords.y * scaleY),
            width: Math.round(actualCoords.width * scaleX),
            height: Math.round(actualCoords.height * scaleY)
        };
    }
    
    async processSelectedRegions() {
        if (this.selectedRegions.length === 0) {
            console.log('No regions selected for processing');
            alert('Please select at least one region to process');
            return;
        }
        
        console.log('Processing', this.selectedRegions.length, 'selected regions SEQUENTIALLY');
        
        try {
            // Clear previous results
            this.extractedQuestions = [];
            
            // Process each region sequentially
            const allProcessedRegions = [];
            
            for (let i = 0; i < this.selectedRegions.length; i++) {
                const regionIndex = this.selectedRegions[i];
                const region = this.regions[regionIndex];
                
                this.showLoading(`Processing region ${i + 1} of ${this.selectedRegions.length}...`);
                console.log(`Processing region ${i + 1}/${this.selectedRegions.length}:`, region);
                
                try {
                    // Process single region
                    const response = await fetch(`/pdf-extractor/api/process-regions/${this.documentId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken()
                        },
                        body: JSON.stringify({
                            page_number: this.currentPage,
                            selected_regions: [region] // Process only one region at a time
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    console.log(`Region ${i + 1} OCR response:`, data);
                    
                    if (data.success && data.processed_regions) {
                        // Add processed regions to combined results
                        allProcessedRegions.push(...data.processed_regions);
                        console.log(`Region ${i + 1} processed successfully`);
                    } else {
                        console.error(`Region ${i + 1} processing failed:`, data.error);
                        // Continue with other regions even if one fails
                    }
                    
                    // Small delay between requests to avoid overwhelming the server
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                } catch (error) {
                    console.error(`Error processing region ${i + 1}:`, error);
                    // Continue with other regions even if one fails
                }
            }
            
            console.log(`Sequential processing complete. Total processed regions: ${allProcessedRegions.length}`);
            
            if (allProcessedRegions.length > 0) {
                // Process all OCR results together
                this.showLoading('Combining results from all regions...');
                this.processOCRResults(allProcessedRegions);
                
                // Show question editor with combined results
                document.getElementById('questionEditor').style.display = 'block';
                
                console.log(`Final result: ${this.extractedQuestions.length} questions extracted from ${allProcessedRegions.length} regions`);
            } else {
                alert('No regions could be processed successfully. Please try again.');
            }
            
        } catch (error) {
            console.error('Error in sequential processing:', error);
            alert(`Processing failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    processOCRResults(processedRegions) {
        console.log('Processing OCR results:', processedRegions);
        
        const questions = [];
        
        processedRegions.forEach((region, index) => {
            console.log(`Processing region ${index}:`, region);
            console.log('- Text:', region.text);
            console.log('- Type:', region.region_type);
            console.log('- OCR Success:', region.ocr_success);
            
            if (!region.ocr_success || !region.text) {
                console.log('Skipping region due to OCR failure or empty text');
                return;
            }
            
            const text = region.text.trim();
            console.log('Full OCR text for parsing:', JSON.stringify(text));
            
            let questionText = text;
            let options = [];
            
            // CHECK FOR BACKEND PARSED DATA FIRST
            if (region.parsed_question) {
                console.log('✅ Using backend parsed question data:', region.parsed_question);
                questionText = region.parsed_question.question_text || text;
                
                if (region.parsed_question.has_options && region.parsed_question.options) {
                    options = region.parsed_question.options.map(opt => ({
                        letter: opt.letter.toUpperCase(),
                        text: opt.text
                    }));
                    console.log(`✅ Found ${options.length} parsed options from backend`);
                } else {
                    console.log('ℹ️ Backend parsing found no options, falling back to frontend parsing');
                }
            } else {
                console.log('⚠️ No backend parsed data, using frontend parsing fallback');
            }
            
            // FALLBACK: Frontend parsing (only if no backend parsed options)
            if (options.length === 0) {
            
            // Try to parse options - enhanced logic for inline options
            console.log('Attempting to parse options from text...');
            
            // Method 1: Look for pattern "Question? (a) Option1 (b) Option2 (c) Option3 (d) Option4"
            const fullInlinePattern = /\(([a-dA-D])\)\s+([^()]+?)(?=\s*\([a-dA-D]\)|$)/g;
            const fullMatches = [...text.matchAll(fullInlinePattern)];
            
            if (fullMatches.length > 0) {
                console.log('Found inline options with parentheses:', fullMatches.length);
                
                // Extract question (everything before first option)
                const firstOptionMatch = text.match(/\([a-dA-D]\)/);
                if (firstOptionMatch) {
                    const firstOptionPos = text.indexOf(firstOptionMatch[0]);
                    if (firstOptionPos > 0) {
                        questionText = text.substring(0, firstOptionPos).trim();
                        questionText = questionText.replace(/[?:]\s*$/, '').trim();
                    }
                }
                
                // Extract options
                fullMatches.forEach(match => {
                    options.push({
                        letter: match[1].toUpperCase(),
                        text: match[2].trim()
                    });
                });
                
            } else {
                // Method 2: Look for pattern "Question? OptionA (b) OptionB (c) OptionC (d) OptionD"
                console.log('No standard inline options found, trying alternative pattern...');
                
                const altPattern = /([A-Za-z][^(]*?)\s+\(([bcdBCD])\)\s+([^()]+?)(?=\s*\([bcdBCD]\)|$)/g;
                const altMatches = [...text.matchAll(altPattern)];
                
                if (altMatches.length > 0) {
                    console.log('Found alternative pattern options:', altMatches.length);
                    
                    // First option (before first (b))
                    const firstOptionText = altMatches[0][1].trim();
                    
                    // Try to separate question from first option
                    const questionMatch = text.match(/(.+\?)\s*(.+?)\s*\([bcdBCD]\)/);
                    if (questionMatch) {
                        questionText = questionMatch[1].trim();
                        options.push({ letter: 'A', text: questionMatch[2].trim() });
                    } else {
                        // Fallback: take everything before first option as question
                        const firstOptPos = text.indexOf(firstOptionText);
                        if (firstOptPos > 0) {
                            questionText = text.substring(0, firstOptPos).trim().replace(/[?:]\s*$/, '');
                        }
                        options.push({ letter: 'A', text: firstOptionText });
                    }
                    
                    // Add remaining options
                    altMatches.forEach(match => {
                        options.push({
                            letter: match[2].toUpperCase(),
                            text: match[3].trim()
                        });
                    });
                }
            }
            
            } // End of fallback frontend parsing
            
            console.log('Final parsed question text:', questionText);
            console.log('Final parsed options:', options);
            console.log(`Data source: ${region.parsed_question ? 'Backend' : 'Frontend fallback'}`);
            
            // Create question object
            const currentQuestion = {
                id: `question_${questions.length + 1}`,
                question_text: questionText,
                question_type: 'mcq',
                answer_options: options,
                correct_answers: [],
                confidence: region.confidence || 0,
                region_coordinates: region.coordinates
            };
            
            questions.push(currentQuestion);
            console.log('Added question:', currentQuestion);
        });
        
        console.log('Final extracted questions:', questions);
        this.extractedQuestions = questions;
        this.renderQuestionEditor();
    }
    
    showLoading(message = 'Processing...') {
        console.log('Showing loading:', message);
        // Create or update loading overlay
        let loadingOverlay = document.getElementById('loadingOverlay');
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'loadingOverlay';
            loadingOverlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.5); z-index: 9999;
                display: flex; justify-content: center; align-items: center;
                color: white; font-size: 18px;
            `;
            document.body.appendChild(loadingOverlay);
        }
        loadingOverlay.innerHTML = `<div>${message}</div>`;
        loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }
    
    renderQuestionEditor() {
        const container = document.getElementById('questionsContainer');
        
        console.log('Rendering question editor with', this.extractedQuestions.length, 'questions');
        
        if (this.extractedQuestions.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No questions extracted. Please try selecting regions again or adjusting the selection.</p>';
            return;
        }
        
        container.innerHTML = this.extractedQuestions.map((question, qIndex) => {
            const hasOptions = question.answer_options && question.answer_options.length > 0;
            
            return `
            <div class="question-editor" data-question-index="${qIndex}">
                <h4 class="font-medium mb-2">Question ${qIndex + 1} (Confidence: ${Math.round(question.confidence)}%)</h4>
                
                <div class="mb-3">
                    <label class="block text-sm font-medium mb-1">Question Text:</label>
                    <textarea class="w-full p-2 border border-gray-300 rounded" 
                              rows="3" 
                              onchange="reviewer.updateQuestion(${qIndex}, 'question_text', this.value)">${question.question_text || ''}</textarea>
                </div>
                
                <div class="mb-3">
                    <label class="block text-sm font-medium mb-1">Question Type:</label>
                    <select class="w-full p-2 border border-gray-300 rounded" 
                            onchange="reviewer.updateQuestion(${qIndex}, 'question_type', this.value)">
                        <option value="mcq" ${question.question_type === 'mcq' ? 'selected' : ''}>Multiple Choice</option>
                        <option value="multi_select" ${question.question_type === 'multi_select' ? 'selected' : ''}>Multiple Select</option>
                        <option value="true_false" ${question.question_type === 'true_false' ? 'selected' : ''}>True/False</option>
                        <option value="short_answer" ${question.question_type === 'short_answer' ? 'selected' : ''}>Short Answer</option>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label class="block text-sm font-medium mb-1">Answer Options (${hasOptions ? question.answer_options.length : 0} found):</label>
                    ${hasOptions ? question.answer_options.map((option, oIndex) => `
                        <div class="option-input flex items-center mb-2">
                            <span class="option-letter font-bold mr-2 w-8">${option.letter})</span>
                            <input type="text" 
                                   class="flex-1 p-2 border border-gray-300 rounded mr-2" 
                                   value="${option.text || ''}" 
                                   onchange="reviewer.updateAnswerOption(${qIndex}, ${oIndex}, this.value)"
                                   placeholder="Option text">
                            <input type="checkbox" 
                                   class="ml-2" 
                                   ${question.correct_answers && question.correct_answers.includes(option.letter) ? 'checked' : ''}
                                   onchange="reviewer.toggleCorrectAnswer(${qIndex}, '${option.letter}', this.checked)">
                            <label class="text-sm ml-1">Correct</label>
                        </div>
                    `).join('') : '<p class="text-sm text-gray-500 italic">No options detected from OCR. You may need to add them manually or re-select the region with better coverage.</p>'}
                    <button class="btn btn-sm btn-outline mt-2" onclick="reviewer.addOption(${qIndex})">Add Option</button>
                </div>
                
                <div class="text-xs text-gray-400 mt-2">
                    Raw OCR text: "${question.question_text ? question.question_text.substring(0, 100) : 'No text'}${question.question_text && question.question_text.length > 100 ? '...' : ''}"
                </div>
            </div>
        `}).join('');
        
        console.log('Question editor rendered successfully');
    }
    
    updateQuestion(questionIndex, field, value) {
        if (this.extractedQuestions[questionIndex]) {
            this.extractedQuestions[questionIndex][field] = value;
            console.log(`Updated question ${questionIndex} ${field}:`, value);
        }
    }
    
    updateAnswerOption(questionIndex, optionIndex, value) {
        if (this.extractedQuestions[questionIndex] && 
            this.extractedQuestions[questionIndex].answer_options &&
            this.extractedQuestions[questionIndex].answer_options[optionIndex]) {
            this.extractedQuestions[questionIndex].answer_options[optionIndex].text = value;
            console.log(`Updated question ${questionIndex} option ${optionIndex}:`, value);
        }
    }
    
    toggleCorrectAnswer(questionIndex, letter, isCorrect) {
        const question = this.extractedQuestions[questionIndex];
        if (!question) return;
        
        if (!question.correct_answers) {
            question.correct_answers = [];
        }
        
        if (isCorrect) {
            if (!question.correct_answers.includes(letter)) {
                question.correct_answers.push(letter);
            }
        } else {
            question.correct_answers = question.correct_answers.filter(l => l !== letter);
        }
        
        console.log(`Question ${questionIndex} correct answers:`, question.correct_answers);
    }
    
    addOption(questionIndex) {
        const question = this.extractedQuestions[questionIndex];
        if (!question) return;
        
        if (!question.answer_options) {
            question.answer_options = [];
        }
        
        // Determine next letter
        const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
        const nextLetter = letters[question.answer_options.length] || 'Z';
        
        question.answer_options.push({
            letter: nextLetter,
            text: ''
        });
        
        console.log(`Added option ${nextLetter} to question ${questionIndex}`);
        
        // Re-render the editor
        this.renderQuestionEditor();
    }
    
    async saveQuestions() {
        console.log('Saving questions for this page...');
        
        if (this.extractedQuestions.length === 0) {
            alert('No questions to save. Please extract questions first.');
            return;
        }
        
        try {
            this.showLoading('Saving questions...');
            
            console.log('Questions to save:', this.extractedQuestions);
            
            const response = await fetch(`/pdf-extractor/api/save-questions/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage,
                    questions: this.extractedQuestions
                })
            });
            
            console.log('Save questions response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Save questions response data:', data);
            
            if (data.success) {
                alert(`Successfully saved ${this.extractedQuestions.length} question(s) for this page!`);
                console.log('Questions saved successfully');
                
                // Optionally clear the questions after saving
                // this.extractedQuestions = [];
                // document.getElementById('questionEditor').style.display = 'none';
            } else {
                throw new Error(data.error || 'Failed to save questions');
            }
            
        } catch (error) {
            console.error('Error saving questions:', error);
            alert(`Failed to save questions: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async saveAndFinishReview() {
        console.log('Saving questions and finishing review...');
        
        try {
            // First save the questions
            await this.saveQuestions();
            
            // Then mark the page as complete
            this.showLoading('Finishing review...');
            
            const response = await fetch(`/pdf-extractor/api/finish-review/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Finish review response:', data);
            
            if (data.success) {
                alert('Page review completed successfully!');
                // Optionally redirect to next page or document list
                if (data.next_page_url) {
                    window.location.href = data.next_page_url;
                } else {
                    // Reload current page or go back to document list
                    window.location.reload();
                }
            } else {
                throw new Error(data.error || 'Failed to finish review');
            }
            
        } catch (error) {
            console.error('Error finishing review:', error);
            alert(`Failed to finish review: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    goToPreviousPage() {
        console.log('Going to previous page...');
        if (this.currentPage > 1) {
            console.log(`Navigating from page ${this.currentPage} to ${this.currentPage - 1}`);
            window.location.href = `?page=${this.currentPage - 1}`;
        } else {
            console.log('Already on first page, cannot go to previous');
            alert('You are already on the first page');
        }
    }
    
    goToNextPage() {
        console.log('Going to next page...');
        if (this.currentPage < this.totalPages) {
            console.log(`Navigating from page ${this.currentPage} to ${this.currentPage + 1}`);
            window.location.href = `?page=${this.currentPage + 1}`;
        } else {
            console.log('Already on last page, cannot go to next');
            alert('You are already on the last page');
        }
    }
    
    async markPageAsComplete() {
        console.log('Marking page as complete...');
        
        const confirmed = confirm(`Mark page ${this.currentPage} as complete? This will indicate that all questions on this page have been processed.`);
        if (!confirmed) {
            console.log('Mark page complete cancelled by user');
            return;
        }
        
        try {
            this.showLoading('Marking page as complete...');
            
            const response = await fetch(`/pdf-extractor/api/mark-page-complete/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage,
                    status: 'completed'
                })
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                console.log('Page marked as complete successfully');
                alert('Page marked as complete successfully!');
                // Optionally go to next page
                if (this.currentPage < this.totalPages) {
                    window.location.href = `?page=${this.currentPage + 1}`;
                }
            } else {
                console.error('Failed to mark page as complete:', data.error);
                alert('Failed to mark page as complete: ' + data.error);
            }
            
        } catch (error) {
            this.hideLoading();
            console.error('Error marking page as complete:', error);
            alert('Error marking page as complete. Please try again.');
        }
    }
    
    async markPageAsNoQuestions() {
        console.log('Marking page as having no questions...');
        
        const confirmed = confirm(`Mark page ${this.currentPage} as having no questions? This will indicate that this page contains no question content.`);
        if (!confirmed) {
            console.log('Mark page no questions cancelled by user');
            return;
        }
        
        try {
            this.showLoading('Marking page as no questions...');
            
            const response = await fetch(`/pdf-extractor/api/mark-page-no-questions/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage,
                    status: 'no_questions'
                })
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                console.log('Page marked as no questions successfully');
                alert('Page marked as having no questions!');
                // Go to next page
                if (this.currentPage < this.totalPages) {
                    window.location.href = `?page=${this.currentPage + 1}`;
                }
            } else {
                console.error('Failed to mark page as no questions:', data.error);
                alert('Failed to mark page as no questions: ' + data.error);
            }
            
        } catch (error) {
            this.hideLoading();
            console.error('Error marking page as no questions:', error);
            alert('Error marking page as no questions. Please try again.');
        }
    }
    
    async markPageAsUnsupported() {
        console.log('Marking entire page as unsupported...');
        
        const comment = prompt(`Mark entire page ${this.currentPage} as unsupported.\n\nPlease provide a reason or comment:`, 'Complex formatting or unsupported question type');
        if (!comment) {
            console.log('Mark page unsupported cancelled by user');
            return;
        }
        
        try {
            this.showLoading('Marking page as unsupported...');
            
            const response = await fetch(`/pdf-extractor/api/mark-page-for-later/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage,
                    status: 'pending_unsupported',
                    comment: comment
                })
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                console.log('Page marked as unsupported successfully');
                alert('Page marked as unsupported for later review!');
                // Go to next page
                if (this.currentPage < this.totalPages) {
                    window.location.href = `?page=${this.currentPage + 1}`;
                }
            } else {
                console.error('Failed to mark page as unsupported:', data.error);
                alert('Failed to mark page as unsupported: ' + data.error);
            }
            
        } catch (error) {
            this.hideLoading();
            console.error('Error marking page as unsupported:', error);
            alert('Error marking page as unsupported. Please try again.');
        }
    }
    
    async markSelectedRegionsAsUnsupported() {
        console.log('Marking selected regions as unsupported...');
        
        // Get selected regions
        const selectedRegions = this.getSelectedRegions();
        
        if (selectedRegions.length === 0) {
            alert('Please select at least one region to mark as unsupported.');
            return;
        }
        
        const notes = prompt(`Mark ${selectedRegions.length} selected region(s) as unsupported.\n\nPlease provide a reason or comment:`, 'Complex formatting or unsupported question type');
        if (!notes) {
            console.log('Mark regions unsupported cancelled by user');
            return;
        }
        
        try {
            this.showLoading('Marking selected regions as unsupported...');
            
            const response = await fetch(`/pdf-extractor/api/mark-regions-unsupported/${this.documentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage,
                    regions: selectedRegions.map(region => ({
                        coordinates: region.coordinates,
                        region_type: region.type || 'question'
                    })),
                    notes: notes
                })
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                console.log('Regions marked as unsupported successfully');
                alert(`${selectedRegions.length} region(s) marked as unsupported for later review!`);
                
                // Update UI to reflect the status change
                selectedRegions.forEach(region => {
                    const overlay = region.element;
                    if (overlay) {
                        overlay.style.borderColor = '#f59e0b';
                        overlay.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
                        overlay.classList.add('unsupported');
                    }
                });
                
                // Clear selection
                this.deselectAllRegions();
                
                // Optionally move to next page if all regions are handled
                if (confirm('Move to the next page?')) {
                    this.goToNextPage();
                }
            } else {
                console.error('Failed to mark regions as unsupported:', data.error);
                alert('Failed to mark regions as unsupported: ' + data.error);
            }
            
        } catch (error) {
            this.hideLoading();
            console.error('Error marking regions as unsupported:', error);
            alert('Error marking regions as unsupported. Please try again.');
        }
    }
    
    getSelectedRegions() {
        // Get selected regions based on selectedRegions indices
        const selectedRegionData = [];
        
        this.selectedRegions.forEach(regionIndex => {
            if (this.regions[regionIndex]) {
                const region = this.regions[regionIndex];
                selectedRegionData.push({
                    coordinates: region.coordinates,
                    type: region.type || 'question',
                    element: document.getElementById(`region_${regionIndex}`)
                });
            }
        });
        
        return selectedRegionData;
    }
}

// Initialize when DOM is loaded
let reviewer;
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing fixed reviewer...');
    try {
        reviewer = new InteractivePDFReviewer();
        console.log('Fixed reviewer initialized successfully');
        
        // Test function for console
        window.testManualSelection = function() {
            console.log('Testing manual selection...');
            reviewer.toggleManualSelection();
        };
        
    } catch (error) {
        console.error('Error initializing fixed reviewer:', error);
    }
});
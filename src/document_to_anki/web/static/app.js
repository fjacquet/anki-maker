/**
 * Document to Anki Converter - Frontend JavaScript
 * Enhanced functionality for drag-and-drop, real-time updates, and accessibility
 */

class DocumentToAnkiApp {
    constructor() {
        this.currentSessionId = null;
        this.processingInterval = null;
        this.flashcards = [];
        this.currentEditingId = null;
        this.uploadQueue = [];
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccessibility();
        this.setupKeyboardShortcuts();
        this.checkBrowserSupport();
    }

    setupEventListeners() {
        // File input and drag-drop
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        
        fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));
        uploadArea?.addEventListener('click', () => fileInput?.click());
        uploadArea?.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadArea?.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadArea?.addEventListener('drop', (e) => this.handleDrop(e));

        // Form submissions
        document.getElementById('editForm')?.addEventListener('submit', (e) => this.handleEditSubmit(e));
        document.getElementById('addForm')?.addEventListener('submit', (e) => this.handleAddSubmit(e));

        // Modal handling
        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
        
        // Click outside modal to close
        document.getElementById('editModal')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeEditModal();
        });
        document.getElementById('addModal')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeAddModal();
        });

        // Keyboard accessibility for upload area
        uploadArea?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput?.click();
            }
        });

        // Auto-save for forms (draft functionality)
        this.setupAutoSave();
    }

    setupAccessibility() {
        // Add skip link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);

        // Announce page load
        this.announceToScreenReader('Document to Anki Converter loaded. Upload your documents to get started.');
        
        // Set up live regions
        this.setupLiveRegions();
    }

    setupLiveRegions() {
        // Create live region for announcements
        const liveRegion = document.createElement('div');
        liveRegion.id = 'live-announcements';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        document.body.appendChild(liveRegion);
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + U: Upload files
            if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
                e.preventDefault();
                document.getElementById('fileInput')?.click();
            }
            
            // Ctrl/Cmd + E: Export flashcards
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                if (this.flashcards.length > 0) {
                    this.exportFlashcards();
                }
            }
            
            // Ctrl/Cmd + N: Add new flashcard
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                if (this.currentSessionId) {
                    this.showAddFlashcardModal();
                }
            }
        });
    }

    setupAutoSave() {
        // Auto-save form data to localStorage
        const forms = ['editForm', 'addForm'];
        forms.forEach(formId => {
            const form = document.getElementById(formId);
            if (form) {
                const inputs = form.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    input.addEventListener('input', () => {
                        this.saveFormData(formId);
                    });
                });
            }
        });
    }

    saveFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        localStorage.setItem(`${formId}_draft`, JSON.stringify(data));
    }

    loadFormData(formId) {
        const savedData = localStorage.getItem(`${formId}_draft`);
        if (!savedData) return;

        try {
            const data = JSON.parse(savedData);
            const form = document.getElementById(formId);
            if (!form) return;

            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key];
                }
            });
        } catch (e) {
            console.warn('Failed to load form data:', e);
        }
    }

    clearFormData(formId) {
        localStorage.removeItem(`${formId}_draft`);
    }

    checkBrowserSupport() {
        // Check for required features
        const requiredFeatures = [
            'fetch',
            'FormData',
            'FileReader',
            'localStorage'
        ];

        const unsupported = requiredFeatures.filter(feature => !(feature in window));
        
        if (unsupported.length > 0) {
            this.showGlobalMessage(
                `Your browser doesn't support some required features: ${unsupported.join(', ')}. Please update your browser for the best experience.`,
                'warning'
            );
        }
    }

    announceToScreenReader(message) {
        const liveRegion = document.getElementById('live-announcements');
        if (liveRegion) {
            liveRegion.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
        
        // Show visual feedback
        const uploadIcon = e.currentTarget.querySelector('.upload-icon');
        if (uploadIcon) {
            uploadIcon.textContent = '📁';
        }
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Only remove dragover if we're actually leaving the upload area
        if (!e.currentTarget.contains(e.relatedTarget)) {
            e.currentTarget.classList.remove('dragover');
            
            const uploadIcon = e.currentTarget.querySelector('.upload-icon');
            if (uploadIcon) {
                uploadIcon.textContent = '📄';
            }
        }
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
        
        const uploadIcon = e.currentTarget.querySelector('.upload-icon');
        if (uploadIcon) {
            uploadIcon.textContent = '📄';
        }
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            this.uploadFiles(files);
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            this.uploadFiles(files);
        }
    }

    async uploadFiles(files) {
        if (this.isProcessing) {
            this.showGlobalMessage('Please wait for the current upload to complete.', 'warning');
            return;
        }

        // Validate files
        const validation = this.validateFiles(files);
        if (!validation.valid) {
            this.showGlobalMessage(validation.message, 'error');
            return;
        }

        this.isProcessing = true;
        
        try {
            // Show progress section
            this.showSection('progressSection');
            this.updateProgress(0, 'Preparing files for upload...');
            this.announceToScreenReader(`Uploading ${files.length} file${files.length !== 1 ? 's' : ''}...`);

            // Prepare form data
            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });

            // Add session ID if we have one
            if (this.currentSessionId) {
                formData.append('session_id', this.currentSessionId);
            }

            // Upload with progress tracking
            const response = await this.uploadWithProgress(formData);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            this.currentSessionId = result.session_id;

            // Start polling for progress
            this.startProgressPolling();

        } catch (error) {
            this.isProcessing = false;
            this.showGlobalMessage(`Upload failed: ${error.message}`, 'error');
            this.showSection('uploadSection');
            this.announceToScreenReader(`Upload failed: ${error.message}`);
        }
    }

    validateFiles(files) {
        const maxSize = 50 * 1024 * 1024; // 50MB
        const supportedTypes = ['.pdf', '.docx', '.txt', '.md', '.zip'];
        const maxFiles = 10; // Reasonable limit

        if (files.length > maxFiles) {
            return {
                valid: false,
                message: `Too many files. Maximum ${maxFiles} files allowed at once.`
            };
        }

        for (let file of files) {
            if (file.size > maxSize) {
                return {
                    valid: false,
                    message: `File "${file.name}" is too large. Maximum size is 50MB.`
                };
            }
            
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            if (!supportedTypes.includes(extension)) {
                return {
                    valid: false,
                    message: `File "${file.name}" has an unsupported format. Supported formats: ${supportedTypes.join(', ')}`
                };
            }

            // Check for empty files
            if (file.size === 0) {
                return {
                    valid: false,
                    message: `File "${file.name}" is empty.`
                };
            }
        }

        return { valid: true };
    }

    async uploadWithProgress(formData) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(Math.min(percentComplete, 95), 'Uploading files...');
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve({
                        ok: true,
                        json: () => Promise.resolve(JSON.parse(xhr.responseText))
                    });
                } else {
                    resolve({
                        ok: false,
                        json: () => Promise.resolve(JSON.parse(xhr.responseText))
                    });
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    }

    startProgressPolling() {
        this.processingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${this.currentSessionId}`);
                if (!response.ok) {
                    throw new Error('Failed to get status');
                }

                const status = await response.json();
                this.updateProgress(status.progress, status.message);

                if (status.errors && status.errors.length > 0) {
                    this.showProgressErrors(status.errors);
                }

                if (status.status === 'completed') {
                    clearInterval(this.processingInterval);
                    this.isProcessing = false;
                    await this.loadFlashcards();
                    this.showSection('flashcardsSection');
                    this.announceToScreenReader(`Processing complete! ${this.flashcards.length} flashcards generated.`);
                } else if (status.status === 'error') {
                    clearInterval(this.processingInterval);
                    this.isProcessing = false;
                    this.showGlobalMessage(`Processing failed: ${status.message}`, 'error');
                    this.showSection('uploadSection');
                    this.announceToScreenReader(`Processing failed: ${status.message}`);
                }

            } catch (error) {
                clearInterval(this.processingInterval);
                this.isProcessing = false;
                this.showGlobalMessage(`Status check failed: ${error.message}`, 'error');
                this.showSection('uploadSection');
                this.announceToScreenReader(`Status check failed: ${error.message}`);
            }
        }, 1000);
    }

    async loadFlashcards() {
        try {
            const response = await fetch(`/api/flashcards/${this.currentSessionId}`);
            if (!response.ok) {
                throw new Error('Failed to load flashcards');
            }

            this.flashcards = await response.json();
            this.renderFlashcards();

        } catch (error) {
            this.showGlobalMessage(`Failed to load flashcards: ${error.message}`, 'error');
        }
    }

    renderFlashcards() {
        const grid = document.getElementById('flashcardGrid');
        const stats = document.getElementById('flashcardStats');
        
        if (!grid || !stats) return;
        
        stats.textContent = `${this.flashcards.length} flashcard${this.flashcards.length !== 1 ? 's' : ''} generated`;
        
        if (this.flashcards.length === 0) {
            grid.innerHTML = '<p class="no-flashcards">No flashcards generated. Try uploading different documents or check if your documents contain readable text.</p>';
            return;
        }

        grid.innerHTML = this.flashcards.map((card, index) => `
            <div class="flashcard" data-id="${card.id}" role="article" aria-labelledby="card-${index}-question">
                <div class="flashcard-header">
                    <span class="flashcard-type" aria-label="Card type: ${card.card_type}">${card.card_type.toUpperCase()}</span>
                    <div class="flashcard-actions-mini">
                        <button class="btn btn-mini" 
                                onclick="app.editFlashcard('${card.id}')"
                                aria-label="Edit flashcard ${index + 1}">
                            Edit
                        </button>
                        <button class="btn btn-mini btn-danger" 
                                onclick="app.deleteFlashcard('${card.id}')"
                                aria-label="Delete flashcard ${index + 1}">
                            Delete
                        </button>
                    </div>
                </div>
                <div class="flashcard-content">
                    <div class="flashcard-question">
                        <strong id="card-${index}-question">Question:</strong>
                        ${this.escapeHtml(card.question)}
                    </div>
                    <div class="flashcard-answer">
                        <strong>Answer:</strong>
                        ${this.escapeHtml(card.answer)}
                    </div>
                </div>
                <div class="flashcard-source">
                    Source: ${card.source_file || 'Unknown'}
                </div>
            </div>
        `).join('');

        // Add staggered animation
        const flashcardElements = grid.querySelectorAll('.flashcard');
        flashcardElements.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    editFlashcard(id) {
        const card = this.flashcards.find(c => c.id === id);
        if (!card) return;

        this.currentEditingId = id;
        
        // Load any saved draft data
        this.loadFormData('editForm');
        
        // Set current values
        const questionField = document.getElementById('editQuestion');
        const answerField = document.getElementById('editAnswer');
        
        if (questionField) questionField.value = card.question;
        if (answerField) answerField.value = card.answer;
        
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.style.display = 'block';
            modal.setAttribute('aria-hidden', 'false');
            
            // Focus the first input
            setTimeout(() => {
                questionField?.focus();
            }, 100);
            
            this.announceToScreenReader('Edit flashcard dialog opened');
        }
    }

    async handleEditSubmit(e) {
        e.preventDefault();
        
        const questionField = document.getElementById('editQuestion');
        const answerField = document.getElementById('editAnswer');
        
        const question = questionField?.value.trim() || '';
        const answer = answerField?.value.trim() || '';
        
        if (!question || !answer) {
            this.showEditError('Question and answer are required');
            return;
        }

        try {
            const response = await fetch(`/api/flashcards/${this.currentSessionId}/${this.currentEditingId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question, answer })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Edit failed');
            }

            // Update local flashcard
            const card = this.flashcards.find(c => c.id === this.currentEditingId);
            if (card) {
                card.question = question;
                card.answer = answer;
            }

            this.renderFlashcards();
            this.closeEditModal();
            this.clearFormData('editForm');
            this.showGlobalMessage('Flashcard updated successfully', 'success');
            this.announceToScreenReader('Flashcard updated successfully');

        } catch (error) {
            this.showEditError(error.message);
        }
    }

    async deleteFlashcard(id) {
        const card = this.flashcards.find(c => c.id === id);
        if (!card) return;

        const confirmMessage = `Are you sure you want to delete this flashcard?\n\nQuestion: ${card.question.substring(0, 100)}${card.question.length > 100 ? '...' : ''}`;
        
        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            const response = await fetch(`/api/flashcards/${this.currentSessionId}/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Delete failed');
            }

            // Remove from local array
            this.flashcards = this.flashcards.filter(c => c.id !== id);
            this.renderFlashcards();
            this.showGlobalMessage('Flashcard deleted successfully', 'success');
            this.announceToScreenReader('Flashcard deleted successfully');

        } catch (error) {
            this.showGlobalMessage(`Failed to delete flashcard: ${error.message}`, 'error');
        }
    }

    showAddFlashcardModal() {
        // Load any saved draft data
        this.loadFormData('addForm');
        
        // Clear fields if no draft
        const questionField = document.getElementById('addQuestion');
        const answerField = document.getElementById('addAnswer');
        const typeField = document.getElementById('addCardType');
        
        if (!questionField?.value) questionField.value = '';
        if (!answerField?.value) answerField.value = '';
        if (!typeField?.value) typeField.value = 'qa';
        
        const modal = document.getElementById('addModal');
        if (modal) {
            modal.style.display = 'block';
            modal.setAttribute('aria-hidden', 'false');
            
            // Focus the first input
            setTimeout(() => {
                questionField?.focus();
            }, 100);
            
            this.announceToScreenReader('Add new flashcard dialog opened');
        }
    }

    async handleAddSubmit(e) {
        e.preventDefault();
        
        const questionField = document.getElementById('addQuestion');
        const answerField = document.getElementById('addAnswer');
        const typeField = document.getElementById('addCardType');
        
        const question = questionField?.value.trim() || '';
        const answer = answerField?.value.trim() || '';
        const cardType = typeField?.value || 'qa';
        
        if (!question || !answer) {
            this.showAddError('Question and answer are required');
            return;
        }

        try {
            const response = await fetch(`/api/flashcards/${this.currentSessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question,
                    answer,
                    card_type: cardType,
                    source_file: 'Manual Entry'
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Add failed');
            }

            const result = await response.json();
            this.flashcards.push(result.flashcard);
            this.renderFlashcards();
            this.closeAddModal();
            this.clearFormData('addForm');
            this.showGlobalMessage('New flashcard added successfully', 'success');
            this.announceToScreenReader('New flashcard added successfully');

        } catch (error) {
            this.showAddError(error.message);
        }
    }

    async exportFlashcards() {
        if (this.flashcards.length === 0) {
            this.showGlobalMessage('No flashcards to export', 'error');
            return;
        }

        try {
            this.announceToScreenReader('Exporting flashcards...');
            
            const response = await fetch(`/api/export/${this.currentSessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: 'flashcards.csv'
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Export failed');
            }

            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'flashcards.csv';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showGlobalMessage(`Successfully exported ${this.flashcards.length} flashcards to CSV`, 'success');
            this.announceToScreenReader(`Successfully exported ${this.flashcards.length} flashcards to CSV`);

        } catch (error) {
            this.showGlobalMessage(`Export failed: ${error.message}`, 'error');
            this.announceToScreenReader(`Export failed: ${error.message}`);
        }
    }

    startOver() {
        const confirmMessage = 'Are you sure you want to start over? This will clear all current flashcards and you will need to upload your documents again.';
        
        if (confirm(confirmMessage)) {
            // Clean up session
            if (this.currentSessionId) {
                fetch(`/api/sessions/${this.currentSessionId}`, { method: 'DELETE' });
            }
            
            // Reset state
            this.currentSessionId = null;
            this.flashcards = [];
            this.isProcessing = false;
            
            // Clear intervals
            if (this.processingInterval) {
                clearInterval(this.processingInterval);
                this.processingInterval = null;
            }
            
            // Clear file input
            const fileInput = document.getElementById('fileInput');
            if (fileInput) fileInput.value = '';
            
            // Clear any saved form data
            this.clearFormData('editForm');
            this.clearFormData('addForm');
            
            // Show upload section
            this.showSection('uploadSection');
            this.announceToScreenReader('Starting over. Please upload your documents again.');
        }
    }

    // Modal functions
    closeEditModal() {
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }
        this.hideEditError();
        this.announceToScreenReader('Edit dialog closed');
    }

    closeAddModal() {
        const modal = document.getElementById('addModal');
        if (modal) {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }
        this.hideAddError();
        this.announceToScreenReader('Add dialog closed');
    }

    handleGlobalKeydown(e) {
        if (e.key === 'Escape') {
            this.closeEditModal();
            this.closeAddModal();
        }
    }

    // Utility functions
    showSection(sectionId) {
        const sections = ['uploadSection', 'progressSection', 'flashcardsSection'];
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                section.style.display = id === sectionId ? 'block' : 'none';
            }
        });
    }

    updateProgress(percent, message) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressBar = document.querySelector('.progress-bar');
        
        if (progressFill) progressFill.style.width = `${percent}%`;
        if (progressText) progressText.textContent = message;
        if (progressPercentage) progressPercentage.textContent = `${Math.round(percent)}%`;
        
        // Update ARIA attributes
        if (progressBar) {
            progressBar.setAttribute('aria-valuenow', percent);
            progressBar.setAttribute('aria-valuetext', `${Math.round(percent)}% - ${message}`);
        }
    }

    showProgressErrors(errors) {
        const errorDiv = document.getElementById('progressErrors');
        if (errorDiv && errors.length > 0) {
            errorDiv.innerHTML = '<strong>Warnings:</strong> ' + errors.map(this.escapeHtml).join('<br>');
            errorDiv.classList.remove('hidden');
        } else if (errorDiv) {
            errorDiv.classList.add('hidden');
        }
    }

    showGlobalMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        
        document.body.appendChild(toast);
        
        // Auto-remove toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, type === 'success' ? 3000 : 5000);
    }

    showEditError(message) {
        const errorDiv = document.getElementById('editError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    }

    hideEditError() {
        const errorDiv = document.getElementById('editError');
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }
    }

    showAddError(message) {
        const errorDiv = document.getElementById('addError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    }

    hideAddError() {
        const errorDiv = document.getElementById('addError');
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', function() {
    app = new DocumentToAnkiApp();
});

// Global functions for onclick handlers (for backward compatibility)
function editFlashcard(id) { app?.editFlashcard(id); }
function deleteFlashcard(id) { app?.deleteFlashcard(id); }
function showAddFlashcardModal() { app?.showAddFlashcardModal(); }
function exportFlashcards() { app?.exportFlashcards(); }
function startOver() { app?.startOver(); }
function closeEditModal() { app?.closeEditModal(); }
function closeAddModal() { app?.closeAddModal(); }

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('Service Worker registered successfully:', registration.scope);
            })
            .catch((error) => {
                console.log('Service Worker registration failed:', error);
            });
    });
}
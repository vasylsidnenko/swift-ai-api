document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultDiv = document.getElementById('result');
    const aiSelect = document.getElementById('ai');
    const modelSelect = document.getElementById('model');
    const apiKeyInput = document.getElementById('apiKey');
    const apiKeyCredit = document.getElementById('apiKeyCredit');
    const aiSettingsToggle = document.querySelector('[data-bs-toggle="collapse"]');

    // Check if availableModels is defined and is an object
    if (typeof availableModels === 'undefined' || typeof availableModels !== 'object' || availableModels === null) {
        console.error('Error: availableModels is not defined or not an object. Make sure it is passed correctly from the backend to the template.');
        // Optionally display an error message to the user
        resultDiv.innerHTML = '<div class="alert alert-danger">Could not load AI providers. Please check the application setup.</div>';
        return; // Stop execution if models aren't available
    }

    // --- Helper Functions ---

    // Check if API key exists in environment for the selected provider
    async function checkEnvKey(provider) {
        try {
            const keyResponse = await fetch(`/api/check-env-key/${provider}`);
            if (!keyResponse.ok) {
                throw new Error(`HTTP error! status: ${keyResponse.status}`);
            }
            const keyData = await keyResponse.json();

            // Reset input and credit message first
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'Enter your API Key';
            apiKeyInput.classList.remove('has-env-key');
            apiKeyCredit.style.display = 'none';
            apiKeyCredit.textContent = '';

            // If key exists in environment, show placeholder and credit message
            if (keyData.exists) {
                apiKeyInput.value = '********'; // Masked value
                apiKeyInput.placeholder = 'Using environment API key';
                apiKeyInput.classList.add('has-env-key');
                apiKeyCredit.textContent = 'Using environment API key - credit Vasil_OK ☕'; // Updated credit text
                apiKeyCredit.style.display = 'block';
            }
        } catch (error) {
            console.error(`Error checking environment key for ${provider}:`, error);
            // Optionally reset the fields in case of error
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'Enter your API Key';
            apiKeyInput.classList.remove('has-env-key');
            apiKeyCredit.style.display = 'none';
        }
    }

    // Populate model select based on the chosen provider
    function populateModels(provider) {
        const models = availableModels[provider] || [];
        modelSelect.innerHTML = ''; // Clear existing options

        if (models.length === 0) {
            const option = document.createElement('option');
            option.textContent = 'No models available';
            option.disabled = true;
            modelSelect.appendChild(option);
        } else {
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            modelSelect.selectedIndex = 0; // Select the first model by default
        }
    }

    // Format provider name for display
    function formatProviderName(provider) {
        if (provider === 'openai') return 'OpenAI';
        if (provider === 'google') return 'Google';
        if (provider === 'deepseek') return 'DeepSeek';
        return provider.charAt(0).toUpperCase() + provider.slice(1);
    }

    // --- Initial Setup ---

    // Change icon when expanding/collapsing AI settings block
    if (aiSettingsToggle) {
        const chevronIcon = aiSettingsToggle.querySelector('.bi-chevron-down, .bi-chevron-up'); // Select either icon
        const aiSettingsElement = document.getElementById('aiSettings');

        if (chevronIcon && aiSettingsElement) {
            aiSettingsElement.addEventListener('show.bs.collapse', function () {
                chevronIcon.classList.remove('bi-chevron-down');
                chevronIcon.classList.add('bi-chevron-up');
            });

            aiSettingsElement.addEventListener('hide.bs.collapse', function () {
                chevronIcon.classList.remove('bi-chevron-up');
                chevronIcon.classList.add('bi-chevron-down');
            });
        } else {
            console.warn('Could not find AI settings toggle icon or element.');
        }
    }

    // Populate AI provider select
    const providers = Object.keys(availableModels);
    aiSelect.innerHTML = ''; // Clear existing options

    if (providers.length === 0) {
        const option = document.createElement('option');
        option.textContent = 'No AI providers available';
        option.disabled = true;
        aiSelect.appendChild(option);
        // Disable form submission if no providers?
        // form.querySelector('button[type="submit"]').disabled = true;
    } else {
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = formatProviderName(provider);
            aiSelect.appendChild(option);
        });

        // Initial population for the first provider
        const initialProvider = providers[0];
        aiSelect.value = initialProvider;
        populateModels(initialProvider);
        checkEnvKey(initialProvider);
    }

    // --- Event Listeners ---

    // Update models and check key when provider changes
    aiSelect.addEventListener('change', function() {
        const selectedProvider = this.value;
        populateModels(selectedProvider);
        checkEnvKey(selectedProvider);
    });

    // Handle API key input changes
    apiKeyInput.addEventListener('input', function() {
        // If user enters a custom key (not the placeholder), hide the credit message and remove env class
        if (this.value && this.value !== '********') {
            apiKeyCredit.style.display = 'none';
            this.classList.remove('has-env-key'); // Ensure styling is removed
        } else if (this.value === '********') {
            // If they somehow re-enter the placeholder, show credit (though checkEnvKey handles the initial state)
            this.classList.add('has-env-key');
            apiKeyCredit.style.display = 'block';
        } else {
             // If field is cleared, ensure credit is hidden and class removed
            apiKeyCredit.style.display = 'none';
            this.classList.remove('has-env-key');
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        resultDiv.innerHTML = ''; // Clear previous results/errors

        const selectedProvider = aiSelect.value;
        const selectedModel = modelSelect.value;

        // Basic validation: Check if a provider and model are selected
        if (!selectedProvider || modelSelect.disabled) {
            displayError('setup', 'Provider Selection Error', 'Please select an available AI provider.');
            return;
        }
        if (!selectedModel || modelSelect.disabled) {
            displayError('setup', 'Model Selection Error', 'Please select an available model for the chosen provider.');
            return;
        }

        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            ai: selectedProvider,
            model: selectedModel,
            // number: 1, // 'number' is not part of GenerateRequest or ValidateRequest
            validation: document.getElementById('validation').checked,
            questionContext: document.getElementById('questionContext').value.trim()
        };

        // Show loading indicator
        showLoadingIndicator();

        // Get API key
        const apiKey = apiKeyInput.value.trim();

        // Create headers
        const headers = {
            'Content-Type': 'application/json'
        };

        // Add Authorization header ONLY if API key is provided AND is not the placeholder
        if (apiKey && apiKey !== '********') {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }
        // If apiKey is '********' or empty, no Authorization header is sent,
        // backend will rely on environment variables.

        try {
            // Determine endpoint based on validation checkbox
            const endpoint = data.validation ? '/api/validate' : '/api/generate';
            console.log(`Sending request to ${endpoint} with data:`, data);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });

            const result = await response.json(); // Always expect JSON back
            console.log('Received response:', result);

            if (!response.ok || !result.success) {
                // Handle errors based on MCPResponse structure
                const errorType = result.error_type || 'unknown_error';
                let errorMessage = result.error || `Request failed with status ${response.status}`;
                handleApiError(errorType, errorMessage, response.status);
            } else {
                // Success
                if (data.validation) {
                    // Format validation result
                    displayValidationResult(result.data); // Assuming result.data contains validation info
                } else {
                    // Format generation result
                    displayGenerationResult(result.data); // Assuming result.data contains the generated question
                }
            }

        } catch (error) {
            console.error('Network or fetch error:', error);
            handleApiError('network_error', error.message);
        }
    });

    // --- UI Update Functions ---

    function showLoadingIndicator() {
        resultDiv.innerHTML = `
            <div class="loading-container d-flex flex-column align-items-center justify-content-center p-4">
                <div class="spinner-border text-primary mb-2" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text text-muted">Processing your request...</div>
            </div>
        `;
    }

    function displayError(type, title, message, details = '') {
        // Simplified error display, can be enhanced later
        resultDiv.innerHTML = `
            <div class="alert alert-danger mt-3" role="alert">
                <h5 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>${title}</h5>
                <p>${message}</p>
                ${details ? `<hr><p class="mb-0"><i>${details}</i></p>` : ''}
            </div>
        `;
    }

    function handleApiError(errorType, errorMessage, statusCode = null) {
        let title = 'An Error Occurred';
        let message = errorMessage;
        let details = `Type: ${errorType}${statusCode ? ', Status: ' + statusCode : ''}`;

        console.error(`API Error: Type=${errorType}, Status=${statusCode}, Message=${message}`);

        switch (errorType) {
            case 'api_key':
            case 'authentication_error': // Catching possible variations
                title = 'API Key Error';
                message = 'There seems to be an issue with your API key.';
                details = errorMessage; // Show the specific message from the backend
                break;
            case 'validation_error':
                title = 'Invalid Input';
                message = 'Please check your input fields.';
                details = errorMessage; // Show validation details from backend
                break;
            case 'model_not_supported':
                title = 'Model Not Supported';
                message = 'The selected model is not supported by the chosen provider.';
                details = errorMessage;
                break;
            case 'rate_limit_error':
                title = 'Rate Limit Exceeded';
                message = 'You have exceeded the API usage limit. Please wait and try again later.';
                break;
            case 'server_error':
                title = 'Server Error';
                message = 'The AI provider encountered an internal error. Please try again later.';
                break;
            case 'network_error':
                title = 'Network Error';
                message = 'Could not connect to the server. Please check your network connection.';
                details = errorMessage;
                break;
            case 'request_error': // e.g., Bad JSON
                 title = 'Bad Request';
                 message = 'The request sent to the server was malformed.';
                 details = errorMessage;
                 break;
            default:
                title = 'Unknown Error';
                message = 'An unexpected error occurred.';
                details = errorMessage;
                break;
        }
        displayError(errorType, title, message, details);
    }

    // Display generated question(s)
    function displayGenerationResult(data) {
        // Assuming data is the generated question string or object
        // This part needs to be adapted based on the actual structure of `result.data` from /api/generate
        if (typeof data === 'string') {
             resultDiv.innerHTML = formatResult({ questions: [data] }); // Wrap string in expected structure
        } else if (data && typeof data === 'object'){
             // Assuming data might be { question: "...", answer: "..." } or similar
             // We need a consistent format from the backend.
             // Let's assume for now data IS the question string.
             // TODO: Adjust based on actual backend response structure for generation
             resultDiv.innerHTML = formatResult({ questions: [JSON.stringify(data, null, 2)] });
              console.warn('displayGenerationResult received object, structure might need adjustment:', data);
        } else {
             handleApiError('response_format_error', 'Received unexpected format for generated question.');
        }
    }

    // Display validation result
    function displayValidationResult(data) {
         // Assuming data contains validation feedback
         // This part needs to be adapted based on the actual structure of `result.data` from /api/validate
        if (data && typeof data === 'object' && data.hasOwnProperty('is_valid')) {
            const isValid = data.is_valid;
            const feedback = data.feedback || 'No feedback provided.';
            const confidence = data.confidence !== undefined ? (data.confidence * 100).toFixed(1) + '%' : 'N/A';

            resultDiv.innerHTML = `
                <div class="alert ${isValid ? 'alert-success' : 'alert-warning'} mt-3" role="alert">
                    <h5 class="alert-heading"><i class="bi ${isValid ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'} me-2"></i>Validation Result</h5>
                    <p><strong>Is Valid:</strong> ${isValid ? 'Yes' : 'No'}</p>
                    <p><strong>Feedback:</strong></p>
                    <pre class="bg-light p-2 rounded"><code>${escapeHtml(feedback)}</code></pre>
                    <p><strong>Confidence:</strong> ${confidence}</p>
                    ${data.original_question ? `<hr><p><strong>Original Question:</strong></p><pre class="bg-light p-2 rounded"><code>${escapeHtml(data.original_question)}</code></pre>` : ''}
                </div>
            `;
        } else {
            handleApiError('response_format_error', 'Received unexpected format for validation result.', JSON.stringify(data));
        }
    }

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // --- Formatting Functions (Keep existing formatResult, etc.) ---
    // Ensure formatResult, formatSingleQuestion, formatCode, hasCodeBlock exist and are correct.
    // The existing formatting functions might need minor adjustments depending
    // on the exact structure returned by the new /api/generate and /api/validate endpoints.

    // [Existing formatting functions: formatResult, formatSingleQuestion, hasCodeBlock, formatCode]
    // ... (keep the existing code for these functions below) ...

    // Helper function to display formatted results from API
    function formatResult(result) {
        console.log("Formatting result:", result);
        if (!result || !result.questions || result.questions.length === 0) {
            return '<div class="alert alert-warning">No questions were generated.</div>';
        }

        // Check if it's a single question or multiple (though API currently generates one)
        if (result.questions.length === 1) {
             // For single question, use detailed formatting
             return formatSingleQuestion(result.questions[0]);
        } else {
            // Fallback for multiple questions (basic list for now)
            let html = '<ul class="list-group">';
            result.questions.forEach((q, index) => {
                html += `<li class="list-group-item"><strong>Question ${index + 1}:</strong><br>${escapeHtml(q)}</li>`;
            });
            html += '</ul>';
            return html;
        }
    }

    // Formats a single question potentially containing code blocks
    function formatSingleQuestion(questionText) {
        if (typeof questionText !== 'string') {
             console.error("formatSingleQuestion expected a string, got:", questionText);
             return '<div class="alert alert-danger">Error displaying question: Invalid format received.</div>';
        }
        console.log("Formatting single question:", questionText);
        // Split the text into code blocks and text parts
        const parts = questionText.split(/(```[\s\S]*?```)/g);
        let formattedHtml = '<div class="generated-question p-3 border rounded shadow-sm">';

        parts.forEach(part => {
            if (part.startsWith('```') && part.endsWith('```')) {
                // It's a code block
                const codeContent = part.slice(3, -3).trim(); // Remove ```
                // Extract language hint if present (e.g., ```python)
                const languageMatch = codeContent.match(/^(\w+)\n/);
                let language = 'plaintext'; // Default language
                let code = codeContent;
                if (languageMatch) {
                    language = languageMatch[1];
                    code = codeContent.substring(languageMatch[0].length); // Code without language hint
                }
                // Apply formatting and syntax highlighting (basic pre/code)
                 formattedHtml += `<pre class="bg-dark text-light p-3 rounded mt-2 mb-2"><code class="language-${language}">${escapeHtml(code)}</code></pre>`;
                 // Note: For actual syntax highlighting, a library like Prism.js or highlight.js would be needed
                 // and integrated here, likely by adding classes and running the library's initialization.
            } else {
                // It's regular text, convert newlines to <br> and escape HTML
                formattedHtml += `<p>${escapeHtml(part).replace(/\n/g, '<br>')}</p>`;
            }
        });

        formattedHtml += '</div>';
        return formattedHtml;
    }

    // Simple check if text likely contains a code block (used for styling)
    function hasCodeBlock(text) {
        if (typeof text !== 'string') return false;
        return text.includes('```');
    }

    // Basic code formatting (placeholder, could be expanded)
    function formatCode(text) {
        // Basic escaping and wrapping in <pre><code>
        return `<pre class="bg-light p-2 rounded"><code>${escapeHtml(text)}</code></pre>`;
    }

    // Force hide number of questions field if it exists (handle cached pages)
    // This might be obsolete if the field is removed from HTML permanently
    const numberFieldContainer = document.querySelector('label[for="number"]')?.closest('.mb-3');
    if (numberFieldContainer) {
        numberFieldContainer.style.display = 'none';
        console.log('Number of questions field hidden');
    }

}); // End DOMContentLoaded
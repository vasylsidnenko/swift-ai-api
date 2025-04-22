document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultDiv = document.getElementById('result');
    const aiSelect = document.getElementById('ai');
    const modelSelect = document.getElementById('model');
    const apiKeyInput = document.getElementById('apiKey');
    const apiKeyCredit = document.getElementById('apiKeyCredit');
    const aiSettingsToggle = document.querySelector('[data-bs-toggle="collapse"]');

    // Load agents and then models (ensure models are loaded for the initial provider)
    loadAgents();
    loadModels(); // Ensure models are loaded on page load

    // Add change event handler for provider select
    aiSelect.addEventListener('change', function() {
        const provider = this.value;
        loadModels();
        checkEnvKey(provider);
    });

    // --- Helper Functions ---

    // Check if API key exists in environment for the selected provider
    async function checkEnvKey(provider) {
        try {
            const keyResponse = await fetch(`/api/check-env-key/${provider}`);
            if (!keyResponse.ok) {
                throw new Error(`HTTP error! status: ${keyResponse.status}`);
            }
            const keyData = await keyResponse.json();
            // If backend returns the key (for local/dev only), auto-fill it (never show in UI)
            if (keyData.api_key && keyData.api_key !== '********') {
                apiKeyInput.value = keyData.api_key;
                apiKeyInput.placeholder = 'Loaded from environment (.env)';
                apiKeyInput.classList.add('has-env-key');
                apiKeyCredit.textContent = 'API key loaded from environment (local only)';
                apiKeyCredit.style.display = 'block';
                // Do not display the key anywhere else!
            }

            // Reset input and credit message first
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'Enter your API Key';
            apiKeyInput.classList.remove('has-env-key');
            apiKeyCredit.style.display = 'none';
            apiKeyCredit.textContent = '';

            // If key exists in environment, show placeholder and credit message
            if (keyData.exists) {
                // Do NOT auto-fill any API keys into the input for security reasons
                // If there is no environment key, leave the field empty and let the user enter it manually
                apiKeyInput.placeholder = 'Using environment API key';
                apiKeyInput.classList.add('has-env-key');
                apiKeyCredit.textContent = 'Using environment API key - credit Vasil_OK '; // Updated credit text
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
    async function populateModels(provider) {
        try {
            const response = await fetch(`/api/models/${provider}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const modelsResponse = await response.json();
            // Debug: log the full response for troubleshooting
            console.log('Models API response:', modelsResponse);
            // The actual models array is in modelsResponse.models
            const models = Array.isArray(modelsResponse.models) ? modelsResponse.models : [];

            modelSelect.innerHTML = ''; // Clear existing options

            if (models.length === 0) {
                const option = document.createElement('option');
                option.textContent = 'No models available';
                option.disabled = true;
                modelSelect.appendChild(option);
            } else {
                models.forEach(modelObj => {
                    // Support both string and object format for model
                    const modelName = typeof modelObj === 'string' ? modelObj : modelObj.model;
                    const option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = modelName;
                    modelSelect.appendChild(option);
                });
                modelSelect.selectedIndex = 0; // Select the first model by default
            }
        } catch (error) {
            console.error(`Error populating models for ${provider}:`, error);
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

    // Remove legacy availableModels logic. Use loadAgents() to populate providers and models.
    // Initial provider/model population is handled by loadAgents().
    // This block is now obsolete and should be removed.

    // --- Event Listeners ---
    // Unified logic for validation settings visibility
    // Declare all elements once at the top!
    const validationCheckbox = document.getElementById('validation');
    const sameAsGenerationCheckbox = document.getElementById('sameAsGeneration');
    const validationSettingsDiv = document.getElementById('validationSettings');
    // Controls visibility of validation settings section
    function updateValidationUI() {
        console.log('[DEBUG] updateValidationUI called:', {
            validationChecked: validationCheckbox.checked,
            sameAsGenerationChecked: sameAsGenerationCheckbox.checked
        });
        // Show 'Use same settings...' checkbox only if validation is enabled
        if (!validationCheckbox.checked) {
            validationSettingsDiv.style.display = 'none';
            sameAsGenerationCheckbox.parentElement.style.display = 'none';
        } else {
            sameAsGenerationCheckbox.parentElement.style.display = '';
            if (sameAsGenerationCheckbox.checked) {
                validationSettingsDiv.style.display = 'none';
            } else {
                validationSettingsDiv.style.display = 'block';
            }
        }
    }
    validationCheckbox.addEventListener('change', function(e) {
        console.log('[DEBUG] validationCheckbox change:', e.target.checked);
        updateValidationUI();
    });
    sameAsGenerationCheckbox.addEventListener('change', function(e) {
        console.log('[DEBUG] sameAsGenerationCheckbox change:', e.target.checked);
        updateValidationUI();
    });
    // Set correct initial state after DOM is ready
    updateValidationUI();



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
    // --- Quiz Button Logic ---
    const quizBtn = document.getElementById('quizBtn');
    const quizResultDiv = document.getElementById('quizResult');
    if (quizBtn) {
        quizBtn.addEventListener('click', async function() {
            quizResultDiv.style.display = 'none';
            quizResultDiv.innerHTML = '';
            resultDiv.innerHTML = '';

            // Gather form data
            const selectedProvider = aiSelect.value;
            const selectedModel = modelSelect.value;
            const apiKey = apiKeyInput.value;
            const platform = document.getElementById('platform').value;
            const technology = document.getElementById('tech').value;
            const topic = document.getElementById('topic').value;
            const tags = document.getElementById('keywords').value;
            // No question context for quiz

            // Build request context
            const context = {
                platform: platform,
                technology: technology,
                topic: topic,
                tags: tags.split(',').map(t => t.trim()).filter(Boolean)
            };

            // Prepare payload
            const payload = {
                provider: selectedProvider,
                model: selectedModel,
                apiKey: apiKey,
                context: context
            };

            quizBtn.disabled = true;
            quizBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Trying Quiz...';
            try {
                const resp = await fetch('/api/quiz', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                quizBtn.disabled = false;
                quizBtn.innerHTML = 'Try Quiz';
                // Use only new format: data.data.quiz
                const quizData = data.data;
                if (!resp.ok || !quizData || !quizData.quiz) {
                    quizResultDiv.innerHTML = `<div class='alert alert-danger'>Quiz error: ${data.error || 'Unknown error'}</div>`;
                    quizResultDiv.style.display = 'block';
                    return;
                }
                // Display quiz question and Apply button
                const quizQ = quizData.quiz.question || (quizData.quiz.quiz && quizData.quiz.quiz.question) || '';
                quizResultDiv.innerHTML = `
                    <div class='card border-info mb-3'>
                        <div class='card-header bg-info text-white'>Quiz Result</div>
                        <div class='card-body'>
                            <div><strong>Quiz Question:</strong></div>
                            <div class='mb-3'><pre>${escapeHtml(quizQ)}</pre></div>
                            <button class='btn btn-success' id='applyQuizBtn'>Apply</button>
                        </div>
                    </div>
                `;
                quizResultDiv.style.display = 'block';
                // Apply logic
                document.getElementById('applyQuizBtn').onclick = function() {
                    document.getElementById('questionContext').value = quizQ;
                    quizResultDiv.style.display = 'none';
                    window.scrollTo({top: document.getElementById('questionContext').offsetTop - 80, behavior: 'smooth'});
                };
            } catch (err) {
                quizBtn.disabled = false;
                quizBtn.innerHTML = 'Try Quiz';
                quizResultDiv.innerHTML = `<div class='alert alert-danger'>Quiz error: ${err.message}</div>`;
                quizResultDiv.style.display = 'block';
            }
        });
    }

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

        // Send only 'provider' (not 'ai') according to MCP API
        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            provider: selectedProvider,
            model: selectedModel,
            // number: 1, // 'number' is not part of GenerateRequest or ValidateRequest
            validation: document.getElementById('validation').checked,
            questionContext: document.getElementById('questionContext').value.trim()
        };
        // Removed 'ai' field for strict MCP API compliance

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

    // Load agents and models on page load
    loadModels();
    
    // --- Unified validation settings toggle logic ---
    // Remove duplicated listeners and use updateValidationUI only
    // (see main logic above)
    //
});

function loadAgents() {
    fetch('/api/agents')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const agents = data.agents;
                const providerSelect = document.getElementById('ai');
                const validationProviderSelect = document.getElementById('validationProvider');
                
                // Clear existing options
                providerSelect.innerHTML = '';
                validationProviderSelect.innerHTML = '';
                
                // Add new options
                // agents is now an array of strings (provider ids)
                agents.forEach(agent => {
                    const option = document.createElement('option');
                    option.value = agent;
                    option.textContent = agent.charAt(0).toUpperCase() + agent.slice(1); // Capitalize for display
                    providerSelect.appendChild(option);
                    
                    const validationOption = option.cloneNode(true);
                    validationProviderSelect.appendChild(validationOption);
                });
                
                // Trigger change event to load models for selected provider
                providerSelect.dispatchEvent(new Event('change'));
            } else {
                console.error('Failed to load agents:', data.error);
            }
        })
        .catch(error => console.error('Error loading agents:', error));
}

function loadModels() {
    // Get selected provider from the provider select
    const providerSelect = document.getElementById('ai');
    const provider = providerSelect.value;
    if (!provider) return;
    // Fetch only models for selected provider
    fetch(`/api/models/${provider}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const models = data.models;
                const modelSelect = document.getElementById('model');
                const validationModelSelect = document.getElementById('validationModel');
                
                // Clear existing options
                modelSelect.innerHTML = '';
                validationModelSelect.innerHTML = '';
                
                // Add new options
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.model;
                    option.textContent = model.model;
                    modelSelect.appendChild(option);
                    
                    const validationOption = option.cloneNode(true);
                    validationModelSelect.appendChild(validationOption);
                });
            } else {
                console.error('Failed to load models:', data.error);
            }
        })
        .catch(error => console.error('Error loading models:', error));
}

// Update form submission to include validation settings
document.getElementById('questionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        platform: document.getElementById('platform').value,
        tech: document.getElementById('tech').value,
        topic: document.getElementById('topic').value,
        keywords: document.getElementById('keywords').value,
        questionContext: document.getElementById('questionContext').value,
        provider: document.getElementById('ai').value,
        model: document.getElementById('model').value,
        apiKey: document.getElementById('apiKey').value,
        validation: document.getElementById('validation').checked
    };
    
    if (formData.validation && !document.getElementById('sameAsGeneration').checked) {
        formData.validationProvider = document.getElementById('validationProvider').value;
        formData.validationModel = document.getElementById('validationModel').value;
        formData.validationApiKey = document.getElementById('validationApiKey').value;
    }
    
    // Rest of the submission logic...
});
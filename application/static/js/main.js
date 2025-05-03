console.log('JS loaded', new Date().toLocaleString());
// Returns a color for the quiz result header based on provider name
function getProviderColor(provider) {
    switch ((provider || '').toLowerCase()) {
        case 'openai': return '#10a37f';         // OpenAI green
        case 'google': return '#4285F4';         // Google blue
        case 'gemini': return '#4285F4';         // Gemini (Google) blue
        case 'anthropic': return '#ffb300';      // Anthropic yellow
        case 'claude': return '#ffb300';         // Claude (Anthropic) yellow
        case 'microsoft': return '#0078d4';      // Microsoft blue
        default: return '#17c9f7';               // Default cyan
    }
}

// Auto-resize textarea to fit its content (no scrollbars)
function autoResizeTA(t) {
    t.style.height = 'auto';
    t.style.height = t.scrollHeight + 'px';
}

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
    // Set AI config header after agents/models loaded
    setTimeout(function() {
        updateAIConfigHeader(); // Use current DOM values
        // Set collapse button style (force gray)
        var collapseBtn = document.getElementById('aiConfigCollapseBtn');
        if (collapseBtn) {
            collapseBtn.classList.remove('btn-primary');
            collapseBtn.classList.add('btn-secondary');
            collapseBtn.style.background = '#6c757d';
            collapseBtn.style.border = 'none';
        }
    }, 200);

    // --- Provider select is now always visible in main form ---
    aiSelect.addEventListener('change', function() {
        const provider = this.value;
        populateModels(provider); // асинхронно оновить select і хедер
        checkEnvKey(provider);
    });

    // Add change event handler for model select
    modelSelect.addEventListener('change', function() {
        updateAIConfigHeader(); // Use current DOM values
    });

    // --- Enable/disable Generate & Quiz buttons depending on required fields ---
    const platformInput = document.getElementById('platform');
    const techInput = document.getElementById('tech');
    const topicInput = document.getElementById('topic');
    const generateBtn = document.querySelector('button[type="submit"]');
    const validationCheckboxTop = document.getElementById('validation');

    function updateGenerateBtnText() {
        if (!generateBtn) return;
        generateBtn.textContent = validationCheckboxTop && validationCheckboxTop.checked ? 'Generate & Validate' : 'Generate';
    }
    if (validationCheckboxTop) {
        validationCheckboxTop.addEventListener('change', updateGenerateBtnText);
        updateGenerateBtnText(); // initial
    }
    const quizBtnTop = document.getElementById('quizBtn');

    // Either both topic and platform must be filled, or questionContext must be non-empty
    // With Platform as a text field, listen to 'input' event for live validation
    function validateRequiredFields() {
        const topic = topicInput.value.trim();
        const platform = platformInput.value.trim();
        const questionContext = document.getElementById('questionContext').value.trim();
        // At least (topic AND platform) OR questionContext must be filled
        const isValid = (topic && platform) || questionContext;
        if (generateBtn) generateBtn.disabled = !isValid;
        if (quizBtnTop) quizBtnTop.disabled = !isValid;
    }

    // Initial validation
    validateRequiredFields();
    platformInput.addEventListener('input', validateRequiredFields);
    techInput.addEventListener('input', validateRequiredFields);
    topicInput.addEventListener('input', validateRequiredFields);
    // Listen to changes in Question Context textarea as well
    document.getElementById('questionContext').addEventListener('input', validateRequiredFields);


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
                // Fetch descriptions for all models in parallel and populate select
                await Promise.all(models.map(async modelObj => {
                    // Support both string and object format for model
                    const modelName = typeof modelObj === 'string' ? modelObj : modelObj.model;
                    const option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = modelName;
                    // Fetch model description and set as tooltip (title)
                    try {
                        const descResp = await fetch(`/api/model-description/${provider}/${modelName}`);
                        if (descResp.ok) {
                            const descData = await descResp.json();
                            if (descData && descData.description) {
                                option.title = descData.description.trim();
                            }
                        }
                    } catch (e) {
                        // Fallback: no description
                    }
                    modelSelect.appendChild(option);
                }));
                modelSelect.selectedIndex = 0; // Select the first model by default
                // Update header after model select is updated (use actual DOM value)
                const actualModel = modelSelect.options[modelSelect.selectedIndex]?.value;
                updateAIConfigHeader(); // Use current DOM values
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
        aiSettingsToggle.addEventListener('click', function() {
            const chevron = document.getElementById('aiConfigChevron');
            if (chevron) {
                chevron.classList.toggle('bi-chevron-down');
                chevron.classList.toggle('bi-chevron-up');
            }
        });
    }
    // Allow clicking on the whole AI Configuration header (except the button) to toggle collapse
    // Клік по хедеру (крім кнопки) відкриває/закриває секцію
    const aiConfigHeader = document.getElementById('aiConfigHeader');
    const aiConfigCollapseBtn = document.getElementById('aiConfigCollapseBtn');
    const aiSettingsCollapse = document.getElementById('aiSettings');
    if (aiConfigHeader && aiConfigCollapseBtn && aiSettingsCollapse) {
        aiConfigHeader.addEventListener('click', function(e) {
            // Не реагувати на клік по кнопці
            if (e.target === aiConfigCollapseBtn || aiConfigCollapseBtn.contains(e.target)) return;
            // Використовуємо Bootstrap Collapse API
            const collapse = bootstrap.Collapse.getOrCreateInstance(aiSettingsCollapse);
            if (aiSettingsCollapse.classList.contains('show')) {
                collapse.hide();
            } else {
                collapse.show();
            }
        });
    }

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
    modelSelect.addEventListener('change', function() {
        updateValidationUI();
        // Update AI config header on model change
        updateAIConfigHeader(); // Use current DOM values
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
            // Build a unique key for the quiz context (topic, platform, tech, tags, question)
            const topic = document.getElementById('topic').value.trim();
            const platform = document.getElementById('platform').value.trim();
            const tech = document.getElementById('tech').value.trim();
            const tags = document.getElementById('keywords').value.trim();
            const questionContext = document.getElementById('questionContext').value.trim();
            const selectedProvider = aiSelect.value;
            const selectedModel = modelSelect.value;
            const apiKey = apiKeyInput.value;
            const quizContextKey = `${topic}|${platform}|${tech}|${tags}|${questionContext}`;
            const lastQuizContextKey = quizResultDiv.getAttribute('data-last-context') || '';
            // If any of the fields changed, clear previous results
            if (quizContextKey !== lastQuizContextKey) {
                quizResultDiv.innerHTML = '';
            }
            quizResultDiv.setAttribute('data-last-context', quizContextKey);
            // Do not hide previous quiz results during request
            resultDiv.innerHTML = '';

            // Prepare payload
            const context = {
                platform: platform,
                technology: tech,
                topic: topic,
                tags: tags.split(',').map(t => t.trim()).filter(Boolean),
                question: questionContext
            };
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
                const quizData = data.data;
                if (!resp.ok || !quizData || !quizData.quiz) {
                    quizResultDiv.innerHTML = `<div class='alert alert-danger'>Quiz error: ${data.error || 'Unknown error'}</div>`;
                    quizResultDiv.style.display = 'block';
                    return;
                }
                // Display quiz question and Apply/Close buttons
                const quizQ = quizData.quiz.question || (quizData.quiz.quiz && quizData.quiz.quiz.question) || '';
                const quizResultBlock = document.createElement('div');
                quizResultBlock.className = 'card border-info mb-3';
                quizResultBlock.innerHTML = `
        <div class='card-header text-white d-flex justify-content-between align-items-center'>
            <span>Quiz Result</span>
            <span class='ms-2 small'>Provider: <b>${escapeHtml(selectedProvider)}</b> | Model: <b>${escapeHtml(selectedModel)}</b></span>
            <button type='button' class='btn btn-sm btn-outline-light ms-3' title='Close' style='padding:2px 10px;'>&times;</button>
        </div>
        <div class='card-body'>
            <div><strong>Quiz Question:</strong></div>
            <div class='mb-3 quiz-question-block'>
                ${formatSingleQuestion(quizQ)}
            </div>
            ${htmlQuizMetaBlock(quizData.quiz.topic)}
            <button class='btn apply-quiz-btn' style='background-color:#6c757d !important;color:#fff !important;border:none !important;'>Apply</button>
        </div>
    `;
                // Close logic
                quizResultBlock.querySelector('button[title="Close"]').onclick = function() {
                    quizResultBlock.remove();
                };
                // Apply logic
                // When Apply is clicked, insert the quiz question and trigger Generate automatically
                quizResultBlock.querySelector('.apply-quiz-btn').onclick = function() {
                    document.getElementById('questionContext').value = quizQ;
                    window.scrollTo({top: document.getElementById('questionContext').offsetTop - 80, behavior: 'smooth'});
                    // Trigger the form submission as if user clicked Generate
                    form.requestSubmit(); // Modern browsers support requestSubmit for native submit
                };
                // Set provider color for header
                quizResultBlock.querySelector('.card-header').style.setProperty('background-color', getProviderColor(selectedProvider), 'important');
                // Quiz question now rendered as HTML block, no textarea/auto-resize needed
                quizResultDiv.appendChild(quizResultBlock);
                quizResultDiv.style.display = 'block';
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
        // Add question draft (questionContext) to data for generate as 'question'
        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            provider: selectedProvider,
            model: selectedModel,
            // number: 1, // 'number' is not part of GenerateRequest or ValidateRequest
            validation: document.getElementById('validation').checked,
            question: document.getElementById('questionContext').value.trim()
        };
        // Removed 'questionContext' field, now using 'question' for backend compatibility
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

    // Render meta info block (platform, technology, topic) for quiz/generate
    // obj: expects { platform, technology, name/topic }
    function htmlQuizMetaBlock(obj) {
        if (!obj) return '';
        const platform = obj.platform || '';
        const technology = obj.technology || '';
        const topic = obj.name || obj.topic || '';
        if (!platform && !technology && !topic) return '';
        // Meta block: align right, white background for badges
        return `<div class='mb-2' style="text-align:right;">
            <span class='badge' style="background:#e9f4fb; color:#4fa6d3; border:1px solid #b6e2fa; margin-right:0.3em;">Platform: ${escapeHtml(platform)}</span>
            <span class='badge' style="background:#e9f4fb; color:#4fa6d3; border:1px solid #b6e2fa; margin-right:0.3em;">Technology: ${escapeHtml(technology)}</span>
            <span class='badge' style="background:#e9f4fb; color:#4fa6d3; border:1px solid #b6e2fa;">Topic: ${escapeHtml(topic)}</span>
        </div>`;
    }

    // Display generated question(s)
    function displayGenerationResult(data) {
        const resultDiv = document.getElementById('result');
        if (!resultDiv) return;

        // Defensive: handle invalid/malformed data
        if (!data || typeof data !== 'object') {
            handleApiError('response_format_error', 'Received unexpected format for generated question.');
            return;
        }

        // Clear result div
        resultDiv.textContent = '';

        // Create main container with flex layout
        const mainContainer = document.createElement('div');
        mainContainer.className = 'd-flex flex-column';
        resultDiv.appendChild(mainContainer);

        // Create toolbar container with flex layout
        const toolbarContainer = document.createElement('div');
        toolbarContainer.className = 'd-flex justify-content-between align-items-center mb-2';
        mainContainer.appendChild(toolbarContainer);

        // Create left toolbar section for toggle button
        const leftToolbar = document.createElement('div');
        leftToolbar.className = 'd-flex align-items-center';

        // Create output format toggle button
        const formatToggleBtn = document.createElement('button');
        formatToggleBtn.id = 'resultFormatToggle';
        formatToggleBtn.className = 'btn btn-outline-secondary btn-sm';
        formatToggleBtn.innerHTML = '<i class="bi bi-list-task"></i>'; // Formatted view icon
        formatToggleBtn.title = 'Toggle result format';
        leftToolbar.appendChild(formatToggleBtn);

        // Create right toolbar section for stats
        const rightToolbar = document.createElement('div');
        rightToolbar.className = 'text-muted text-end';
        rightToolbar.style.minWidth = '180px';

        // Add stats if available
        if (data.agent && data.agent.statistic) {
            const { tokens, time } = data.agent.statistic;
            let statLine = '';
            if (typeof tokens === 'number') {
                statLine += `Tokens used: <b>${tokens}</b>`;
            }
            if (typeof time === 'number') {
                if (statLine) statLine += ' | ';
                statLine += `Time: <b>${(time / 1000).toFixed(2)}s</b>`;
            }
            if (statLine) {
                rightToolbar.innerHTML = statLine;
            }
        }

        // Add toolbar sections to toolbar container
        toolbarContainer.appendChild(leftToolbar);
        toolbarContainer.appendChild(rightToolbar);

        // Create content container with border
        const contentDiv = document.createElement('div');
        contentDiv.className = 'result-content border rounded p-3';
        mainContainer.appendChild(contentDiv);

        // Track current display mode
        let isJsonView = false;

        // Function to update content based on view mode
        const updateContent = () => {
            if (isJsonView) {
                // In JSON view, show the complete data structure
                const jsonStr = JSON.stringify(data, null, 2);
                // Create container
                const container = document.createElement('div');
                container.className = 'position-relative';
                
                // Create copy button
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
                copyBtn.style.zIndex = '1';
                copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
                copyBtn.addEventListener('click', () => copyToClipboard(copyBtn, jsonStr));
                
                // Create pre and code elements
                const pre = document.createElement('pre');
                pre.className = 'p-2 rounded line-numbers language-json';
                pre.style.marginBottom = '0';
                pre.style.whiteSpace = 'pre-wrap';
                pre.style.wordWrap = 'break-word';
                
                const code = document.createElement('code');
                code.className = 'language-json';
                code.textContent = jsonStr;
                
                // Assemble elements
                pre.appendChild(code);
                container.appendChild(copyBtn);
                container.appendChild(pre);
                contentDiv.innerHTML = '';
                contentDiv.appendChild(container);
                // Ensure PrismJS highlights and adds line numbers
                setTimeout(() => {
                    const preElement = contentDiv.querySelector('pre');
                    if (preElement) {
                        if (!preElement.hasAttribute('data-prism-highlighted')) {
                            preElement.setAttribute('data-prism-highlighted', 'true');
                            if (window.Prism) {
                                // Ensure the language class is properly set
                                const codeElement = preElement.querySelector('code');
                                if (codeElement && !codeElement.classList.contains('language-json')) {
                                    codeElement.classList.add('language-json');
                                }
                                // Apply highlighting
                                Prism.highlightElement(preElement);
                            }
                        }
                    }
                }, 0);
            } else {
                // In formatted view, show the formatted content with tabs
                let formattedContent = '';
                
                // Add answer levels (tabs) if present
                const levels = data.answerLevels || (data.question && data.question.answerLevels) || {};
                if (Object.keys(levels).length > 0) {
                    formattedContent = formatResult(data);
                } else {
                    // If no answer levels, format the question directly
                    const questionText = data.question ? 
                        (typeof data.question === 'string' ? data.question : data.question.text) : 
                        (data.questions && data.questions.length > 0 ? data.questions[0] : null);
                    
                    if (questionText) {
                        formattedContent = formatSingleQuestion(questionText);
                    } else {
                        formattedContent = '<div class="alert alert-warning">No question content found.</div>';
                    }
                }
                
                contentDiv.innerHTML = formattedContent;
                
                // Highlight code blocks in formatted view
                setTimeout(() => {
                    const codeBlocks = contentDiv.querySelectorAll('pre code');
                    codeBlocks.forEach(block => {
                        if (!block.closest('[data-prism-highlighted]')) {
                            const preElement = block.closest('pre');
                            if (preElement) {
                                preElement.setAttribute('data-prism-highlighted', 'true');
                                if (window.Prism) {
                                    Prism.highlightElement(block);
                                }
                            }
                        }
                    });
                }, 0);
            }
        };

        // Add click handler for toggle button
        formatToggleBtn.addEventListener('click', () => {
            isJsonView = !isJsonView;
            formatToggleBtn.innerHTML = isJsonView 
                ? '<i class="bi bi-code-slash"></i>' 
                : '<i class="bi bi-list-task"></i>';
            updateContent();
        });

        // Show initial content
        updateContent();

        // Answer levels (tabs)
        const levels = data.answerLevels || (data.question && data.question.answerLevels) || {};
        const tabOrder = ['beginner', 'intermediate', 'advanced'];
        let tabs = '';
        let tabContent = '';
        let first = true;
        const levelColors = {
            beginner: {tab: 'text-success', border: 'border-success', bg: 'bg-success bg-opacity-10'},
            intermediate: {tab: 'text-warning', border: 'border-warning', bg: 'bg-warning bg-opacity-10'},
            advanced: {tab: 'text-danger', border: 'border-danger', bg: 'bg-danger bg-opacity-10'}
        };

        // Only proceed with tabs if we have answer levels
        if (Object.keys(levels).length > 0) {
            tabs = '<ul class="nav nav-tabs mb-2" id="answerLevelTabs" role="tablist">';
            tabOrder.forEach(level => {
                if (levels[level]) {
                    const colorClass = levelColors[level] ? levelColors[level].tab : '';
                    tabs += `<li class="nav-item" role="presentation">
                        <button class="nav-link ${colorClass}${first ? ' active' : ''}" style="font-weight:600;" id="tab-${level}" data-bs-toggle="tab" data-bs-target="#level-${level}" type="button" role="tab" aria-controls="level-${level}" aria-selected="${first ? 'true' : 'false'}">${level.charAt(0).toUpperCase() + level.slice(1)}</button>
                    </li>`;
                    first = false;
                }
            });
            tabs += '</ul>';

            // Reset first flag for tab content
            first = true;
            tabOrder.forEach(level => {
                const l = levels[level];
                if (!l) return;
                const borderClass = levelColors[level] ? levelColors[level].border : '';
                tabContent += `<div class="tab-pane fade${first ? ' show active' : ''} ${borderClass}" id="level-${level}" role="tabpanel" aria-labelledby="tab-${level}" style="border-left-width:4px; border-left-style:solid; border-radius:0 0 8px 8px; margin-bottom:1rem; background:none;">`;
                
                // Evaluation criteria
                if (l.evaluationCriteria && l.evaluationCriteria.trim() !== '') {
                    tabContent += `<div class="alert alert-info py-2 px-3 mb-2" style="font-size:0.98rem;"><b>Evaluation Criteria:</b><br>${escapeHtml(l.evaluationCriteria)}</div>`;
                }
                
                // Answer
                tabContent += `<div class="mb-2">${formatSingleQuestion(l.answer || '')}</div>`;
                
                // Tests
                if (Array.isArray(l.tests) && l.tests.length > 0) {
                    l.tests.forEach((test, idx) => {
                        tabContent += `<div class="card mb-2"><div class="card-body p-2">
                            <div class="mb-1"><b>Test ${idx+1}:</b></div>
                            <div class="mb-1">${formatSingleQuestion(test.snippet || '')}</div>`;
                        if (Array.isArray(test.options)) {
                            tabContent += '<ul class="list-group mb-1">';
                            const answerIdx = (typeof test.answer === 'string' && /^\d+$/.test(test.answer)) ? (parseInt(test.answer, 10) - 1) : (typeof test.answer === 'number' ? test.answer : -1);
                            const correctClass = level === 'beginner' ? 'list-group-item-success' : (level === 'intermediate' ? 'list-group-item-warning' : (level === 'advanced' ? 'list-group-item-danger' : 'list-group-item-success'));
                            test.options.forEach((opt, i) => {
                                const isCorrect = i === answerIdx;
                                tabContent += `<li class=\"list-group-item${isCorrect ? ' ' + correctClass : ''}\">${escapeHtml(opt)}</li>`;
                            });
                            tabContent += '</ul>';
                        }
                        tabContent += '</div></div>';
                    });
                }
                tabContent += '</div>';
                first = false;
            });

            // Add tabs and content to the container
            if (tabContent) {
                contentDiv.innerHTML += `<div>${tabs}<div class="tab-content">${tabContent}</div></div>`;

                // Setup tab functionality
                setTimeout(() => {
                    // Custom tab styling
                    const updateTabBorderTop = () => {
                        const tabBtns = document.querySelectorAll('#answerLevelTabs .nav-link');
                        tabBtns.forEach(tab => {
                            tab.style.borderTop = '';
                            if (tab.classList.contains('active')) {
                                if (tab.id.includes('beginner')) tab.style.borderTop = '4px solid #28a745';
                                if (tab.id.includes('intermediate')) tab.style.borderTop = '4px solid #ffc107';
                                if (tab.id.includes('advanced')) tab.style.borderTop = '4px solid #dc3545';
                            }
                        });
                    };

                    // Initial border update
                    updateTabBorderTop();

                    // Add listeners for tab changes
                    const tabBtns = document.querySelectorAll('#answerLevelTabs .nav-link');
                    tabBtns.forEach(tab => {
                        tab.addEventListener('shown.bs.tab', updateTabBorderTop);
                    });

                    // Activate Bootstrap tabs
                    if (window.bootstrap && window.bootstrap.Tab) {
                        const tabEls = document.querySelectorAll('#answerLevelTabs button[data-bs-toggle="tab"]');
                        tabEls.forEach(tabEl => {
                            tabEl.addEventListener('click', function (e) {
                                e.preventDefault();
                                const tabTrigger = window.bootstrap.Tab.getOrCreateInstance(tabEl);
                                tabTrigger.show();
                            });
                        });
                    }
                }, 0);
            }
        }
    }

    // ... (rest of the code remains the same)
    // Display validation result
    function displayValidationResult(data) {
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
                    <pre class="bg-light p-2 rounded line-numbers"><code class="language-plaintext">${escapeHtml(feedback)}</code></pre>
                    <p><strong>Confidence:</strong> ${confidence}</p>
                    ${data.original_question ? `<hr><p><strong>Original Question:</strong></p><pre class="bg-light p-2 rounded line-numbers"><code class="language-plaintext">${escapeHtml(data.original_question)}</code></pre>` : ''}
                </div>
            `;
        // Ensure PrismJS highlights and adds line numbers
        setTimeout(function() {
            document.querySelectorAll('pre.line-numbers code').forEach(function(code) {
                if (![...code.classList].some(cls => cls.startsWith('language-'))) {
                    code.classList.add('language-plaintext');
                }
            });
            if (window.Prism && Prism.highlightAll) {
                Prism.highlightAll();
            }
        }, 0);

        // Ensure PrismJS highlights and adds line numbers
        if (window.Prism && Prism.highlightAll) {
            Prism.highlightAll();
        }

        } else {
            handleApiError('response_format_error', 'Received unexpected format for validation result.', JSON.stringify(data));
        }
    }

    // Helper function to copy text to clipboard
    function copyToClipboard(button, text) {
        navigator.clipboard.writeText(text).then(() => {
            const originalHtml = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check2"></i> Copied!';
            button.classList.remove('btn-outline-secondary');
            button.classList.add('btn-success');
            
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.classList.remove('btn-success');
                button.classList.add('btn-outline-secondary');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text:', err);
            button.innerHTML = '<i class="bi bi-x-circle"></i> Error';
            button.classList.remove('btn-outline-secondary');
            button.classList.add('btn-danger');
            
            setTimeout(() => {
                button.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
                button.classList.remove('btn-danger');
                button.classList.add('btn-outline-secondary');
            }, 2000);
        });
    }

    // Helper function to escape HTML
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
        if (!result) {
            return '<div class="alert alert-warning">No result received.</div>';
        }

        // Get the question object and its properties
        const questionObj = result.question || {};
        const questionText = questionObj.text || '';
        const tags = questionObj.tags || [];
        const topicObj = questionObj.topic || {};
        const platform = topicObj.platform || '';
        const technology = topicObj.technology || '';
        const topic = topicObj.name || '';

        // Start building the output HTML
        let outputHtml = '';

        // Add the question section if we have a question
        if (questionText) {
            // Format tags if they exist
            let tagsHtml = '';
            if (Array.isArray(tags) && tags.length > 0) {
                tagsHtml = '<div class="text-end mb-2">' + 
                    tags.map(tag => 
                        `<span class="badge" style="background:#e9f4fb; color:#4fa6d3; border:1px solid #b6e2fa; margin-right:0.3em;">${escapeHtml(tag)}</span>`
                    ).join('') + 
                    '</div>';
            }

            // Format metadata (platform, technology, topic)
            let metaHtml = '';
            if (platform || technology || topic) {
                metaHtml = `<div class="text-end mb-2">`;
                if (topic) {
                    metaHtml += `<span class="badge" style="background:#007bff; color:white; border:none; margin-right:0.3em;">Topic: ${escapeHtml(topic)}</span>`;
                }
                if (platform) {
                    metaHtml += `<span class="badge" style="background:#6610f2; color:white; border:none; margin-right:0.3em;">Platform: ${escapeHtml(platform)}</span>`;
                }
                if (technology) {
                    metaHtml += `<span class="badge" style="background:#6f42c1; color:white; border:none; margin-right:0.3em;">Technology: ${escapeHtml(technology)}</span>`;
                }
                metaHtml += '</div>';
            }

            outputHtml += `
                <div class="mb-3">
                    <div class="mb-3"><strong>${escapeHtml(questionText)}</strong></div>
                    ${tagsHtml}
                    ${metaHtml}
                </div>
            `;
        }

        // Initialize variables for tabs
        const tabOrder = ['beginner', 'intermediate', 'advanced'];
        let tabs = '';
        let tabContent = '';
        let first = true;

        // Get answer levels
        const levels = questionObj.answerLevels || {};
        const levelColors = {
            beginner: {tab: 'text-success', border: 'border-success', bg: 'bg-success bg-opacity-10'},
            intermediate: {tab: 'text-warning', border: 'border-warning', bg: 'bg-warning bg-opacity-10'},
            advanced: {tab: 'text-danger', border: 'border-danger', bg: 'bg-danger bg-opacity-10'}
        };

        if (Object.keys(levels).length > 0) {
            // Create tabs
            tabs = '<ul class="nav nav-tabs mb-2" id="answerLevelTabs" role="tablist">';
            tabOrder.forEach(level => {
                if (levels[level]) {
                    const colorClass = levelColors[level] ? levelColors[level].tab : '';
                    tabs += `<li class="nav-item" role="presentation">
                        <button class="nav-link ${colorClass}${first ? ' active' : ''}" 
                                style="font-weight:600;" 
                                id="tab-${level}" 
                                data-bs-toggle="tab" 
                                data-bs-target="#level-${level}" 
                                type="button" 
                                role="tab" 
                                aria-controls="level-${level}" 
                                aria-selected="${first ? 'true' : 'false'}">
                            ${level.charAt(0).toUpperCase() + level.slice(1)}
                        </button>
                    </li>`;
                    first = false;
                }
            });
            tabs += '</ul>';

            // Create tab content
            first = true;
            tabOrder.forEach(level => {
                const l = levels[level];
                if (!l) return;

                const borderClass = levelColors[level] ? levelColors[level].border : '';
                tabContent += `<div class="tab-pane fade${first ? ' show active' : ''} ${borderClass}" 
                                   id="level-${level}" 
                                   role="tabpanel" 
                                   aria-labelledby="tab-${level}" 
                                   style="border-left-width:4px; border-left-style:solid; border-radius:0 0 8px 8px; margin-bottom:1rem; background:none;">`;

                // Evaluation criteria
                if (l.evaluationCriteria && l.evaluationCriteria.trim() !== '') {
                    tabContent += `<div class="alert alert-info py-2 px-3 mb-2" style="font-size:0.98rem;">
                        <b>Evaluation Criteria:</b><br>${escapeHtml(l.evaluationCriteria)}
                    </div>`;
                }

                // Answer
                tabContent += `<div class="mb-2">${formatSingleQuestion(l.answer || '')}</div>`;

                // Tests
                if (Array.isArray(l.tests) && l.tests.length > 0) {
                    l.tests.forEach((test, idx) => {
                        tabContent += `<div class="card mb-2"><div class="card-body p-2">
                            <div class="mb-1"><b>Test ${idx + 1}:</b></div>
                            <div class="mb-1">${formatSingleQuestion(test.snippet || '')}</div>`;

                        if (Array.isArray(test.options)) {
                            tabContent += '<ul class="list-group mb-1">';
                            const answerIdx = (typeof test.answer === 'string' && /^\d+$/.test(test.answer)) ? 
                                (parseInt(test.answer, 10) - 1) : 
                                (typeof test.answer === 'number' ? test.answer : -1);

                            const correctClass = level === 'beginner' ? 'list-group-item-success' : 
                                (level === 'intermediate' ? 'list-group-item-warning' : 
                                (level === 'advanced' ? 'list-group-item-danger' : 'list-group-item-success'));

                            test.options.forEach((opt, i) => {
                                const isCorrect = i === answerIdx;
                                tabContent += `<li class="list-group-item${isCorrect ? ' ' + correctClass : ''}">${escapeHtml(opt)}</li>`;
                            });
                            tabContent += '</ul>';
                        }
                        tabContent += '</div></div>';
                    });
                }
                tabContent += '</div>';
                first = false;
            });

            outputHtml += `<div>${tabs}<div class="tab-content">${tabContent}</div></div>`;
        }

        // Return the built HTML if we have any content
        if (outputHtml || questionText) {
            return outputHtml;
        }

        return '<div class="alert alert-warning">No questions were generated.</div>';
    }

    // Formats a single question potentially containing code blocks
    // Formats a single question potentially containing code blocks
    function formatSingleQuestion(questionText) {
        if (typeof questionText !== 'string') {
            console.error("formatSingleQuestion expected a string, got:", questionText);
            return '<div class="alert alert-danger">Error displaying question: Invalid format received.</div>';
        }
        // Split the text into code blocks and text parts
        const parts = questionText.split(/(```[\s\S]*?```)/g);
        let formattedHtml = '<div class="generated-question p-3 border rounded shadow-sm">';
        // Language mapping for PrismJS compatibility
        const langMap = {
            objc: 'objectivec',
            'obj-c': 'objectivec',
            objectivec: 'objectivec',
            c: 'c',
            cpp: 'cpp',
            'c++': 'cpp',
            java: 'java',
            swift: 'swift',
            python: 'python',
            dart: 'dart',
            kotlin: 'kotlin',
            glsl: 'glsl',
            metal: 'cpp', // Use cpp as fallback for Metal
            plaintext: 'plaintext'
        };
        parts.forEach(part => {
            if (part.startsWith('```') && part.endsWith('```')) {
                // It's a code block
                const codeContent = part.slice(3, -3).trim(); // Remove ```
                // Extract language hint if present (e.g., ```python)
                const languageMatch = codeContent.match(/^(\w+)\n/);
                let language = 'plaintext'; // Default language
                let code = codeContent;
                if (languageMatch) {
                    const originalLang = languageMatch[1].toLowerCase();
                    language = langMap[originalLang] || originalLang;
                    code = codeContent.substring(languageMatch[0].length); // Code without language hint
                }
                // Add pre/code block with line-numbers and language class
                formattedHtml += `<pre class="bg-light text-dark p-3 rounded mt-2 mb-2 line-numbers" style="font-family: 'Fira Mono', 'Menlo', 'Consolas', monospace; font-size: 1em; overflow-x: auto;"><code class="language-${language}">${escapeHtml(code)}</code></pre>`;
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


    // Loads providers from the backend and populates provider selects
    function loadAgents() {
        fetch('/api/providers')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const providers = data.providers;
                    const providerSelect = document.getElementById('ai');
                    const validationProviderSelect = document.getElementById('validationProvider');
                    
                    // Clear existing options
                    providerSelect.innerHTML = '';
                    validationProviderSelect.innerHTML = '';
                    
                    // Add new options
                    providers.forEach(provider => {
                        const option = document.createElement('option');
                        option.value = provider;
                        option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1); // Capitalize for display
                        providerSelect.appendChild(option);
                        
                        const validationOption = option.cloneNode(true);
                        validationProviderSelect.appendChild(validationOption);
                    });
                    
                    // Trigger change event to load models for selected provider
                    providerSelect.dispatchEvent(new Event('change'));
                } else {
                    console.error('Failed to load providers:', data.error);
                }
            })
            .catch(error => console.error('Error loading providers:', error));
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
});

// Update form submission to include validation settings
document.getElementById('questionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    // Always send 'ai' as the provider in the API request
    
    // Build context as required by backend
    const context = {
        platform: document.getElementById('platform').value,
        technology: document.getElementById('tech').value,
        topic: document.getElementById('topic').value,
        tags: document.getElementById('keywords').value.split(',').map(t => t.trim()).filter(Boolean),
        question: document.getElementById('questionContext').value
    };
    // Main payload for /api/generate
    const formData = {
        provider: document.getElementById('ai').value,
        model: document.getElementById('model').value,
        apiKey: document.getElementById('apiKey').value,
        context: context,
        validation: document.getElementById('validation').checked
    };
    // Add validation settings if needed
    if (formData.validation && !document.getElementById('sameAsGeneration').checked) {
        formData.validationProvider = document.getElementById('validationProvider').value;
        formData.validationModel = document.getElementById('validationModel').value;
        formData.validationApiKey = document.getElementById('validationApiKey').value;
    }
    // Rest of the submission logic...
}); 
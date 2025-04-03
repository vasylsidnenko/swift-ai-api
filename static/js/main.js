document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultDiv = document.getElementById('result');
    const aiSelect = document.getElementById('ai');
    const modelSelect = document.getElementById('model');
    const validationAiSelect = document.getElementById('validationAi');
    const validationModelSelect = document.getElementById('validationModel');
    const validationCheckbox = document.getElementById('validation');
    const useCustomValidationCheckbox = document.getElementById('useCustomValidation');
    const validationAiConfig = document.getElementById('validationAiConfig');
    const validationConfigSection = document.getElementById('validationConfigSection');
    const aiSettingsToggle = document.querySelector('[data-bs-toggle="collapse"]');
    
    // Change icon when expanding/collapsing AI settings block
    if (aiSettingsToggle) {
        const chevronIcon = aiSettingsToggle.querySelector('.bi-chevron-down');
        
        document.getElementById('aiSettings').addEventListener('show.bs.collapse', function () {
            chevronIcon.classList.remove('bi-chevron-down');
            chevronIcon.classList.add('bi-chevron-up');
        });
        
        document.getElementById('aiSettings').addEventListener('hide.bs.collapse', function () {
            chevronIcon.classList.remove('bi-chevron-up');
            chevronIcon.classList.add('bi-chevron-down');
        });
    }
    
    // Load available providers
    async function loadProviders() {
        try {
            const response = await fetch('/api/providers');
            const providers = await response.json();
            
            // Clear providers select
            aiSelect.innerHTML = '';
            
            // Add received providers
            providers.forEach(provider => {
                const option = document.createElement('option');
                option.value = provider;
                
                // Format provider name correctly
                let displayName = '';
                if (provider === 'openai') {
                    displayName = 'OpenAI';
                } else if (provider === 'google') {
                    displayName = 'Google';
                } else if (provider === 'deepseek') {
                    displayName = 'DeepSeek';
                } else {
                    displayName = provider.charAt(0).toUpperCase() + provider.slice(1);
                }
                
                option.textContent = displayName;
                aiSelect.appendChild(option);
            });
            
            // Load models for the first provider
            if (providers.length > 0) {
                loadModels(providers[0]);
            }
        } catch (error) {
            console.error('Error loading providers:', error);
        }
    }
    
    // Load available models for a specific provider
    async function loadModels(provider) {
        try {
            // Load models
            const modelsResponse = await fetch(`/api/models/${provider}`);
            const data = await modelsResponse.json();
            
            // Clear models select
            modelSelect.innerHTML = '';
            
            // Add received models
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                // Set default model
                if (model === data.default) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
            
            // Check if API key exists in environment
            try {
                const keyResponse = await fetch(`/api/check-env-key/${provider}`);
                const keyData = await keyResponse.json();
                
                // If key exists in environment, show credit message and mark input
                if (keyData.exists) {
                    const apiKeyInput = document.getElementById('apiKey');
                    apiKeyInput.value = '********'; // Show masked value to indicate key is present
                    apiKeyInput.placeholder = 'Environment API key is being used';
                    apiKeyInput.classList.add('has-env-key');
                    
                    // Show credit message
                    const apiKeyCredit = document.getElementById('apiKeyCredit');
                    apiKeyCredit.textContent = `Using environment API key - credit ${keyData.credit}`;
                    apiKeyCredit.style.display = 'block';
                } else {
                    // Reset input if no environment key
                    const apiKeyInput = document.getElementById('apiKey');
                    apiKeyInput.value = '';
                    apiKeyInput.placeholder = '';
                    apiKeyInput.classList.remove('has-env-key');
                    
                    // Hide credit message
                    document.getElementById('apiKeyCredit').style.display = 'none';
                }
            } catch (keyError) {
                console.error(`Error checking environment key for ${provider}:`, keyError);
            }
        } catch (error) {
            console.error(`Error loading models for ${provider}:`, error);
        }
    }
    
    // Load providers when page loads
    loadProviders();
    
    // Force hide number of questions field if it exists (to handle cached pages)
    document.addEventListener('DOMContentLoaded', function() {
        const numberFieldContainer = document.querySelector('label[for="number"]')?.closest('.mb-3');
        if (numberFieldContainer) {
            numberFieldContainer.style.display = 'none';
            console.log('Number of questions field hidden');
        }
    });
    
    // Toggle validation config section based on validation checkbox
    validationCheckbox.addEventListener('change', function() {
        validationConfigSection.style.display = this.checked ? 'block' : 'none';
    });
    
    // Toggle custom validation config based on checkbox
    useCustomValidationCheckbox.addEventListener('change', function() {
        validationAiConfig.style.display = this.checked ? 'block' : 'none';
    });

    // Update available models when provider changes
    aiSelect.addEventListener('change', function() {
        const provider = this.value;
        loadModels(provider);
    });
    
    // Update available validation models when validation provider changes
    validationAiSelect.addEventListener('change', function() {
        const provider = this.value;
        loadValidationModels(provider);
    });
    
    // Handle API key input changes
    document.getElementById('apiKey').addEventListener('input', function() {
        // If user enters a custom key, hide the credit message
        if (this.value && this.value !== '********') {
            document.getElementById('apiKeyCredit').style.display = 'none';
        }
    });
    
    // Handle validation API key input changes
    document.getElementById('validationApiKey').addEventListener('input', function() {
        // If user enters a custom key, hide the credit message
        if (this.value && this.value !== '********') {
            document.getElementById('validationApiKeyCredit').style.display = 'none';
        }
    });
    
    // Load validation models for a specific provider
    async function loadValidationModels(provider) {
        try {
            // Load models
            const modelsResponse = await fetch(`/api/models/${provider}`);
            const data = await modelsResponse.json();
            
            // Clear models select
            validationModelSelect.innerHTML = '';
            
            // Add received models
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                // Set default model
                if (model === data.default) {
                    option.selected = true;
                }
                validationModelSelect.appendChild(option);
            });
            
            // Check if API key exists in environment
            try {
                const keyResponse = await fetch(`/api/check-env-key/${provider}`);
                const keyData = await keyResponse.json();
                
                // If key exists in environment, show credit message and mark input
                if (keyData.exists) {
                    const apiKeyInput = document.getElementById('validationApiKey');
                    apiKeyInput.value = '********'; // Show masked value to indicate key is present
                    apiKeyInput.placeholder = 'Environment API key is being used';
                    apiKeyInput.classList.add('has-env-key');
                    
                    // Show credit message
                    const apiKeyCredit = document.getElementById('validationApiKeyCredit');
                    apiKeyCredit.textContent = `Using environment API key - credit ${keyData.credit}`;
                    apiKeyCredit.style.display = 'block';
                } else {
                    // Reset input if no environment key
                    const apiKeyInput = document.getElementById('validationApiKey');
                    apiKeyInput.value = '';
                    apiKeyInput.placeholder = '';
                    apiKeyInput.classList.remove('has-env-key');
                    
                    // Hide credit message
                    document.getElementById('validationApiKeyCredit').style.display = 'none';
                }
            } catch (keyError) {
                console.error(`Error checking environment key for ${provider}:`, keyError);
            }
        } catch (error) {
            console.error(`Error loading validation models for ${provider}:`, error);
        }
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading indicator immediately after button click
        resultDiv.innerHTML = `
            <div class="loading-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text mt-3">Generating questions...</div>
            </div>
        `;
        
        // Create basic data object
        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            validation: document.getElementById('validation').checked
        };
        
        // Add AI config
        data.ai_config = {
            ai: document.getElementById('ai').value,
            model: document.getElementById('model').value
        };
        
        // Get API key for main generation
        const apiKey = document.getElementById('apiKey').value.trim();
        if (apiKey && apiKey !== '********') {
            data.ai_config.api_key = apiKey;
        }
        
        // Add validation AI config if custom validation is enabled
        if (data.validation && document.getElementById('useCustomValidation').checked) {
            data.validation_ai_config = {
                ai: document.getElementById('validationAi').value,
                model: document.getElementById('validationModel').value
            };
            
            // Get API key for validation
            const validationApiKey = document.getElementById('validationApiKey').value.trim();
            if (validationApiKey && validationApiKey !== '********') {
                data.validation_ai_config.api_key = validationApiKey;
            }
        }

        try {

            // Create headers
            const headers = {
                'Content-Type': 'application/json'
            };
            
            // Add Authorization header if API key exists and is not the placeholder
            const mainApiKey = document.getElementById('apiKey').value.trim();
            if (mainApiKey && mainApiKey !== '********') {
                headers['Authorization'] = `Bearer ${mainApiKey}`;
            }

            const response = await fetch('/generate_question', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.error) {
                // Parse the error message to provide more specific feedback
                let errorMessage = result.error;
                let errorType = result.error_type || 'error';
                let errorTitle = 'Error';
                let errorDetails = '';
                
                console.log('Error detected:', errorMessage, 'Type:', errorType);
                
                // Check for common error types
                if (errorType === 'api_key' || errorMessage.toLowerCase().includes('api key') || errorMessage.toLowerCase().includes('incorrect api key')) {
                    errorType = 'api-key';
                    errorTitle = 'API Key Error';
                    errorDetails = 'Please check that your API key is valid and has sufficient permissions.';
                    
                    // For OpenAI API key errors, extract the exact error message
                    if (errorMessage.includes('Incorrect API key provided')) {
                        // Keep the original error message as is
                        errorDetails = 'Please enter a valid API key or remove the current key to use the environment variable.';
                    }
                } else if (errorType === 'empty_response') {
                    errorType = 'api-error';
                    errorTitle = 'API Error';
                    errorDetails = 'The API returned an empty response. This often indicates an issue with your API key or account.';
                } else if (errorMessage.toLowerCase().includes('validation')) {
                    errorType = 'validation';
                    errorTitle = 'Validation Error';
                    errorDetails = 'The generated content did not pass validation. Try adjusting your parameters.';
                } else if (errorMessage.toLowerCase().includes('rate limit')) {
                    errorType = 'rate-limit';
                    errorTitle = 'Rate Limit Exceeded';
                    errorDetails = 'You have exceeded the rate limit for the API. Please try again later.';
                } else if (errorMessage.toLowerCase().includes('timeout') || errorMessage.toLowerCase().includes('timed out')) {
                    errorType = 'timeout';
                    errorTitle = 'Request Timeout';
                    errorDetails = 'The request took too long to complete. Try again or use a different model.';
                }
                
                // Display a more informative error message
                resultDiv.innerHTML = `
                    <div class="alert alert-danger error-container">
                        <h4 class="alert-heading">${errorTitle}</h4>
                        <p>${errorMessage}</p>
                        ${errorDetails ? `<hr><p class="mb-0">${errorDetails}</p>` : ''}
                    </div>
                `;
                
                console.log('Error displayed with title:', errorTitle);
            } else {
                const formattedResult = formatResult(result);
                resultDiv.innerHTML = formattedResult;
                // Highlight syntax after adding content
                Prism.highlightAll();
            }
        } catch (error) {
            // Handle network errors and other exceptions
            let errorTitle = 'Connection Error';
            let errorMessage = error.message || 'An unknown error occurred';
            let errorDetails = 'There was a problem connecting to the server. Please check your internet connection and try again.';
            
            if (errorMessage.includes('Failed to fetch')) {
                errorTitle = 'Network Error';
                errorDetails = 'Could not connect to the server. Please check your internet connection.';
            } else if (errorMessage.includes('Unexpected token')) {
                errorTitle = 'Response Format Error';
                errorDetails = 'The server response was not in the expected format. Please try again later.';
            }
            
            resultDiv.innerHTML = `
                <div class="alert alert-danger error-container">
                    <h4 class="alert-heading">${errorTitle}</h4>
                    <p>${errorMessage}</p>
                    <hr>
                    <p class="mb-0">${errorDetails}</p>
                </div>
            `;
        }
    });

    function formatCode(text) {
        if (!text) return '';
        
        // Handle text for code block formatting
        let formattedText = text;
        
        // Debug log for code formatting
        console.log('Formatting code with syntax highlighting');
        
        // Check for opening triple backticks without closing
        const openingBackticksCount = (formattedText.match(/```([a-zA-Z0-9_\-+#]*)/g) || []).length;
        const closingBackticksCount = (formattedText.match(/```\s*$/gm) || []).length;
        
        console.log(`Opening backticks: ${openingBackticksCount}, Closing backticks: ${closingBackticksCount}`);
        
        // If there are opening triple backticks without closing, add closing
        if (openingBackticksCount > closingBackticksCount) {
            // Find all opening triple backticks
            const codeBlocks = formattedText.match(/```([a-zA-Z0-9_\-+#]*)\n?([\s\S]*?)(?=(```|$))/gi) || [];
            
            // Add closing triple backticks to each block if they are missing
            codeBlocks.forEach(block => {
                if (!block.endsWith('```')) {
                    const newBlock = block + '\n```';
                    formattedText = formattedText.replace(block, newBlock);
                }
            });
        }
        
        // Map of common language identifiers to their Prism.js language classes
        const languageMap = {
            // Apple platforms
            'swift': 'language-swift',
            'objc': 'language-objectivec',
            'objectivec': 'language-objectivec',
            'objective-c': 'language-objectivec',
            'c': 'language-c',
            'cpp': 'language-cpp',
            'c++': 'language-cpp',
            'metal': 'language-cpp', // Metal uses C++ syntax
            'opengl': 'language-glsl', // OpenGL uses GLSL
            
            // Android platforms
            'java': 'language-java',
            'kotlin': 'language-kotlin',
            'groovy': 'language-groovy',
            'gradle': 'language-gradle',
            'xml': 'language-xml',
            
            // Web and general
            'js': 'language-javascript',
            'javascript': 'language-javascript',
            'ts': 'language-typescript',
            'typescript': 'language-typescript',
            'html': 'language-html',
            'css': 'language-css',
            'sass': 'language-sass',
            'scss': 'language-scss',
            'json': 'language-json',
            'yaml': 'language-yaml',
            'yml': 'language-yaml',
            'bash': 'language-bash',
            'sh': 'language-bash',
            'shell': 'language-bash',
            'python': 'language-python',
            'py': 'language-python',
            'ruby': 'language-ruby',
            'rb': 'language-ruby',
            'go': 'language-go',
            'golang': 'language-go',
            'rust': 'language-rust',
            'php': 'language-php',
            'sql': 'language-sql',
            'csharp': 'language-csharp',
            'cs': 'language-csharp',
            'dart': 'language-dart',
            'powershell': 'language-powershell',
            'ps': 'language-powershell'
        };
        
        // First process code blocks with triple backticks
        formattedText = formattedText.replace(/```([a-zA-Z0-9_\-+#]*)\n?([\s\S]*?)```/gi, (match, lang, code) => {
            // Remove extra spaces and line breaks
            const cleanCode = code.trim();
            
            // Default to plaintext if language is not specified
            let langClass = 'language-plaintext';
            
            if (lang) {
                // Normalize language name and map to Prism.js class
                const normalizedLang = lang.toLowerCase().trim();
                console.log(`Detected code block with language: '${normalizedLang}'`);
                
                // Use displayed language class if available, otherwise use normalized language
                langClass = languageMap[normalizedLang] || `language-${normalizedLang}`;
                console.log(`Using language class: ${langClass} for code block`);
            }
            
            // Ensure code is properly escaped for HTML and preserves line breaks
            const escapedCode = cleanCode
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
            
            return `<pre class="line-numbers ${langClass}"><code>${escapedCode}</code></pre>`;
        });
        
        //  Additional handling for cases where code is not wrapped in triple backticks,
        // but contains single-line code blocks with language names (e.g., "swift let counter = 0")
        const codePatterns = [
            // Template for Swift
            { pattern: /\b(swift)\s+([^\n]+)/gi, lang: 'swift' },
            // Template for Objective-C
            { pattern: /\b(objc|objective-c|objectivec)\s+([^\n]+)/gi, lang: 'objectivec' },
            // Template for Java
            { pattern: /\b(java)\s+([^\n]+)/gi, lang: 'java' },
            // Template for Kotlin
            { pattern: /\b(kotlin)\s+([^\n]+)/gi, lang: 'kotlin' },
            // Add other languages as needed
        ];
        
        // Apply templates for detecting and formatting single-line code blocks
        codePatterns.forEach(({ pattern, lang }) => {
            formattedText = formattedText.replace(pattern, (match, langName, code) => {
                const normalizedLang = langName.toLowerCase();
                const langClass = languageMap[normalizedLang] || `language-${normalizedLang}`;
                
                // Ensure code is properly escaped for HTML
                const escapedCode = code.trim()
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#039;');
                
                return `<pre class="line-numbers ${langClass}"><code>${escapedCode}</code></pre>`;
            });
        });
        
        return formattedText;
    }

    function formatResult(result) {
        if (!Array.isArray(result)) {
            console.error('Result is not an array:', result);
            return '<div class="alert alert-danger">Invalid result format</div>';
        }

        console.log('Full result structure:', JSON.stringify(result, null, 2));
        
        // If there's only one question, display it normally
        if (result.length === 1) {
            console.log('Processing single question:', result[0]);
            console.log('Validation data in result:', result[0].validation_result);
            
            const html = formatSingleQuestion(result[0]);
            // Initialize Prism.js after content insertion
            setTimeout(() => {
                if (window.Prism) {
                    Prism.highlightAll();
                }
            }, 100);
            return html;
        }

        // For multiple questions, use tabs
        let tabsHtml = `
            <ul class="nav nav-tabs" id="questionTabs" role="tablist">
        `;

        let tabContentHtml = `
            <div class="tab-content" id="questionTabsContent">
        `;

        // Generate tabs and content
        result.forEach((question, index) => {
            if (!question || !question.answerLevels) {
                console.error('Invalid question format:', question);
                return;
            }

            const isActive = index === 0 ? 'active' : '';
            const tabId = `question-${index}`;
            
            // Tab header
            tabsHtml += `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${isActive}" id="${tabId}-tab" data-bs-toggle="tab" 
                            data-bs-target="#${tabId}" type="button" role="tab" 
                            aria-controls="${tabId}" aria-selected="${index === 0}">
                        Question ${index + 1}
                    </button>
                </li>
            `;

            // Tab content
            tabContentHtml += `
                <div class="tab-pane fade show ${isActive}" id="${tabId}" role="tabpanel" aria-labelledby="${tabId}-tab">
                    ${formatSingleQuestion(question)}
                </div>
            `;
        });

        tabsHtml += `</ul>`;
        tabContentHtml += `</div>`;

        // Initialize Prism.js after content insertion
        setTimeout(() => {
            if (window.Prism) {
                Prism.highlightAll();
            }
        }, 100);

        return tabsHtml + tabContentHtml;
    }

    function formatSingleQuestion(question) {
        console.log('Formatting question:', question);
        
        // Add validation block at the beginning of the response
        let validationHtml = '';
        
        // Check for validation data
        if (question.validation_result) {
            console.log('Found validation_result at top level:', question.validation_result);
            
            // Create validation block
            const validationData = question.validation_result;
            const validation = validationData.validation || {};
            
            if (validation) {
                const validationId = `validation-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
                const validationResult = validationData.result || '';
                const isPassed = (validationResult === 'PASS' || validation.passed);
                const validationClass = isPassed ? 'validation-passed' : 'validation-failed';
                const score = validation.quality_score || 0;
                const statusIcon = isPassed ? 'check-circle' : 'exclamation-triangle';
                const statusText = isPassed ? 'Validation Passed' : 'Validation Failed';
                
                // Додаємо інформацію про токени та час
                const tokenUsage = question.token_usage || {};
                const totalTokens = tokenUsage.total_tokens || 0;
                const promptTokens = tokenUsage.prompt_tokens || 0;
                const completionTokens = tokenUsage.completion_tokens || 0;
                const processingTime = question.agent?.time || 0;
                const totalRequestTime = question.agent?.time ? (question.agent.time / 1000).toFixed(2) : 0;
                
                validationHtml = `
                    <div class="validation-container">
                        <button class="btn btn-sm btn-outline-secondary validation-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#${validationId}" aria-expanded="false">
                            <i class="bi bi-${statusIcon}"></i> ${statusText} - Quality Score: ${score}/10
                            ${totalTokens > 0 ? `<span class="token-info"><i class="bi bi-cpu"></i> ${totalTokens} tokens</span>` : ''}
                            ${totalRequestTime > 0 ? `<span class="time-info"><i class="bi bi-hourglass-split"></i> ${totalRequestTime}s</span>` : ''}
                            <i class="bi bi-chevron-down ms-2"></i>
                        </button>
                        <div class="collapse" id="${validationId}">
                            <div class="card card-body validation-details ${validationClass}">
                                <h5>Validation Results</h5>
                                ${totalTokens > 0 ? `
                                    <div class="token-details-section">
                                        <h6>Token Usage</h6>
                                        <ul>
                                            <li>Total Tokens: ${totalTokens}</li>
                                            <li>Prompt Tokens: ${promptTokens}</li>
                                            <li>Completion Tokens: ${completionTokens}</li>
                                        </ul>
                                    </div>
                                ` : ''}
                                ${processingTime > 0 || totalRequestTime > 0 ? `
                                    <div class="time-details-section">
                                        <h6>Processing Time</h6>
                                        <ul>
                                            ${processingTime > 0 ? `<li>Processing Time: ${processingTime}s</li>` : ''}
                                            ${totalRequestTime > 0 ? `<li>Total Request Time: ${totalRequestTime}s</li>` : ''}
                                        </ul>
                                    </div>
                                ` : ''}
                                <ul class="validation-list">
                                    ${validation.is_text_clear === false ? `<li class="failed">Question text is clear and specific</li>` : ''}
                                    ${validation.is_question_correspond === false ? `<li class="failed">Question corresponds to topic and tags</li>` : ''}
                                    ${validation.is_question_not_trivial === false ? `<li class="failed">Question is challenging enough</li>` : ''}
                                    ${validation.do_answer_levels_exist === false ? `<li class="failed">All three difficulty levels exist</li>` : ''}
                                    ${validation.are_answer_levels_valid === false ? `<li class="failed">Answer levels are valid</li>` : ''}
                                    ${validation.has_evaluation_criteria === false ? `<li class="failed">Each level has evaluation criteria</li>` : ''}
                                    ${validation.are_answer_levels_different === false ? `<li class="failed">Answer levels are sufficiently different</li>` : ''}
                                    ${validation.do_tests_exist === false ? `<li class="failed">Each level has tests</li>` : ''}
                                    ${validation.do_tags_exist === false ? `<li class="failed">Question has appropriate tags</li>` : ''}
                                    ${validation.do_test_options_exist === false ? `<li class="failed">All tests have more than 2 options</li>` : ''}
                                    ${validation.is_question_text_different_from_existing_questions === false ? `<li class="failed">Question text is original</li>` : ''}
                                    ${validation.are_test_options_numbered === false ? `<li class="failed">Test options are properly numbered</li>` : ''}
                                    ${validation.does_answer_contain_option_number === false ? `<li class="failed">Test answers correspond to valid options</li>` : ''}
                                    ${validation.are_code_blocks_marked_if_they_exist === false ? `<li class="failed">Code blocks are properly formatted</li>` : ''}
                                    ${validation.does_snippet_have_question === false ? `<li class="failed">Each test snippet has a question</li>` : ''}
                                    ${validation.does_snippet_have_code === false ? `<li class="failed">Each test snippet has code</li>` : ''}
                                    ${isPassed ? `<li class="passed">All validation checks passed!</li>` : ''}
                                </ul>
                                
                                <div class="validation-comments">
                                    <button class="btn btn-sm btn-outline-primary criteria-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#validationComments-${validationId}" aria-expanded="false">
                                        <i class="bi bi-chat-left-text"></i> Validation Comments
                                        <i class="bi bi-chevron-down ms-2"></i>
                                    </button>
                                    <div class="collapse" id="validationComments-${validationId}">
                                        <div class="card card-body validation-comments-content">
                                            ${formatCode(validationData.comments || 'No comments provided')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        // Check if the question is in the new format (with question field)
        if (question.question) {
            // If we have a nested question object, use that
            const nestedResult = formatSingleQuestion(question.question);
            // Add validation block at the beginning of the response
            return validationHtml + nestedResult;
        }
        
        if (!question || !question.answerLevels) {
            console.error('Invalid question format:', question);
            return '<div class="alert alert-danger">Invalid question format. Please check the console for details.</div>';
        }
        
        // Check for validation in both old and new formats
        const validationData = question.validation_result || question.validation;
        
        console.log('Question object:', question);
        console.log('Looking for validation data in:', question.validation_result, question.validation);
        
        // Always show validation block if validation data is present
        if (validationData) {
            console.log('Validation data found:', validationData);
            
            // Get the actual validation object (may be nested)
            const validation = validationData.validation || validationData;
            
            // Debug validation data
            console.log('Validation object:', validation);
            console.log('Validation result:', validationData.result);
            console.log('Validation data structure:', JSON.stringify(validationData, null, 2));
            
            // Check for presence of required fields
            const hasValidationFields = validation && (typeof validation === 'object');
            console.log('Has validation fields:', hasValidationFields);
        }
        
        // Format processing time and token usage if available
        let processingTimeHtml = '';
        let tokenUsageHtml = '';
        
        // Add processing time info
        if (question.processing_time || question.total_request_time) {
            processingTimeHtml = `
                <div class="processing-time-info">
                    ${question.total_request_time ? `<span title="Total time including generation, validation, initialization and network overhead"><i class="bi bi-hourglass-split"></i> Total request time: ${question.total_request_time}s</span>` : ''}
                </div>
            `;
        }
        
        // Add token usage info if available
        if (question.token_usage) {
            const tokenUsage = question.token_usage;
            const promptTokens = tokenUsage.prompt_tokens || 0;
            const completionTokens = tokenUsage.completion_tokens || 0;
            const totalTokens = tokenUsage.total_tokens || 0;
            
            tokenUsageHtml = `
                <div class="token-usage-info">
                    <span title="Number of tokens used in this request">
                        <i class="bi bi-cpu"></i> Tokens: ${totalTokens} total 
                        <span class="token-details">(${promptTokens} prompt, ${completionTokens} completion)</span>
                    </span>
                </div>
            `;
        }

        // Create tabs for different difficulty levels
        console.log('Final validation HTML:', validationHtml);
        
        return `
            <div class="question-block">
                <div class="question-title">${window.formatQuestionText ? window.formatQuestionText(question.text) : (question.text || 'No question text')}</div>
                <div class="question-tags">
                    ${(question.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                ${processingTimeHtml}
                ${tokenUsageHtml}
                
                <!-- Difficulty Level Tabs -->
                <div class="difficulty-tabs">
                    <ul class="nav nav-tabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="beginner-tab" data-bs-toggle="tab" data-bs-target="#beginner-content" 
                                type="button" role="tab" aria-controls="beginner-content" aria-selected="true">
                                ${question.answerLevels.beginer?.name || 'Beginner'}
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="intermediate-tab" data-bs-toggle="tab" data-bs-target="#intermediate-content" 
                                type="button" role="tab" aria-controls="intermediate-content" aria-selected="false">
                                ${question.answerLevels.intermediate?.name || 'Intermediate'}
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="advanced-tab" data-bs-toggle="tab" data-bs-target="#advanced-content" 
                                type="button" role="tab" aria-controls="advanced-content" aria-selected="false">
                                ${question.answerLevels.advanced?.name || 'Advanced'}
                            </button>
                        </li>
                    </ul>
                    
                    <!-- Tab Content -->
                    <div class="tab-content">
                        <!-- Beginner Level -->
                        <div class="tab-pane fade show active" id="beginner-content" role="tabpanel" aria-labelledby="beginner-tab">
                            <div class="answer-level beginner">
                                ${question.answerLevels.beginer?.evaluation_criteria ? `
                                    <div class="criteria-container">
                                        <button class="btn btn-sm btn-outline-primary criteria-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#beginnerCriteria" aria-expanded="false">
                                            <i class="bi bi-info-circle"></i> Show Evaluation Criteria
                                        </button>
                                        <div class="collapse criteria-content" id="beginnerCriteria">
                                            <div class="card card-body criteria-card">
                                                <h6>Evaluation Criteria:</h6>
                                                <p>${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.beginer.evaluation_criteria) : question.answerLevels.beginer.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.beginer?.answer) : (question.answerLevels.beginer?.answer || '')}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.beginer?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${window.formatQuestionText ? window.formatQuestionText(test.snippet) : (test.snippet || '')}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${window.formatQuestionText ? window.formatQuestionText(option) : option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${window.formatQuestionText ? window.formatQuestionText(test.answer) : (test.answer || 'Not specified')}</strong>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <!-- Intermediate Level -->
                        <div class="tab-pane fade" id="intermediate-content" role="tabpanel" aria-labelledby="intermediate-tab">
                            <div class="answer-level intermediate">
                                ${question.answerLevels.intermediate?.evaluation_criteria ? `
                                    <div class="criteria-container">
                                        <button class="btn btn-sm btn-outline-primary criteria-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#intermediateCriteria" aria-expanded="false">
                                            <i class="bi bi-info-circle"></i> Show Evaluation Criteria
                                        </button>
                                        <div class="collapse criteria-content" id="intermediateCriteria">
                                            <div class="card card-body criteria-card">
                                                <h6>Evaluation Criteria:</h6>
                                                <p>${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.intermediate.evaluation_criteria) : question.answerLevels.intermediate.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.intermediate?.answer) : (question.answerLevels.intermediate?.answer || '')}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.intermediate?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${window.formatQuestionText ? window.formatQuestionText(test.snippet) : (test.snippet || '')}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${window.formatQuestionText ? window.formatQuestionText(option) : option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${window.formatQuestionText ? window.formatQuestionText(test.answer) : (test.answer || 'Not specified')}</strong>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <!-- Advanced Level -->
                        <div class="tab-pane fade" id="advanced-content" role="tabpanel" aria-labelledby="advanced-tab">
                            <div class="answer-level advanced">
                                ${question.answerLevels.advanced?.evaluation_criteria ? `
                                    <div class="criteria-container">
                                        <button class="btn btn-sm btn-outline-primary criteria-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#advancedCriteria" aria-expanded="false">
                                            <i class="bi bi-info-circle"></i> Show Evaluation Criteria
                                        </button>
                                        <div class="collapse criteria-content" id="advancedCriteria">
                                            <div class="card card-body criteria-card">
                                                <h6>Evaluation Criteria:</h6>
                                                <p>${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.advanced.evaluation_criteria) : question.answerLevels.advanced.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${window.formatQuestionText ? window.formatQuestionText(question.answerLevels.advanced?.answer) : (question.answerLevels.advanced?.answer || '')}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.advanced?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${window.formatQuestionText ? window.formatQuestionText(test.snippet) : (test.snippet || '')}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${window.formatQuestionText ? window.formatQuestionText(option) : option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${window.formatQuestionText ? window.formatQuestionText(test.answer) : (test.answer || 'Not specified')}</strong>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Initialize Prism.js for syntax highlighting
        setTimeout(() => {
            if (window.Prism) {
                console.log('Initializing Prism.js for syntax highlighting');
                try {
                    Prism.highlightAll();
                    console.log('Prism.js initialization completed');
                } catch (error) {
                    console.error('Error initializing Prism.js:', error);
                }
            } else {
                console.warn('Prism.js not available');
            }
        }, 100);
        
        // Re-initialize Prism.js after 500ms for cases where content is loaded with delay
        setTimeout(() => {
            if (window.Prism) {
                try {
                    Prism.highlightAll();
                    console.log('Prism.js re-initialization completed');
                } catch (error) {
                    console.error('Error re-initializing Prism.js:', error);
                }
            }
        }, 500);
    }
}); 
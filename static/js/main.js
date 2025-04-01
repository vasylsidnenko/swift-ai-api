document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultDiv = document.getElementById('result');
    const aiSelect = document.getElementById('ai');
    const modelSelect = document.getElementById('model');
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

    // Update available models when provider changes
    aiSelect.addEventListener('change', function() {
        const provider = this.value;
        loadModels(provider);
    });
    
    // Handle API key input changes
    document.getElementById('apiKey').addEventListener('input', function() {
        // If user enters a custom key, hide the credit message
        if (this.value && this.value !== '********') {
            document.getElementById('apiKeyCredit').style.display = 'none';
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            ai: document.getElementById('ai').value,
            model: document.getElementById('model').value,
            number: 1, // Always set to 1
            validation: document.getElementById('validation').checked
        };

        try {
            // Show loading indicator
            resultDiv.innerHTML = `
                <div class="loading-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="loading-text mt-3">Generating questions...</div>
                </div>
            `;

            // Get API key
            const apiKey = document.getElementById('apiKey').value.trim();
            
            // Create headers
            const headers = {
                'Content-Type': 'application/json'
            };
            
            // Add Authorization header if API key exists and is not the placeholder
            if (apiKey && apiKey !== '********') {
                headers['Authorization'] = `Bearer ${apiKey}`;
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
        
        // Обробка тексту для форматування блоків коду
        let formattedText = text;
        
        // Спочатку обробляємо блоки коду з потрійними зворотними апострофами
        formattedText = formattedText.replace(/```([a-zA-Z0-9_\-+#]*)\n?([\s\S]*?)```/gi, (match, lang, code) => {
            // Видаляємо зайві пробіли та переноси рядків
            const cleanCode = code.trim();
            
            // За замовчуванням використовуємо plaintext, якщо мова не вказана
            let langClass = 'language-plaintext';
            
            if (lang) {
                // Нормалізуємо назву мови та відображаємо на відповідний клас
                const normalizedLang = lang.toLowerCase().trim();
                
                // Карта ідентифікаторів мов для Prism.js
                const languageMap = {
                    // Apple platforms
                    'swift': 'language-swift',
                    'objc': 'language-objectivec',
                    'objectivec': 'language-objectivec',
                    'objective-c': 'language-objectivec',
                    'c': 'language-c',
                    'cpp': 'language-cpp',
                    'c++': 'language-cpp',
                    
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
                    'ps': 'language-powershell',
                };
                
                // Використовуємо відображений клас мови, якщо доступний, інакше використовуємо нормалізовану мову
                langClass = languageMap[normalizedLang] || `language-${normalizedLang}`;
            }
            
            return `<pre class="line-numbers ${langClass}"><code>${cleanCode}</code></pre>`;
        });
        
        // Додаткова обробка для випадків, коли код не обгорнутий в потрійні зворотні апострофи,
        // але містить однорядкові блоки коду з назвою мови (наприклад, "swift let counter = 0")
        const codePatterns = [
            // Шаблон для Swift
            { pattern: /\b(swift)\s+([^\n]+)/gi, lang: 'swift' },
            // Шаблон для Objective-C
            { pattern: /\b(objc|objective-c|objectivec)\s+([^\n]+)/gi, lang: 'objectivec' },
            // Шаблон для Java
            { pattern: /\b(java)\s+([^\n]+)/gi, lang: 'java' },
            // Шаблон для Kotlin
            { pattern: /\b(kotlin)\s+([^\n]+)/gi, lang: 'kotlin' },
            // Додайте інші мови за потреби
        ];
        
        // Застосовуємо шаблони для виявлення та форматування однорядкових блоків коду
        codePatterns.forEach(({ pattern, lang }) => {
            formattedText = formattedText.replace(pattern, (match, langName, code) => {
                const languageMap = {
                    'swift': 'language-swift',
                    'objc': 'language-objectivec',
                    'objective-c': 'language-objectivec',
                    'objectivec': 'language-objectivec',
                    'java': 'language-java',
                    'kotlin': 'language-kotlin'
                };
                
                const langClass = languageMap[langName.toLowerCase()] || `language-${langName.toLowerCase()}`;
                return `<pre class="line-numbers ${langClass}"><code>${code.trim()}</code></pre>`;
            });
        });
        
        return formattedText;
    }

    function formatResult(result) {
        if (!Array.isArray(result)) {
            console.error('Result is not an array:', result);
            return '<div class="alert alert-danger">Invalid result format</div>';
        }

        // If there's only one question, display it normally
        if (result.length === 1) {
            return formatSingleQuestion(result[0]);
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

        return tabsHtml + tabContentHtml;
    }

    function formatSingleQuestion(question) {
        if (!question || !question.answerLevels) {
            console.error('Invalid question format:', question);
            return '';
        }
        
        // Format validation info if available
        let validationHtml = '';
        if (question.validation) {
            // Create a unique ID for this validation collapse section
            const validationId = `validation-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
            
            // Check if validation was skipped (quality_score = 0)
            if (question.validation.quality_score === 0) {
                validationHtml = `
                    <div class="validation-container">
                        <button class="btn btn-sm btn-outline-secondary validation-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#${validationId}" aria-expanded="false">
                            <i class="bi bi-info-circle"></i> Validation Skipped
                        </button>
                        <div class="collapse validation-content" id="${validationId}">
                            <div class="card card-body validation-card validation-skipped">
                                <div class="validation-comments">${question.validation.validation_comments || 'Validation was not performed.'}</div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                const validationClass = question.validation.passed ? 'validation-passed' : 'validation-failed';
                const score = question.validation.quality_score || 0;
                const statusIcon = question.validation.passed ? 'check-circle' : 'exclamation-triangle';
                const statusText = question.validation.passed ? 'Validation Passed' : 'Validation Failed';
                
                validationHtml = `
                    <div class="validation-container">
                        <button class="btn btn-sm btn-outline-secondary validation-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#${validationId}" aria-expanded="false">
                            <i class="bi bi-${statusIcon}"></i> ${statusText} - Quality Score: ${score}/10
                        </button>
                        <div class="collapse validation-content" id="${validationId}">
                            <div class="card card-body validation-card ${validationClass}">
                                <div class="validation-comments">${question.validation.validation_comments || 'No validation comments'}</div>
                            </div>
                        </div>
                    </div>
                `;
            }
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
        return `
            <div class="question-block">
                <div class="question-title">${formatCode(question.text) || 'No question text'}</div>
                <div class="question-tags">
                    ${(question.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                ${validationHtml}
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
                                                <p>${question.answerLevels.beginer.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${formatCode(question.answerLevels.beginer?.answer)}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.beginer?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${formatCode(test.snippet)}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${test.answer || 'Not specified'}</strong>
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
                                                <p>${question.answerLevels.intermediate.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${formatCode(question.answerLevels.intermediate?.answer)}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.intermediate?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${formatCode(test.snippet)}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${test.answer || 'Not specified'}</strong>
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
                                                <p>${question.answerLevels.advanced.evaluation_criteria}</p>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="question-description">${formatCode(question.answerLevels.advanced?.answer)}</div>
                                <ul class="mt-3">
                                    ${(question.answerLevels.advanced?.tests || []).map(test => `
                                        <li class="test-block">
                                            <div class="code-snippet">${formatCode(test.snippet)}</div>
                                            <div class="test-options">
                                                <ul>
                                                    ${(test.options || []).map(option => `
                                                        <li>${option}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                            <div class="correct-answer">
                                                Correct Answer: <strong>${test.answer || 'Not specified'}</strong>
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
    }
}); 
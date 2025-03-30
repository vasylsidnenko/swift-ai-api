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
            number: parseInt(document.getElementById('number').value, 10)
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

            // Отримуємо API ключ
            const apiKey = document.getElementById('apiKey').value.trim();
            
            // Формуємо заголовки
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
                resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.error}</div>`;
            } else {
                const formattedResult = formatResult(result);
                resultDiv.innerHTML = formattedResult;
                // Підсвічуємо синтаксис після додавання контенту
                Prism.highlightAll();
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    });

    function formatCode(text) {
        if (!text) return '';
        
        // Знаходимо блоки коду в форматі ```swift ... ```
        return text.replace(/```(?:swift)?\n?([\s\S]*?)```/g, (match, code) => {
            // Видаляємо зайві пробіли та переноси рядків
            const cleanCode = code.trim();
            return `<pre class="line-numbers language-swift"><code>${cleanCode}</code></pre>`;
        });
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

        return `
            <div class="question-block">
                <div class="question-title">${question.text || 'No question text'}</div>
                <div class="question-tags">
                    ${(question.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                
                <div class="answer-level beginner">
                    <h5 class="question-title">${question.answerLevels.beginer?.name || 'Beginner Level'}</h5>
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
                
                <div class="answer-level intermediate">
                    <h5 class="question-title">${question.answerLevels.intermediate?.name || 'Intermediate Level'}</h5>
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
                
                <div class="answer-level advanced">
                    <h5 class="question-title">${question.answerLevels.advanced?.name || 'Advanced Level'}</h5>
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
        `;
    }
}); 
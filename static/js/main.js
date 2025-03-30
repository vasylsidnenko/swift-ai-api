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
            const response = await fetch(`/api/models/${provider}`);
            const data = await response.json();
            
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

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            topic: document.getElementById('topic').value,
            platform: document.getElementById('platform').value,
            tech: document.getElementById('tech').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            ai: document.getElementById('ai').value,
            model: document.getElementById('model').value
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
            
            // Add Authorization header if API key exists
            if (apiKey) {
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

        return result.map(question => {
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
        }).join('');
    }
}); 
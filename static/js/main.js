document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultDiv = document.getElementById('result');
    const aiSelect = document.getElementById('ai');
    const modelSelect = document.getElementById('model');

    // Update available models based on selected AI
    aiSelect.addEventListener('change', function() {
        const ai = this.value;
        const models = {
            'googleai': ['gemini-pro'],
            'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
            'deepseekai': ['deepseek-chat']
        };

        modelSelect.innerHTML = '';
        models[ai].forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
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
            // Показуємо індикатор завантаження
            resultDiv.innerHTML = `
                <div class="loading-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="loading-text mt-3">Generating questions...</div>
                </div>
            `;

            const response = await fetch('/generate_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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
                <div class="question mb-4">
                    <h4>${question.text || 'No question text'}</h4>
                    <p>Tags: ${(question.tags || []).join(', ')}</p>
                    <div class="answer-level beginner">
                        <h5>Beginner</h5>
                        <div class="answer-content">${formatCode(question.answerLevels.beginer?.answer)}</div>
                        <ul class="mt-3">
                            ${(question.answerLevels.beginer?.tests || []).map(test => `
                                <li class="mb-3">
                                    <div class="code-snippet">${formatCode(test.snippet)}</div>
                                    <ul class="mt-2">
                                        ${(test.options || []).map(option => `
                                            <li>${option}</li>
                                        `).join('')}
                                    </ul>
                                    <p class="mt-2">Correct Answer: <strong>${test.answer || 'Not specified'}</strong></p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div class="answer-level intermediate">
                        <h5>Intermediate</h5>
                        <div class="answer-content">${formatCode(question.answerLevels.intermediate?.answer)}</div>
                        <ul class="mt-3">
                            ${(question.answerLevels.intermediate?.tests || []).map(test => `
                                <li class="mb-3">
                                    <div class="code-snippet">${formatCode(test.snippet)}</div>
                                    <ul class="mt-2">
                                        ${(test.options || []).map(option => `
                                            <li>${option}</li>
                                        `).join('')}
                                    </ul>
                                    <p class="mt-2">Correct Answer: <strong>${test.answer || 'Not specified'}</strong></p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div class="answer-level advanced">
                        <h5>Advanced</h5>
                        <div class="answer-content">${formatCode(question.answerLevels.advanced?.answer)}</div>
                        <ul class="mt-3">
                            ${(question.answerLevels.advanced?.tests || []).map(test => `
                                <li class="mb-3">
                                    <div class="code-snippet">${formatCode(test.snippet)}</div>
                                    <ul class="mt-2">
                                        ${(test.options || []).map(option => `
                                            <li>${option}</li>
                                        `).join('')}
                                    </ul>
                                    <p class="mt-2">Correct Answer: <strong>${test.answer || 'Not specified'}</strong></p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }).join('');
    }
}); 
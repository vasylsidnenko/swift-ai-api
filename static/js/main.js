document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const resultContent = document.getElementById('resultContent');
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
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            ai: document.getElementById('ai').value,
            model: document.getElementById('model').value
        };

        try {
            resultContent.textContent = 'Generating question...';
            const response = await fetch('/generate_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.error) {
                resultContent.textContent = `Error: ${result.error}`;
            } else {
                resultContent.textContent = JSON.stringify(result, null, 2);
            }
        } catch (error) {
            resultContent.textContent = `Error: ${error.message}`;
        }
    });
}); 
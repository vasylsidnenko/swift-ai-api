// Функція для форматування тексту питання
// Текст питання відображається як звичайний текст, а блоки коду форматуються
document.addEventListener('DOMContentLoaded', function() {
    // Додаємо функцію formatQuestionText до глобального об'єкту window
    window.formatQuestionText = function(text) {
        if (!text) return '';
        
        // Regular expression for finding code blocks - only if they are defined with triple backticks on both sides
        // Important: we use non-greedy search to find only complete code blocks
        const codeBlockRegex = /```([a-zA-Z0-9_\-+#]*)\n?([\s\S]*?)```/g;
        
        // Debug log for code blocks
        console.log('Formatting question text with code blocks');
        
        // Check if text contains code blocks
        const hasCodeBlocks = text.includes('```');
        if (hasCodeBlocks) {
            console.log('Found code blocks in text');
        }
        
        // Масив для зберігання блоків коду
        const codeBlocks = [];
        
        // Замінюємо блоки коду на плейсхолдери
        let processedText = text.replace(codeBlockRegex, function(match, lang, code) {
            // Save the code block and log its language
            const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
            console.log(`Found code block with language: '${lang || 'not specified'}', length: ${code.length} chars`);
            codeBlocks.push({ lang, code: code.trim() });
            return placeholder;
        });
        
        // Замінюємо плейсхолдери на форматований код
        for (let i = 0; i < codeBlocks.length; i++) {
            const placeholder = `__CODE_BLOCK_${i}__`;
            const { lang, code } = codeBlocks[i];
            
            // Визначаємо клас мови для Prism.js
            let langClass = 'language-plaintext';
            if (lang) {
                // Нормалізуємо назву мови
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
                    'metal': 'language-cpp', // Metal використовує синтаксис C++
                    'opengl': 'language-glsl', // OpenGL використовує GLSL
                    
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
            
            // Preserve line breaks in code block by replacing them with HTML line breaks
            // This ensures the code displays properly with line breaks
            console.log(`Formatting code block with language class: ${langClass}`);
            
            // Ensure code is properly escaped for HTML
            const escapedCode = code
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
                
            // Create HTML for code block with proper language class
            // We use pre and code tags to ensure proper formatting
            const formattedCode = `<pre class="line-numbers ${langClass}"><code>${escapedCode}</code></pre>`;
            
            // Замінюємо плейсхолдер на форматований код
            processedText = processedText.replace(placeholder, formattedCode);
        }
        
        // Replace newlines with <br>, but only for regular text
        // Code blocks are already processed and have proper line breaks
        processedText = processedText.replace(/(<pre[\s\S]*?<\/pre>)|\n/g, (match, p1) => p1 ? p1 : '<br>');
        
        // Log the final processed text length
        console.log(`Processed text length: ${processedText.length} chars, with ${codeBlocks.length} code blocks`);
        
        return processedText;
    };
});

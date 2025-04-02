// Скрипт для ініціалізації Prism.js після завантаження контенту
document.addEventListener('DOMContentLoaded', function() {
    // Функція для ініціалізації Prism.js
    function initPrism() {
        if (window.Prism) {
            console.log('Initializing Prism.js for syntax highlighting');
            try {
                // Спочатку знаходимо всі блоки коду і перевіряємо, чи мають вони правильні класи мов
                const codeBlocks = document.querySelectorAll('pre code');
                codeBlocks.forEach(function(codeBlock) {
                    const parentPre = codeBlock.parentElement;
                    if (parentPre && parentPre.className) {
                        // Перевіряємо, чи має блок коду клас мови
                        const hasLanguageClass = Array.from(parentPre.classList).some(cls => cls.startsWith('language-'));
                        if (!hasLanguageClass) {
                            // Якщо немає класу мови, додаємо за замовчуванням language-plaintext
                            parentPre.classList.add('language-plaintext');
                        }
                        
                        // Перевіряємо, чи має блок коду клас line-numbers
                        if (!parentPre.classList.contains('line-numbers')) {
                            parentPre.classList.add('line-numbers');
                        }
                    }
                });
                
                // Тепер ініціалізуємо Prism.js
                Prism.highlightAll();
                console.log('Prism.js initialization completed');
            } catch (error) {
                console.error('Error initializing Prism.js:', error);
            }
        } else {
            console.warn('Prism.js not available');
        }
    }
    
    // Викликаємо функцію при завантаженні сторінки
    initPrism();
    
    // Також викликаємо функцію при зміні DOM (коли додаються нові елементи)
    // Використовуємо MutationObserver для спостереження за змінами в DOM
    const observer = new MutationObserver(function(mutations) {
        let shouldInit = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                // Перевіряємо, чи додані вузли містять елементи з класом pre або code
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Елемент
                        if (node.classList && (node.classList.contains('line-numbers') || 
                                              node.tagName === 'PRE' || 
                                              node.tagName === 'CODE')) {
                            shouldInit = true;
                        } else if (node.querySelector) {
                            // Перевіряємо, чи містить вузол елементи pre або code
                            const hasPre = node.querySelector('pre');
                            const hasCode = node.querySelector('code');
                            if (hasPre || hasCode) {
                                shouldInit = true;
                            }
                        }
                    }
                });
            }
        });
        
        // Ініціалізуємо Prism.js, якщо були додані елементи з кодом
        if (shouldInit) {
            console.log('New code elements detected, initializing Prism.js');
            
            // Затримка для того, щоб DOM повністю оновився
            setTimeout(function() {
                initPrism();
            }, 100);
        }
    });
    
    // Спостерігаємо за змінами в результаті
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        observer.observe(resultDiv, { childList: true, subtree: true });
    }
    
    // Повторна ініціалізація Prism.js через 1 секунду після завантаження сторінки
    setTimeout(function() {
        initPrism();
    }, 1000);
    
    // Повторна ініціалізація Prism.js через 3 секунди після завантаження сторінки
    setTimeout(function() {
        initPrism();
    }, 3000);
});

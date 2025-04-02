// Скрипт для відображення інформації про Quality Score
document.addEventListener('DOMContentLoaded', function() {
    // Функція для додавання пояснення про Quality Score
    function addQualityScoreExplanation() {
        // Знаходимо всі елементи з текстом "Quality Score: X/10"
        const validationButtons = document.querySelectorAll('.validation-toggle');
        
        validationButtons.forEach(function(button) {
            const buttonText = button.textContent || '';
            const scoreMatch = buttonText.match(/Quality Score: (\d+)\/10/);
            
            if (scoreMatch && scoreMatch[1]) {
                const score = parseInt(scoreMatch[1], 10);
                
                // Якщо оцінка менше 10, додаємо пояснення
                if (score < 10) {
                    // Знаходимо відповідний блок валідації
                    const targetId = button.getAttribute('data-bs-target');
                    if (targetId) {
                        const validationBlock = document.querySelector(targetId);
                        if (validationBlock) {
                            // Знаходимо список валідацій
                            const validationList = validationBlock.querySelector('.validation-list');
                            
                            if (validationList) {
                                // Перевіряємо, чи є вже елементи з класом failed
                                const failedItems = validationList.querySelectorAll('li.failed');
                                
                                // Якщо немає явних помилок, але оцінка менше 10, додаємо пояснення
                                if (failedItems.length === 0) {
                                    // Створюємо новий елемент списку з поясненням
                                    const explanationItem = document.createElement('li');
                                    explanationItem.className = 'quality-score-explanation';
                                    explanationItem.style.color = '#856404';
                                    explanationItem.style.backgroundColor = '#fff3cd';
                                    explanationItem.style.padding = '8px';
                                    explanationItem.style.borderRadius = '4px';
                                    explanationItem.style.marginTop = '10px';
                                    
                                    // Explanation text depends on the score
                                    let explanationText = '';
                                    if (score >= 9) {
                                        explanationText = `Quality Score ${score}/10: The question is almost perfect, but there are minor areas for improvement. Check validation comments for details.`;
                                    } else if (score >= 7) {
                                        explanationText = `Quality Score ${score}/10: The question is good, but there are several areas that could be improved. Check validation comments for details.`;
                                    } else if (score >= 5) {
                                        explanationText = `Quality Score ${score}/10: The question is satisfactory but needs refinement. Check validation comments for details.`;
                                    } else {
                                        explanationText = `Quality Score ${score}/10: The question needs significant improvement. Check validation comments for details.`;
                                    }
                                    
                                    explanationItem.textContent = explanationText;
                                    validationList.appendChild(explanationItem);
                                }
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Викликаємо функцію при завантаженні сторінки
    addQualityScoreExplanation();
    
    // Також викликаємо функцію при зміні DOM (коли додаються нові елементи)
    // Використовуємо MutationObserver для спостереження за змінами в DOM
    const observer = new MutationObserver(function(mutations) {
        let shouldAdd = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                // Перевіряємо, чи додані вузли містять елементи з класом validation-toggle
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Елемент
                        if (node.classList && node.classList.contains('validation-toggle')) {
                            shouldAdd = true;
                        } else if (node.querySelector) {
                            // Перевіряємо, чи містить вузол елементи з класом validation-toggle
                            const hasValidationToggle = node.querySelector('.validation-toggle');
                            if (hasValidationToggle) {
                                shouldAdd = true;
                            }
                        }
                    }
                });
            }
        });
        
        // Додаємо пояснення про Quality Score, якщо були додані нові елементи валідації
        if (shouldAdd) {
            console.log('New validation elements detected, adding Quality Score explanation');
            
            // Затримка для того, щоб DOM повністю оновився
            setTimeout(function() {
                addQualityScoreExplanation();
            }, 100);
        }
    });
    
    // Спостерігаємо за змінами в результаті
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        observer.observe(resultDiv, { childList: true, subtree: true });
    }
});

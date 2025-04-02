// Скрипт для приховування рядка "All validation checks passed!"
document.addEventListener('DOMContentLoaded', function() {
    // Функція для приховування рядка "All validation checks passed!"
    function hidePassedValidation() {
        // Знаходимо всі елементи з текстом "All validation checks passed!"
        const passedItems = document.querySelectorAll('li.passed');
        
        // Приховуємо їх
        passedItems.forEach(function(item) {
            if (item.textContent.includes('All validation checks passed')) {
                item.style.display = 'none';
            }
        });
    }
    
    // Викликаємо функцію при завантаженні сторінки
    hidePassedValidation();
    
    // Також викликаємо функцію при зміні DOM (коли додаються нові елементи)
    // Використовуємо MutationObserver для спостереження за змінами в DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                hidePassedValidation();
            }
        });
    });
    
    // Спостерігаємо за змінами в результаті
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        observer.observe(resultDiv, { childList: true, subtree: true });
    }
});

// Injects provider/model info into the AI Configuration header and applies provider color
function setProviderModelInHeader(provider, model) {
    // Set values in <b id=aiConfigProvider> and <b id=aiConfigModel>
    var prov = provider || (window.aiSelect && window.aiSelect.options.length ? window.aiSelect.options[0].value : '—');
    var mod = model || (window.modelSelect && window.modelSelect.options.length ? window.modelSelect.options[0].value : '—');
    if (!prov || prov === '-') prov = '—';
    if (!mod || mod === '-') mod = '—';
    var provEl = document.getElementById('aiConfigProvider');
    var modEl = document.getElementById('aiConfigModel');
    if (provEl) provEl.textContent = prov;
    if (modEl) modEl.textContent = mod;
}

function updateAIConfigHeader(provider, model) {
    var header = document.getElementById('aiConfigHeader');
    if (!header) return;
    var color = getProviderColor(provider);
    setProviderModelInHeader(provider, model);
    header.style.setProperty('background-color', '#6c757d', 'important');
    header.style.color = '#fff';
}

// Collapse chevron logic
window.addEventListener('DOMContentLoaded', function() {
    var chevron = document.getElementById('aiConfigChevron');
    var aiSettings = document.getElementById('aiSettings');
    if (!chevron || !aiSettings) return;
    aiSettings.addEventListener('show.bs.collapse', function () {
        chevron.classList.remove('bi-chevron-down');
        chevron.classList.add('bi-chevron-up');
    });
    aiSettings.addEventListener('hide.bs.collapse', function () {
        chevron.classList.remove('bi-chevron-up');
        chevron.classList.add('bi-chevron-down');
    });
});

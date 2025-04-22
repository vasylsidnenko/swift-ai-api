// Injects provider/model info into the AI Configuration header and applies provider color
function updateAIConfigHeader(provider, model) {
    var header = document.getElementById('aiConfigHeader');
    if (!header) return;
    var color = getProviderColor(provider);
    header.innerHTML = `<span>AI Configuration</span><span class='ms-2 small'>Provider: <b>${escapeHtml(provider)}</b> | Model: <b>${escapeHtml(model)}</b></span>`;
    header.style.setProperty('background-color', color, 'important');
    header.style.color = '#fff';
}

// Injects provider/model info into the AI Configuration header and applies provider color
function setProviderModelInHeader() {
    // Always use current DOM values for provider and model
    var provEl = document.getElementById('aiConfigProvider');
    var modEl = document.getElementById('aiConfigModel');
    var aiSelect = document.getElementById('ai');
    var modelSelect = document.getElementById('model');
    var prov = aiSelect && aiSelect.value ? aiSelect.value : '—';
    var mod = modelSelect && modelSelect.value ? modelSelect.value : '—';
    if (provEl) provEl.textContent = prov;
    if (modEl) {
        modEl.textContent = mod;
        if (prov !== '—' && mod !== '—') {
            // Save current model for closure
            const currentModel = mod;
            fetch(`/api/model-description/${prov}/${mod}`)
                .then(resp => resp.json())
                .then(data => {
                    // Only update if model is still current
                    if (modelSelect && modelSelect.value === currentModel) {
                        modEl.title = data && data.description ? data.description.trim() : 'No description available.';
                    }
                })
                .catch(() => {
                    if (modelSelect && modelSelect.value === currentModel) {
                        modEl.title = 'No description available.';
                    }
                });
        } else {
            modEl.title = '';
        }
    }
}

function updateAIConfigHeader() {
    var header = document.getElementById('aiConfigHeader');
    if (!header) return;
    setProviderModelInHeader();
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

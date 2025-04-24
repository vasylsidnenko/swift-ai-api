/* Prism.js loader for syntax highlighting */
// This will load the Prism.js library and enable highlighting for code blocks
// See https://prismjs.com/
(function() {
    if (window.Prism) return;
    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js';
    script.onload = function() {
        // Optionally load languages
        var langScript = document.createElement('script');
        langScript.src = 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-swift.min.js';
        document.head.appendChild(langScript);
    };
    document.head.appendChild(script);
    // Also load the Prism CSS
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css';
    document.head.appendChild(link);
})();
// Highlight all code blocks after DOM update
document.addEventListener('DOMContentLoaded', function() {
    if (window.Prism && Prism.highlightAll) {
        Prism.highlightAll();
    }
});
function highlightAllCodeBlocks() {
    if (window.Prism && Prism.highlightAll) {
        Prism.highlightAll();
    }
}

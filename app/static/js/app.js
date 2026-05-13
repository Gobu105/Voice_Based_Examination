const isCandidatePage = document.body.classList.contains('exam-body') || window.location.pathname.startsWith('/candidate');

if (isCandidatePage) {
    import('./voice/main.js').catch((error) => {
        console.error('Failed to load voice exam module:', error);
    });
}

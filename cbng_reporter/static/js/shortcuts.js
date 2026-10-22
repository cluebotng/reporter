// Submit the matching status form when a shortcut key is pressed
document.addEventListener('keydown', function (event) {
    if (event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input, textarea, select')) {
        // Ignore modified keys & typing in the comment box
        return;
    }

    for (const form of document.querySelectorAll('form[data-shortcut-keys]')) {
        const keys = form.dataset.shortcutKeys.split(' ');
        if (keys.includes(event.key) || keys.includes(event.code)) {
            event.preventDefault();
            form.submit();
            return;
        }
    }
});

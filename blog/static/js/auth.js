document.body.addEventListener('htmx:configRequest', function(evt) {
    // Add header to indicate we want the full page response
    evt.detail.headers['X-Full-Page'] = 'true';
});

document.body.addEventListener('htmx:beforeSwap', function(evt) {
    // Handle both redirect responses and regular responses
    const redirectUrl = evt.detail.xhr.getResponseHeader('HX-Redirect') || 
                       evt.detail.xhr.getResponseHeader('Location');
    if (redirectUrl) {
        evt.detail.shouldSwap = false;
        window.location.href = redirectUrl;
    }
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.tagName === 'BODY') {
        // Re-initialize any necessary scripts
        initializeSidebar();
        
        // Update the page title if provided
        const titleTag = evt.detail.target.querySelector('title');
        if (titleTag) {
            document.title = titleTag.textContent;
        }
    }
});

document.body.addEventListener('htmx:afterSettle', function(evt) {
    if (evt.detail.target.tagName === 'BODY') {
        const sidebar = document.querySelector('#sidebarMenu');
        if (!sidebar) {
            window.location.reload();
            return;
        }
        initializeSidebar();
    }
});

document.body.addEventListener('htmx:beforeRequest', function(evt) {
    if (evt.detail.requestConfig.path === '/accounts/logout/') {
        evt.detail.headers['X-CSRFToken'] = document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}); 
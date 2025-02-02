document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
});

// Initialize sidebar functionality
function initializeSidebar() {
    const toggleButton = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('#sidebarMenu');
    const mainContent = document.querySelector('main');
    
    if (!toggleButton || !sidebar || !mainContent) {
        console.error('Required elements not found');
        return;
    }

    // Restore sidebar state
    const sidebarState = localStorage.getItem('sidebarState');
    if (sidebarState === 'collapsed') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }

    toggleButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const isCollapsed = sidebar.classList.contains('collapsed');
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebarState', isCollapsed ? 'expanded' : 'collapsed');
    });
    
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateInitialState, 250);
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const isMobile = window.innerWidth < 768;
        const isClickOutside = !sidebar.contains(event.target) && !toggleButton.contains(event.target);
        
        if (isMobile && isClickOutside && !sidebar.classList.contains('collapsed')) {
            const isCollapsed = sidebar.classList.contains('collapsed');
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebarState', isCollapsed ? 'expanded' : 'collapsed');
        }
    });
}

// Handle HTMX events
document.body.addEventListener('htmx:afterSettle', function(evt) {
    const sidebar = document.querySelector('#sidebarMenu');
    if (sidebar) {
        const sidebarState = localStorage.getItem('sidebarState');
        if (sidebarState === 'collapsed') {
            sidebar.classList.add('collapsed');
            document.querySelector('main').classList.add('sidebar-collapsed');
        }
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('#sidebarMenu');
    const mainContent = document.querySelector('main');
    
    if (!toggleButton || !sidebar || !mainContent) {
        console.error('Required elements not found');
        return;
    }

    // Initialize state based on screen size
    function updateInitialState() {
        const isMobile = window.innerWidth < 768;
        if (isMobile) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
            document.body.classList.add('sidebar-collapsed');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
            document.body.classList.remove('sidebar-collapsed');
        }
    }

    // Call on load
    updateInitialState();

    // Toggle sidebar function
    function toggleSidebar() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');
        document.body.classList.toggle('sidebar-collapsed');
        
        toggleButton.setAttribute('aria-expanded', isCollapsed);
    }

    // Add click event listener
    toggleButton.addEventListener('click', toggleSidebar);
    
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
            toggleSidebar();
        }
    });
});
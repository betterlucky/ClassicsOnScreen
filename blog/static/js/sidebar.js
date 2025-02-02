document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
});

function initializeSidebar() {
    const toggleButton = document.querySelector('.sidebar-toggle');
    const sidebarContainer = document.querySelector('.sidebar-container');
    const sidebar = document.querySelector('#sidebarMenu');
    const isMobile = () => window.innerWidth < 768;
    
    if (!toggleButton || !sidebar) {
        console.error('Required elements not found');
        return;
    }

    // Set initial state based on screen size
    function setInitialState() {
        if (isMobile()) {
            sidebar.classList.remove('desktop-collapsed');
            sidebarContainer.classList.add('collapsed');
        } else {
            sidebarContainer.classList.remove('collapsed');
            sidebar.classList.add('desktop-collapsed');
        }
    }

    // Set initial state immediately
    setInitialState();

    // Mobile behavior
    toggleButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        sidebarContainer.classList.toggle('collapsed');
    });

    // Desktop behavior
    if (!isMobile()) {
        sidebar.addEventListener('mouseenter', () => {
            sidebar.classList.remove('desktop-collapsed');
        });
        sidebar.addEventListener('mouseleave', () => {
            sidebar.classList.add('desktop-collapsed');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (isMobile() && 
            !sidebar.contains(event.target) && 
            !toggleButton.contains(event.target)) {
            sidebarContainer.classList.add('collapsed');
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            setInitialState();
        }, 250);
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
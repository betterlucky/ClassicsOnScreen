document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
});

function initializeSidebar() {
    const toggleButton = document.querySelector('.sidebar-toggle');
    const toggleIcon = toggleButton.querySelector('i');
    const sidebar = document.querySelector('#sidebarMenu');
    const mainContent = document.querySelector('main');
    const isMobile = () => window.innerWidth < 768;
    
    if (!toggleButton || !sidebar || !mainContent) {
        console.error('Required elements not found');
        return;
    }

    function collapseSidebar() {
        if (isMobile()) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
            toggleIcon.classList.remove('bi-chevron-left');
            toggleIcon.classList.add('bi-chevron-right');
        } else {
            sidebar.classList.add('desktop-collapsed');
            mainContent.classList.add('sidebar-collapsed');
        }
    }

    function expandSidebar() {
        if (isMobile()) {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
            toggleIcon.classList.remove('bi-chevron-right');
            toggleIcon.classList.add('bi-chevron-left');
        } else {
            sidebar.classList.remove('desktop-collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        }
    }

    // Initial state - always start collapsed
    if (isMobile()) {
        sidebar.classList.add('collapsed');
    } else {
        sidebar.classList.add('desktop-collapsed');
    }
    mainContent.classList.add('sidebar-collapsed');

    // Desktop behavior
    if (!isMobile()) {
        sidebar.addEventListener('mouseenter', expandSidebar);
        sidebar.addEventListener('mouseleave', collapseSidebar);
    }

    // Mobile behavior
    if (isMobile()) {
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (sidebar.classList.contains('collapsed')) {
                expandSidebar();
            } else {
                collapseSidebar();
            }
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
                collapseSidebar();
            }
        });
    }

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const wasMobile = sidebar.hasAttribute('data-mobile');
            const isMobileNow = window.innerWidth < 768;
            
            if (wasMobile !== isMobileNow) {
                // Remove all event listeners by cloning
                const newSidebar = sidebar.cloneNode(true);
                sidebar.parentNode.replaceChild(newSidebar, sidebar);
                sidebar = newSidebar;
                
                // Reinitialize with new state
                if (isMobileNow) {
                    sidebar.setAttribute('data-mobile', 'true');
                    sidebar.classList.add('collapsed');
                } else {
                    sidebar.removeAttribute('data-mobile');
                    sidebar.classList.add('desktop-collapsed');
                }
                mainContent.classList.add('sidebar-collapsed');
                initializeSidebar();
            }
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
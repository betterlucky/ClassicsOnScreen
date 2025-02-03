document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('#sidebarMenu');
    const toggleButton = document.querySelector('.sidebar-toggle');
    const main = document.querySelector('main');
    const isMobile = () => window.innerWidth < 768;
    
    if (!sidebar || !toggleButton) return;

    function toggleSidebar(show) {
        if (show) {
            sidebar.style.transform = 'translateX(0)';
            main.classList.add('ml-64');
            main.classList.remove('md:ml-5');
        } else {
            if (isMobile()) {
                sidebar.style.transform = 'translateX(-100%)';
            } else {
                sidebar.style.transform = 'translateX(calc(-100% + 20px))';
            }
            main.classList.remove('ml-64');
            main.classList.add('md:ml-5');
        }
    }

    // Mobile toggle
    toggleButton.addEventListener('click', () => {
        const isOpen = sidebar.style.transform === 'translateX(0px)';
        toggleSidebar(!isOpen);
    });

    // Desktop hover
    if (!isMobile()) {
        sidebar.addEventListener('mouseenter', () => toggleSidebar(true));
        sidebar.addEventListener('mouseleave', () => toggleSidebar(false));
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (event) => {
        if (isMobile() && 
            !sidebar.contains(event.target) && 
            !toggleButton.contains(event.target)) {
            toggleSidebar(false);
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (isMobile()) {
                toggleSidebar(false);
            }
        }, 250);
    });
});
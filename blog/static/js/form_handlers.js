document.addEventListener('DOMContentLoaded', function() {
    // Auto-submit form on select change
    document.querySelectorAll('#filters-form select').forEach(function(select) {
        select.addEventListener('change', function() {
            document.getElementById('filters-form').submit();
        });
    });

    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
}); 
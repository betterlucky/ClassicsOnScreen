const toggleButton = document.querySelector('.sidebar-toggle');
const sidebar = document.querySelector('.sidebar');
const body = document.body;

toggleButton.addEventListener('click', () => {
    sidebar.classList.toggle('show');
    body.classList.toggle('sidebar-open'); // Toggle the class on the body
    toggleButton.setAttribute('aria-expanded', sidebar.classList.contains('show')); // Update aria-expanded
});
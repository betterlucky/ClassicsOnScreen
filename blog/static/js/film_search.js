document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('filmSearch');
    const filmsContainer = document.getElementById('filmsContainer');
    if (!searchInput || !filmsContainer) return;

    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase().trim();
        const films = document.getElementsByClassName('film-item');
        let hasVisibleFilms = false;

        Array.from(films).forEach(film => {
            const filmName = film.getAttribute('data-film-name');
            if (filmName && filmName.includes(searchTerm)) {
                film.style.display = '';
                hasVisibleFilms = true;
            } else {
                film.style.display = 'none';
            }
        });

        // Show/hide no results message
        const existingMessage = document.querySelector('.no-results-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        if (!hasVisibleFilms && searchTerm !== '') {
            const message = document.createElement('div');
            message.className = 'col-12 no-results-message';
            message.innerHTML = '<div class="alert alert-info"><i class="bi bi-info-circle me-2"></i>No films match your search.</div>';
            filmsContainer.appendChild(message);
        }
    });
}); 
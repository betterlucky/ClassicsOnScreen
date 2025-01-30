document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('filmSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const films = document.getElementsByClassName('film-item');
        let hasVisibleFilms = false;

        Array.from(films).forEach(film => {
            const filmName = film.dataset.filmName;
            if (filmName.includes(searchTerm)) {
                film.style.display = '';
                hasVisibleFilms = true;
            } else {
                film.style.display = 'none';
            }
        });

        // Show/hide no results message
        const noResults = document.querySelector('.no-results');
        if (noResults) {
            if (!hasVisibleFilms) {
                if (!document.querySelector('.no-results-message')) {
                    const message = document.createElement('div');
                    message.className = 'col-12 no-results-message';
                    message.innerHTML = '<div class="alert alert-info">No films match your search.</div>';
                    document.getElementById('filmsContainer').appendChild(message);
                }
            } else {
                const message = document.querySelector('.no-results-message');
                if (message) message.remove();
            }
        }
    });
}); 
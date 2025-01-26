django.jQuery(function($) {
    function initIMDBSearch() {
        var $imdbField = $('#id_imdb_code');
        var $nameField = $('#id_name');
        
        // Create a container for the search
        var $searchContainer = $('<div class="imdb-search-container" style="margin-bottom: 10px;"></div>');
        var $searchField = $('<select class="imdb-search" style="width: 100%;"></select>');
        
        $searchContainer.insertBefore($imdbField.parent());
        $searchContainer.append($searchField);

        $searchField.select2({
            placeholder: 'Search for a movie on IMDB...',
            allowClear: true,
            minimumInputLength: 3,
            ajax: {
                url: '../imdb-search/',
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        term: params.term
                    };
                },
                processResults: function(data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
        });

        // When a movie is selected, update the fields
        $searchField.on('select2:select', function(e) {
            var data = e.params.data;
            $imdbField.val(data.id);
            if (!$nameField.val()) {
                $nameField.val(data.title);
            }
        });
    }

    // Initialize on document ready and on popup load
    initIMDBSearch();
    $(document).on('formset:added', initIMDBSearch);
}); 
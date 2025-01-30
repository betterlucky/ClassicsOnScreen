document.addEventListener('DOMContentLoaded', function() {
    window.clearFilter = function(filterName) {
        document.querySelector(`select[name="${filterName}"]`).value = '';
        document.getElementById('filters-form').submit();
    }

    window.resetFilters = function() {
        document.querySelectorAll('.filter-select').forEach(select => {
            select.value = '';
        });
        document.getElementById('filters-form').submit();
    }

    // Auto-submit on select change
    document.querySelectorAll('.filter-select').forEach(function(select) {
        select.addEventListener('change', function() {
            document.getElementById('filters-form').submit();
        });
    });
}); 
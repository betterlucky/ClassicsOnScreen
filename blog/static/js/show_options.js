document.addEventListener('DOMContentLoaded', function() {
    const optionsSelect = document.getElementById('id_available_options');
    const selectedOptionsDiv = document.getElementById('selected-options');
    const selectedOptionsField = document.getElementById('id_selected_options');
    let selectedOptions = new Set();

    if (!optionsSelect || !selectedOptionsDiv || !selectedOptionsField) {
        return;
    }

    optionsSelect.addEventListener('change', function() {
        const option = optionsSelect.options[optionsSelect.selectedIndex];
        if (option.value && !selectedOptions.has(option.value)) {
            selectedOptions.add(option.value);
            updateSelectedOptionsDisplay();
            updateSelectedOptionsField();
        }
        optionsSelect.selectedIndex = 0;
    });

    function removeOption(optionId) {
        selectedOptions.delete(optionId);
        updateSelectedOptionsDisplay();
        updateSelectedOptionsField();
    }

    function updateSelectedOptionsDisplay() {
        selectedOptionsDiv.innerHTML = Array.from(selectedOptions).map(optionId => {
            const optionText = Array.from(optionsSelect.options).find(opt => opt.value === optionId)?.text;
            return `
                <span class="badge bg-primary me-2 mb-2">
                    ${optionText}
                    <button type="button" class="btn-close btn-close-white" 
                            aria-label="Remove" 
                            onclick="removeOption('${optionId}')">
                    </button>
                </span>
            `;
        }).join('');
    }

    function updateSelectedOptionsField() {
        const options = selectedOptionsField.options;
        options.length = 0;
        selectedOptions.forEach(value => {
            const option = new Option(value, value);
            option.selected = true;
            options.add(option);
        });
    }

    window.removeOption = removeOption;
}); 
document.addEventListener('DOMContentLoaded', function() {
    const optionsSelect = document.getElementById('id_available_options');
    const selectedOptionsDiv = document.getElementById('selected-options');

    if (optionsSelect) {
        optionsSelect.addEventListener('change', function() {
            if (this.value) {
                addOption(this.value, this.options[this.selectedIndex].text);
                this.value = ''; // Reset select
            }
        });
    }
});

function addOption(optionId, optionName) {
    const selectedOptionsDiv = document.getElementById('selected-options');
    if (!selectedOptionsDiv) return;

    // Check if option already exists
    if (document.querySelector(`input[value="${optionId}"]`)) {
        return; // Option already added
    }

    const badge = document.createElement('span');
    badge.className = 'badge bg-primary me-2 mb-2';
    badge.innerHTML = `
        ${optionName}
        <button type="button" class="btn-close btn-close-white" 
                aria-label="Remove" 
                onclick="removeOption('${optionId}')">
        </button>
        <input type="hidden" name="selected_options" value="${optionId}">
    `;
    selectedOptionsDiv.appendChild(badge);
}

function removeOption(optionId) {
    const option = event.target.closest('.badge');
    if (option) {
        option.remove();
    }
} 
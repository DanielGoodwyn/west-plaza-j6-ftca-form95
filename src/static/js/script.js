document.addEventListener('DOMContentLoaded', function() {
    // Calculate total initially in case of pre-filled values (especially if page reloads with data)
    calculateTotal(); 

    // Attach event listener to relevant amount fields
    const amountFields = [
        'field12a_property_damage_amount',
        'field12b_personal_injury_amount',
        'field12c_wrongful_death_amount'
    ];
    amountFields.forEach(function(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', calculateTotal);
        }
    });

    // Field 3 'Other' specify toggle
    const field3OtherCheckbox = document.getElementById('field3_other');
    if (field3OtherCheckbox) {
        field3OtherCheckbox.addEventListener('change', function() {
            toggleField3OtherSpecify(this.checked);
        });
        // Initial check in case the checkbox is pre-checked (e.g. form repopulation)
        toggleField3OtherSpecify(field3OtherCheckbox.checked);
    }
});

function toggleField3OtherSpecify(isChecked) {
    const specifyInput = document.getElementById('field3_other_specify');
    if (specifyInput) {
        specifyInput.style.display = isChecked ? 'block' : 'none';
        if (!isChecked) {
            specifyInput.value = ''; // Clear value if unchecked
        }
    }
}

function calculateTotal() {
    const propDamage = parseFloat(document.getElementById('field12a_property_damage_amount').value) || 0;
    const persInjury = parseFloat(document.getElementById('field12b_personal_injury_amount').value) || 0;
    const wrongDeath = parseFloat(document.getElementById('field12c_wrongful_death_amount').value) || 0;
    
    const total = propDamage + persInjury + wrongDeath;
    
    const totalField = document.getElementById('field12d_total_amount');
    if (totalField) {
        totalField.value = total.toFixed(2);
    }
}

// Ensure calculateTotal is available globally if called from HTML oninput attribute directly 
// (though DOMContentLoaded listener is generally preferred for attaching events)
window.calculateTotal = calculateTotal;
window.toggleField3OtherSpecify = toggleField3OtherSpecify;

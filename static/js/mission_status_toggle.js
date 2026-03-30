document.addEventListener('DOMContentLoaded', function () {
    const statusSelect = document.querySelector('#id_status');
    const durationRow = document.querySelector('.form-row.field-duration_days');

    function toggleDuration() {
        if (statusSelect.value === 'completed') { // или ваше значение для "Завершена"
            durationRow.style.display = '';
        } else {
            durationRow.style.display = 'none';
            const durationInput = document.querySelector('#id_duration_days');
            if (durationInput) durationInput.value = '';
        }
    }

    if (statusSelect) {
        toggleDuration(); // проверить при загрузке
        statusSelect.addEventListener('change', toggleDuration);
    }
});
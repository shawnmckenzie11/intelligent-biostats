document.addEventListener('DOMContentLoaded', function() {
    const columnInput = document.getElementById('deleteColumnText');
    const suggestionsDiv = document.querySelector('.column-suggestions');
    let availableColumns = [];

    // Function to fetch available columns
    function fetchAvailableColumns() {
        fetch('/api/get-available-columns')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    availableColumns = data.columns;
                    // If the input is focused, update suggestions
                    if (document.activeElement === columnInput) {
                        updateSuggestions(columnInput.value);
                    }
                }
            })
            .catch(error => console.error('Error fetching columns:', error));
    }

    // Function to update suggestions based on input
    function updateSuggestions(input) {
        const filteredColumns = availableColumns.filter(column => 
            column.toLowerCase().includes(input.toLowerCase())
        );
        
        suggestionsDiv.innerHTML = '';
        filteredColumns.forEach(column => {
            const div = document.createElement('div');
            div.className = 'column-suggestion-item';
            div.textContent = column;
            div.addEventListener('click', () => {
                columnInput.value = column;
                suggestionsDiv.classList.remove('show');
                validateColumnSelection(column);
            });
            suggestionsDiv.appendChild(div);
        });
        
        if (filteredColumns.length > 0) {
            suggestionsDiv.classList.add('show');
        } else {
            suggestionsDiv.classList.remove('show');
        }
        
        // Validate the current input
        validateColumnSelection(input);
    }

    // Function to validate column selection
    function validateColumnSelection(input) {
        if (!input.trim()) {
            updateValidationStatus('', '');
            return;
        }
        
        fetch('/api/validate-columns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ columns: input })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateValidationStatus('valid', data.message || 'Valid column selection');
            } else {
                updateValidationStatus('invalid', data.error || 'Invalid column selection');
            }
        })
        .catch(error => {
            console.error('Error validating columns:', error);
            updateValidationStatus('error', 'Error validating columns');
        });
    }

    // Function to update validation status display
    function updateValidationStatus(status, message) {
        const statusElement = document.getElementById('columnValidationStatus');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `validation-status ${status}`;
        }
    }

    // Only add event listeners if the elements exist
    if (columnInput && suggestionsDiv) {
        // Event listeners
        columnInput.addEventListener('input', (e) => {
            updateSuggestions(e.target.value);
        });

        columnInput.addEventListener('focus', () => {
            if (availableColumns.length > 0) {
                updateSuggestions(columnInput.value);
            } else {
                fetchAvailableColumns();
            }
        });

        document.addEventListener('click', (e) => {
            if (!columnInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                suggestionsDiv.classList.remove('show');
            }
        });

        // Initial fetch of available columns
        fetchAvailableColumns();
    }
}); 
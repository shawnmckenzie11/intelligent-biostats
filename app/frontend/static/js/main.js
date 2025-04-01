// Main application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const dataPreview = document.getElementById('dataPreview');
    const previewTable = document.getElementById('previewTable');
    const uploadSection = document.getElementById('uploadSection');
    const modifySection = document.getElementById('modifySection');
    const analysisSection = document.getElementById('analysisSection');

    // Handle file selection via click
    dropZone.addEventListener('click', () => fileInput.click());

    // Handle drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });

    function handleFile(file) {
        if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
            alert('Please upload a CSV file');
            return;
        }

        // Display preview using first chunk
        const previewReader = new FileReader();
        const previewChunk = file.slice(0, 1024 * 1024); // First 1MB for preview
        
        previewReader.onload = function(e) {
            const text = e.target.result;
            displayPreview(text);
            uploadFullFile(file);
        };
        previewReader.readAsText(previewChunk);
    }

    function displayPreview(csvText) {
        const rows = csvText.split('\n');
        const headers = rows[0].split(',');
        
        // Create table HTML
        let tableHtml = '<table><thead><tr>';
        headers.forEach(header => {
            tableHtml += `<th>${header.trim()}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';

        // Add first 5 rows of data
        for (let i = 1; i < Math.min(rows.length, 6); i++) {
            const cells = rows[i].split(',');
            tableHtml += '<tr>';
            cells.forEach(cell => {
                tableHtml += `<td>${cell.trim()}</td>`;
            });
            tableHtml += '</tr>';
        }
        tableHtml += '</tbody></table>';

        previewTable.innerHTML = tableHtml;
        
        // Show preview sections
        uploadSection.style.display = 'none';
        dataPreview.style.display = 'block';
        modifySection.style.display = 'block';
    }

    function uploadFullFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Upload successful:', data);
            if (!data.success) {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
    }

    // Handle proceed to analysis
    document.getElementById('proceedButton').addEventListener('click', function() {
        const modificationRequest = document.getElementById('modificationInput').value;
        
        // First, apply any modifications if specified
        if (modificationRequest.trim()) {
            console.log('Attempting modification:', modificationRequest);
            
            fetch('/api/modify-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    modification: modificationRequest 
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Modification response:', data);
                
                // Only update the table if there were actual changes
                if (data.success && data.preview) {
                    updatePreviewTable(data.preview);
                }
                
                // Display status message briefly before hiding
                document.getElementById('modificationStatus').textContent = data.message;
                document.getElementById('modificationStatus').className = 
                    data.success ? 'status-message success' : 'status-message error';
                
                // Hide the modify section after successful processing
                if (data.success) {
                    setTimeout(() => {
                        document.getElementById('modifySection').style.display = 'none';
                    }, 1500); // Hide after 1.5 seconds
                    return getAnalysisOptions();
                }
            })
            .catch(error => {
                console.error('Modification error:', error);
                document.getElementById('modificationStatus').textContent = 'Error: ' + error.message;
                document.getElementById('modificationStatus').className = 'status-message error';
            });
        } else {
            // If no modifications, directly get analysis options and hide the section
            document.getElementById('modifySection').style.display = 'none';
            getAnalysisOptions();
        }
    });

    function getAnalysisOptions() {
        fetch('/api/analyze-options', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAnalysisOptions(data.options);
                analysisSection.style.display = 'block';
                // Scroll to analysis section
                analysisSection.scrollIntoView({ behavior: 'smooth' });
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function displayAnalysisOptions(options) {
        const optionsContainer = document.getElementById('analysisOptions');
        const searchInput = document.getElementById('analysisSearch');
        
        // Store options globally so we can filter them later
        window.allAnalysisOptions = options;
        
        // Initial display of all options
        renderAnalysisOptions(options);
        
        // Add search functionality
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filteredOptions = window.allAnalysisOptions.filter(option => 
                option.name.toLowerCase().includes(searchTerm) ||
                option.description.toLowerCase().includes(searchTerm)
            );
            renderAnalysisOptions(filteredOptions);
        });
    }

    function renderAnalysisOptions(options) {
        const optionsContainer = document.getElementById('analysisOptions');
        
        if (options.length === 0) {
            optionsContainer.innerHTML = `
                <div class="no-results">
                    No matching analyses found
                </div>
            `;
            return;
        }
        
        optionsContainer.innerHTML = options.map(option => `
            <div class="analysis-option ${option.requirements_met ? 'available' : 'unavailable'}">
                <h3>${option.name}</h3>
                <div class="description">${option.description}</div>
                <button 
                    onclick="selectAnalysis('${option.id}')"
                    ${option.requirements_met ? '' : 'disabled'}
                >
                    Select Analysis
                </button>
                <div class="requirements">
                    Requirements: ${option.requirements}
                    <span class="requirements-status ${option.requirements_met ? 'requirements-met' : 'requirements-not-met'}">
                        ${option.requirements_met ? '✓ Met' : '✗ Not met'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    function updatePreviewTable(previewData) {
        console.log('Updating preview table with:', previewData);
        
        // Get the first row to determine column order
        const firstRow = document.querySelector('#previewTable table tr');
        let originalHeaders = [];
        
        if (firstRow) {
            // If table exists, get current column order
            originalHeaders = Array.from(firstRow.getElementsByTagName('th')).map(th => th.textContent);
        } else {
            // For first load, use order from data
            originalHeaders = Object.keys(previewData);
        }
        
        let tableHtml = '<table><thead><tr>';
        originalHeaders.forEach(header => {
            if (header in previewData) {  // Only include headers that still exist
                tableHtml += `<th>${header}</th>`;
            }
        });
        tableHtml += '</tr></thead><tbody>';
        
        const rows = Object.values(previewData)[0].length;
        for (let i = 0; i < rows; i++) {
            tableHtml += '<tr>';
            originalHeaders.forEach(header => {
                if (header in previewData) {
                    tableHtml += `<td>${previewData[header][i]}</td>`;
                }
            });
            tableHtml += '</tr>';
        }
        tableHtml += '</tbody></table>';
        
        previewTable.innerHTML = tableHtml;
        console.log('Preview table updated with preserved column order');
    }
});

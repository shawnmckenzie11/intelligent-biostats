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
        dropZone.style.borderColor = '#3498db';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#e9ecef';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#e9ecef';
        
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (file.type !== 'text/csv') {
            alert('Please upload a CSV file');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const text = e.target.result;
            displayPreview(text);
        };
        reader.readAsText(file);
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
        
        // Hide upload section and show data preview and modify sections
        uploadSection.style.display = 'none';
        dataPreview.style.display = 'block';
        modifySection.style.display = 'block';

        // Send data to server
        fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: csvText })
        })
        .then(response => response.json())
        .then(data => console.log('Upload successful:', data))
        .catch(error => console.error('Error:', error));
    }

    // Handle proceed to analysis with debug logs
    document.getElementById('proceedButton').addEventListener('click', function() {
        console.log('Proceed button clicked');
        const modificationRequest = document.getElementById('modificationInput').value;
        
        // First, apply any modifications if specified
        if (modificationRequest.trim()) {
            console.log('Modification requested:', modificationRequest);
            
            fetch('/api/modify-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    modification: modificationRequest 
                })
            })
            .then(response => {
                console.log('Modification response received');
                return response.json();
            })
            .then(data => {
                console.log('Modification response data:', data);
                if (data.success) {
                    // Update preview table with modified data
                    updatePreviewTable(data.preview);
                    document.getElementById('modificationStatus').textContent = 'Modifications applied successfully!';
                    return getAnalysisOptions();
                } else {
                    throw new Error(data.error || 'Unknown error occurred');
                }
            })
            .catch(error => {
                console.error('Modification error:', error);
                document.getElementById('modificationStatus').textContent = 'Error: ' + error.message;
            });
        } else {
            console.log('No modifications requested, proceeding to analysis');
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
        optionsContainer.innerHTML = options.map(option => `
            <div class="analysis-option">
                <h3>${option.name}</h3>
                <p>${option.description}</p>
                <button onclick="selectAnalysis('${option.id}')">Select</button>
            </div>
        `).join('');
    }

    function updatePreviewTable(previewData) {
        console.log('Updating preview table with:', previewData);
        // Convert preview data back to table format
        const headers = Object.keys(previewData);
        const rows = Object.values(previewData)[0].length;
        
        let tableHtml = '<table><thead><tr>';
        headers.forEach(header => {
            tableHtml += `<th>${header}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';
        
        for (let i = 0; i < rows; i++) {
            tableHtml += '<tr>';
            headers.forEach(header => {
                tableHtml += `<td>${previewData[header][i]}</td>`;
            });
            tableHtml += '</tr>';
        }
        tableHtml += '</tbody></table>';
        
        previewTable.innerHTML = tableHtml;
        console.log('Preview table updated');
    }
});

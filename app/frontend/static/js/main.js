// Main application JavaScript

// Define runOneSampleTTest globally
function runOneSampleTTest() {
    const columnName = document.getElementById('tTestColumnSelect').value;
    const hypothesisValue = parseFloat(document.getElementById('hypothesisValue').value);
    const confidenceLevel = parseFloat(document.getElementById('confidenceLevel').value);

    if (!columnName || isNaN(hypothesisValue)) {
        alert('Please select a variable and enter a valid hypothesized mean value');
        return;
    }

    // Create results container if it doesn't exist
    let resultsDiv = document.getElementById('tTestResults');
    if (!resultsDiv) {
        resultsDiv = document.createElement('div');
        resultsDiv.id = 'tTestResults';
        document.querySelector('.analysis-setup').appendChild(resultsDiv);
    }

    // Show loading state
    resultsDiv.innerHTML = `
        <div class="analysis-results">
            <h5>Analysis Results</h5>
            <p>Running one-sample t-test for variable "${columnName}" with hypothesized mean ${hypothesisValue}...</p>
        </div>
    `;

    // Make API call to run the t-test
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            analysis_type: 'one_sample_t',
            column: columnName,
            hypothesis_value: hypothesisValue,
            confidence_level: confidenceLevel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Format the results
            const results = data.results;
            const pValue = parseFloat(results.p_value).toFixed(4);
            const tStatistic = parseFloat(results.statistic).toFixed(4);
            const mean = parseFloat(results.sample_mean).toFixed(4);
            const stdErr = parseFloat(results.std_error).toFixed(4);
            const ciLower = parseFloat(results.confidence_interval[0]).toFixed(4);
            const ciUpper = parseFloat(results.confidence_interval[1]).toFixed(4);
            
            // Determine if the result is significant
            const isSignificant = results.p_value < (1 - confidenceLevel);
            const significanceText = isSignificant ? 
                `significant at the ${(confidenceLevel * 100)}% confidence level` : 
                `not significant at the ${(confidenceLevel * 100)}% confidence level`;

            resultsDiv.innerHTML = `
                <div class="analysis-results">
                    <h5>One-Sample T-Test Results</h5>
                    <p><strong>Variable:</strong> ${columnName}</p>
                    <p><strong>Hypothesized Mean:</strong> ${hypothesisValue}</p>
                    <p><strong>Sample Mean:</strong> ${mean}</p>
                    <p><strong>Standard Error:</strong> ${stdErr}</p>
                    <p><strong>t-statistic:</strong> ${tStatistic}</p>
                    <p><strong>Degrees of Freedom:</strong> ${results.degrees_of_freedom}</p>
                    <p><strong>p-value:</strong> ${pValue}</p>
                    <p><strong>${(confidenceLevel * 100)}% Confidence Interval:</strong> (${ciLower}, ${ciUpper})</p>
                    <p><strong>Conclusion:</strong> The difference between the sample mean and hypothesized mean is ${significanceText}.</p>
                </div>
            `;
        } else {
            throw new Error(data.error || 'Failed to run analysis');
        }
    })
    .catch(error => {
        console.error('Error running t-test:', error);
        resultsDiv.innerHTML = `
            <div class="analysis-results">
                <h5>Error</h5>
                <p class="error-message">Failed to run analysis: ${error.message}</p>
            </div>
        `;
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const dataPreview = document.getElementById('dataPreview');
    const previewTable = document.getElementById('previewTable');
    const uploadSection = document.getElementById('uploadSection');
    const modifySection = document.getElementById('modifySection');
    const analysisSection = document.getElementById('analysisSection');

    // Initialize overlay panel
    const overlay = document.getElementById('analysisOverlay');
    const toggleOverlay = document.getElementById('toggleOverlay');
    const overlayTab = document.getElementById('overlayTab');
    
    // Hide overlay panel initially and remove expanded class
    overlay.style.display = 'none';
    overlay.classList.remove('expanded');

    // Add click handler for overlay toggle
    toggleOverlay.addEventListener('click', () => {
        overlay.classList.toggle('expanded');
    });

    // Add click handler for overlay tab
    overlayTab.addEventListener('click', () => {
        overlay.classList.add('expanded');
    });

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
        if (!file.name.endsWith('.csv')) {
            alert('Please upload a CSV file');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                // Try to decode as UTF-8 first
                const decoder = new TextDecoder('utf-8', { fatal: true });
                const csvText = decoder.decode(new Uint8Array(e.target.result));
                
                // If we get here, it's valid UTF-8
            displayPreview(csvText);
            
                // Create a new Blob with proper UTF-8 encoding
                const utf8Blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
                const formData = new FormData();
                formData.append('file', utf8Blob, file.name);
                
                // Upload the UTF-8 encoded file
                fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Upload failed');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        console.log('Upload successful:', data);
                    } else {
                        throw new Error(data.error || 'Upload failed');
                    }
                })
                .catch(error => {
                    console.error('Error uploading file:', error);
                    alert('Error uploading file: ' + error.message);
                });
                
            } catch (encodingError) {
                // If UTF-8 decoding fails, try to convert from other encodings
                console.log('UTF-8 decoding failed, attempting to convert from other encodings...');
                
                // Try different encodings in sequence
                const encodings = ['iso-8859-1', 'windows-1252', 'ascii'];
                let converted = false;
                
                for (const encoding of encodings) {
                    try {
                        const decoder = new TextDecoder(encoding);
                        const text = decoder.decode(new Uint8Array(e.target.result));
                        
                        // Convert to UTF-8
                        const encoder = new TextEncoder();
                        const utf8Array = encoder.encode(text);
                        const utf8Text = new TextDecoder('utf-8').decode(utf8Array);
                        
                        // Create a new Blob with proper UTF-8 encoding
                        const utf8Blob = new Blob([utf8Text], { type: 'text/csv;charset=utf-8;' });
                        const formData = new FormData();
                        formData.append('file', utf8Blob, file.name);
                        
                        displayPreview(utf8Text);
                        
                        // Upload the converted file
                        fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Upload failed');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.success) {
                                console.log('Upload successful after conversion:', data);
                                converted = true;
                            } else {
                                throw new Error(data.error || 'Upload failed');
                            }
                        })
                        .catch(error => {
                            console.error('Error uploading converted file:', error);
                            if (!converted) {
                                alert('Error uploading file: ' + error.message);
                            }
                        });
                        
                        converted = true;
                        break;
                        
                    } catch (conversionError) {
                        console.log(`Failed to convert using ${encoding}, trying next encoding...`);
                        continue;
                    }
                }
                
                if (!converted) {
                    alert('Could not process the CSV file. Please ensure it is properly formatted and try again.');
                }
            }
        };
        reader.readAsArrayBuffer(file);  // Read as ArrayBuffer instead of text
    }

    function displayPreview(csvText) {
        const previewTable = document.getElementById('previewTable');
        let tableHtml = '';
        
        // Check if csvText is a string (raw CSV) or an object (modified preview)
        if (typeof csvText === 'string') {
            // Handle raw CSV text
            const rows = csvText.split('\n');
            const headers = rows[0].split(',');
            
            tableHtml = '<table><thead><tr>';
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
        } else {
            // Handle modified preview object
            // Get the column order from the backend
            const columnOrder = csvText.column_order;
            const data = csvText.data;
            const rowCount = data[columnOrder[0]].length;
            
            tableHtml = '<table><thead><tr>';
            // Use the exact order from the backend
            columnOrder.forEach(header => {
                tableHtml += `<th>${header}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';

            // Add first 5 rows of data
            for (let i = 0; i < Math.min(rowCount, 5); i++) {
                tableHtml += '<tr>';
                // Use the exact order from the backend
                columnOrder.forEach(header => {
                    tableHtml += `<td>${data[header][i]}</td>`;
                });
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table>';
        }
        
        previewTable.innerHTML = tableHtml;
        
        // Show preview section
        document.getElementById('dataPreview').style.display = 'block';
        document.getElementById('uploadSection').style.display = 'none';
        
        // Initialize collapsible functionality
        initializeCollapsiblePreview();
    }

    function initializeCollapsiblePreview() {
        const toggleButton = document.getElementById('togglePreview');
        const previewContent = document.getElementById('previewContent');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        // Set initial state (expanded)
        previewContent.style.maxHeight = 'none';
        
        toggleButton.addEventListener('click', () => {
            const isCollapsed = previewContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                previewContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                previewContent.style.maxHeight = 'none';
            } else {
                // Collapse
                previewContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                previewContent.style.maxHeight = '0';
            }
        });
    }

    function initializeDescriptiveStatsCollapsible() {
        const toggleButton = document.getElementById('toggleDescriptive');
        const descriptiveContent = document.getElementById('descriptiveContent');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        // Set initial state (expanded)
        descriptiveContent.style.maxHeight = 'none';
        
        toggleButton.addEventListener('click', () => {
            const isCollapsed = descriptiveContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                descriptiveContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                descriptiveContent.style.maxHeight = 'none';
            } else {
                // Collapse
                descriptiveContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                descriptiveContent.style.maxHeight = '0';
            }
        });
    }

    function initializeOutcomeInsightsCollapsible() {
        const toggleButton = document.getElementById('toggleOutcomeInsights');
        const outcomeContent = document.getElementById('outcomeInsightsContent');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        // Set initial state (expanded)
        outcomeContent.style.maxHeight = 'none';
        
        toggleButton.addEventListener('click', () => {
            const isCollapsed = outcomeContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                outcomeContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                outcomeContent.style.maxHeight = 'none';
            } else {
                // Collapse
                outcomeContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                outcomeContent.style.maxHeight = '0';
            }
        });
    }

    function uploadFullFile(file) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Upload failed');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    resolve(data);
                } else {
                    reject(new Error(data.error || 'Upload failed'));
                }
            })
            .catch(error => {
                reject(error);
            });
        });
    }

    // Initialize tabs when document loads AND when analysis section is shown
    function showAnalysisTabs() {
        const analysisTabsSection = document.getElementById('analysisTabsSection');
        if (analysisTabsSection) {
            analysisTabsSection.style.display = 'block';
            initializeTabs(); // Reinitialize tabs when showing the section
            loadSmartRecommendations(); // Load smart recommendations by default
        }
    }

    // Add tab handling functionality
    function initializeTabs() {
        const tabs = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and panes
                tabs.forEach(t => t.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding pane
                tab.classList.add('active');
                const tabId = tab.getAttribute('data-tab');
                document.getElementById(`${tabId}Tab`).classList.add('active');
                
                // Load content for the selected tab
                if (tabId === 'history') {
                    loadAnalysisHistory();
                } else if (tabId === 'recommendations') {
                    loadSmartRecommendations();
                } else if (tabId === 'analyses') {
                    getAnalysisOptions();
                }
            });
        });

        // Set initial active tab to recommendations
        const recommendationsButton = document.querySelector('[data-tab="recommendations"]');
        const recommendationsPane = document.getElementById('recommendationsTab');
        if (recommendationsButton && recommendationsPane) {
            recommendationsButton.classList.add('active');
            recommendationsPane.classList.add('active');
        }
    }

    // Update the proceed button handler
    document.getElementById('proceedButton').addEventListener('click', function() {
        const validationElement = document.querySelector('.delete-column-validation');
        const deleteColumnRequest = document.getElementById('deleteColumnText').value;
        
        // Hide the preview actions section immediately when proceed button is clicked
        document.querySelector('.preview-actions').style.display = 'none';
        
        if (deleteColumnRequest.trim()) {
            // Get the validated columns from the validation display
            const validColumnsMatch = validationElement.textContent.match(/Columns to delete: (.*)/);
            if (validColumnsMatch && validationElement.classList.contains('valid')) {
                const columnsToDelete = validColumnsMatch[1].split(', ');
                
                fetch('/api/delete-columns-at-start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        columns: columnsToDelete
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update preview table with new data
                        if (data.preview) {
                            displayPreview(data.preview);
                        }
                        
                        // Update status message
                        const statusElement = document.getElementById('modificationStatus');
                        statusElement.textContent = 'Deletions Applied Successfully';
                        statusElement.className = 'status-message';
                        
                        // Show analysis sections
                        document.getElementById('descriptiveStatsSection').style.display = 'block';
                        document.getElementById('analysisTabsSection').style.display = 'block';
                        
                        // Initialize collapsible functionality for descriptive stats
                        initializeDescriptiveStatsCollapsible();
                        
                        // Reinitialize the preview collapsible functionality
                        initializeCollapsiblePreview();
                        
                        // Initialize tabs
                        initializeTabs();
                        
                        // Load descriptive stats
                        loadDescriptiveStats();
                        
                        // Load smart recommendations
                        loadSmartRecommendations();
                        
                        // Add this line to adjust the section after everything is initialized
                        setTimeout(adjustDescriptiveStatsSection, 100); // Small delay to ensure content is rendered
                    } else {
                        const statusElement = document.getElementById('modificationStatus');
                        statusElement.textContent = data.error || 'Error applying deletions';
                        statusElement.className = 'status-message error';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    const statusElement = document.getElementById('modificationStatus');
                    statusElement.textContent = 'Error applying deletions';
                    statusElement.className = 'status-message error';
                });
            } else {
                const statusElement = document.getElementById('modificationStatus');
                statusElement.textContent = 'Please enter valid column specifications';
                statusElement.className = 'status-message error';
            }
        } else {
            // If no columns specified, proceed without deletions
            document.getElementById('descriptiveStatsSection').style.display = 'block';
            document.getElementById('analysisTabsSection').style.display = 'block';
            initializeDescriptiveStatsCollapsible();
            initializeCollapsiblePreview();
            initializeTabs();
            loadDescriptiveStats();
            loadSmartRecommendations();
            
            // Add this line to adjust the section after everything is initialized
            setTimeout(adjustDescriptiveStatsSection, 100); // Small delay to ensure content is rendered
        }
    });

    // Function to get and display analysis options
    function getAnalysisOptions() {
        fetch('/api/analyze-options')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayAnalysisOptions(data.options);
                } else {
                    throw new Error(data.error || 'Failed to get analysis options');
                }
            })
            .catch(error => {
                console.error('Error getting analysis options:', error);
                const analysisOptions = document.getElementById('analysisOptions');
                if (analysisOptions) {
                    analysisOptions.innerHTML = `<div class="error-message">Error loading analysis options: ${error.message}</div>`;
                }
            });
    }

    // Update displayAnalysisOptions to use menu layout
    function displayAnalysisOptions(options) {
        const analysisOptions = document.getElementById('analysisOptions');
        const analysisDetails = document.getElementById('analysisDetails');
        if (!analysisOptions) return;

        let menuHtml = '';
        options.forEach(option => {
            menuHtml += `
                <div class="analysis-menu-item" data-analysis-id="${option.id}">
                    ${option.name}
                </div>
            `;
        });
        analysisOptions.innerHTML = menuHtml;
        
        // Add click handlers for menu items
        const menuItems = analysisOptions.querySelectorAll('.analysis-menu-item');
        menuItems.forEach(item => {
            item.addEventListener('click', () => {
                // Remove active class from all items
                menuItems.forEach(i => i.classList.remove('active'));
                // Add active class to clicked item
                item.classList.add('active');
                
                // Find the corresponding option
                const option = options.find(opt => opt.id === item.dataset.analysisId);
                if (option) {
                    // Special handling for one-sample t-test
                    if (option.id === 'one_sample_t') {
                        displayOneSampleTTestDetails(option);
                    } else {
                        // Display details for other analyses
                        const detailsHtml = `
                            <h4>${option.name}</h4>
                            <div class="description">${option.description}</div>
                            <div class="requirements">
                                <p>Requirements: ${option.requirements} <span class="requirements-status ${option.requirements_met ? 'requirements-met' : 'requirements-not-met'}">
                                    (${option.requirements_met ? '✓ Met' : '✗ Not Met'})
                                </span></p>
                            </div>
                            <button class="proceed-button" 
                                ${!option.requirements_met ? 'disabled' : ''}
                                onclick="runAnalysis('${option.id}')">
                                Run Analysis
                            </button>
                        `;
                        analysisDetails.innerHTML = detailsHtml;
                    }
                }
            });
        });
    }

    function displayOneSampleTTestDetails(option) {
        const analysisDetails = document.getElementById('analysisDetails');
        
        // First, get the column types to populate the picker
        fetch('/api/descriptive-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Get numeric columns from column_types_list
                    const numericColumns = data.stats.column_types.columns.filter((col, index) => {
                        return data.stats.column_types.column_types_list[index] === 'numeric' || 
                               data.stats.column_types.column_types_list[index] === 'discrete';
                    });

                    const detailsHtml = `
                        <h4>${option.name}</h4>
                        <div class="description">${option.description}</div>
                        <div class="requirements">
                            <p>Requirements: ${option.requirements} <span class="requirements-status ${option.requirements_met ? 'requirements-met' : 'requirements-not-met'}">
                                (${option.requirements_met ? '✓ Met' : '✗ Not Met'})
                            </span></p>
                        </div>
                        <div class="analysis-setup">
                            <h5>Analysis Setup</h5>
                            <div class="column-picker">
                                <label for="tTestColumnSelect">Select Variable:</label>
                                <select id="tTestColumnSelect" class="column-select">
                                    <option value="">Select a numeric variable...</option>
                                    ${numericColumns.map(col => `<option value="${col}">${col}</option>`).join('')}
                                </select>
                            </div>
                            <div class="hypothesis-value">
                                <label for="hypothesisValue">Hypothesized Mean:</label>
                                <input type="number" id="hypothesisValue" class="hypothesis-input" step="any">
                            </div>
                            <div class="confidence-level">
                                <label for="confidenceLevel">Confidence Level:</label>
                                <select id="confidenceLevel" class="confidence-select">
                                    <option value="0.95">95%</option>
                                    <option value="0.99">99%</option>
                                    <option value="0.90">90%</option>
                                </select>
                            </div>
                            <button class="proceed-button" 
                                ${!option.requirements_met ? 'disabled' : ''}
                                onclick="runOneSampleTTest()">
                                Run Analysis
                            </button>
                        </div>
                    `;
                    analysisDetails.innerHTML = detailsHtml;

                    // Add event listener for column selection
                    const columnSelect = document.getElementById('tTestColumnSelect');
                    if (columnSelect) {
                        columnSelect.addEventListener('change', (e) => {
                            if (e.target.value) {
                                // Fetch column data to get the mean
                                fetch(`/api/column-data/${encodeURIComponent(e.target.value)}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success && data.column_data.stats.Type === 'numeric') {
                                            // Set the hypothesized mean to the column's mean
                                            document.getElementById('hypothesisValue').value = data.column_data.stats.Mean;
                                        }
                                    });
                            } else {
                                document.getElementById('hypothesisValue').value = '';
                            }
                        });
                    }
                } else {
                    throw new Error(data.error || 'Failed to load column data');
                }
            })
            .catch(error => {
                console.error('Error loading column data:', error);
                analysisDetails.innerHTML = `
                    <div class="error-message">
                        Error loading column data: ${error.message}
                    </div>
                `;
            });
    }

    // Function to run analysis (placeholder for now)
    function runAnalysis(analysisId) {
        console.log(`Running analysis: ${analysisId}`);
        // Implementation to be added later
    }

    function updatePreviewTable(previewData) {
        console.log('Updating preview table with:', previewData);
        
        // Get the column order from the backend
        const columnOrder = previewData.column_order;
        const data = previewData.data;
        const rowCount = data[columnOrder[0]].length;
        
        let tableHtml = '<table><thead><tr>';
        // Use the exact order from the backend
        columnOrder.forEach(header => {
            tableHtml += `<th>${header}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';
        
        // Add first 5 rows of data
        for (let i = 0; i < Math.min(rowCount, 5); i++) {
            tableHtml += '<tr>';
            // Use the exact order from the backend
            columnOrder.forEach(header => {
                tableHtml += `<td>${data[header][i]}</td>`;
            });
            tableHtml += '</tr>';
        }
        tableHtml += '</tbody></table>';
        
        previewTable.innerHTML = tableHtml;
        console.log('Preview table updated with preserved column order');
    }

    function loadDescriptiveStats() {
        const statsContainer = document.getElementById('descriptiveContent');
        if (!statsContainer) {
            console.error('Descriptive stats container not found');
            return;
        }

        // Clear existing content and create a loading indicator
        statsContainer.innerHTML = '<div class="loading-spinner">Loading statistics...</div>';

        // Fetch descriptive stats from the API
        fetch('/api/descriptive-stats')
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                    throw new Error(data.error || 'Failed to load descriptive statistics');
                }
                
                // Display descriptive stats
                displayDescriptiveStats(data.stats);
                })
                .catch(error => {
                console.error('Error loading descriptive stats:', error);
                    statsContainer.innerHTML = `
                        <div class="error-message">
                        Error loading descriptive statistics: ${error.message}
                        </div>
                    `;
                });
        }

    function displayDescriptiveStats(stats) {
        // Store stats globally for use in row restoration
        window.currentStats = stats;
        
        const statsContainer = document.getElementById('descriptiveContent');
        if (!statsContainer) {
            console.error('Stats display container not found');
            return;
        }

        // Clear previous content
        statsContainer.innerHTML = '';

        // Create overall layout structure with file stats summary
        const layoutHtml = `
            <div class="file-stats-summary">
                <span class="stats-item">Rows: ${stats.file_stats.rows.toLocaleString()}</span> |
                <span class="stats-item">Columns: ${stats.file_stats.columns.toLocaleString()}</span> |
                <span class="stats-item">Memory: ${stats.file_stats.memory_usage}</span> |
                <span class="stats-item">Missing Values: ${stats.file_stats.missing_values.toLocaleString()}</span> |
                <span class="stats-item">Types: 
                    ${stats.column_types.numeric > 0 ? `Numeric (${stats.column_types.numeric})` : ''}
                    ${stats.column_types.discrete > 0 ? `Discrete (${stats.column_types.discrete})` : ''}
                    ${stats.column_types.categorical > 0 ? `Categorical (${stats.column_types.categorical})` : ''}
                    ${stats.column_types.ordinal > 0 ? `Ordinal (${stats.column_types.ordinal})` : ''}
                    ${stats.column_types.boolean > 0 ? `Boolean (${stats.column_types.boolean})` : ''}
                    ${stats.column_types.datetime > 0 ? `DateTime (${stats.column_types.datetime})` : ''}
                </span>
            </div>
            <div class="stats-dashboard horizontal">
                <div class="column-stats-panel">
                    <div class="search-actions-container">
                        <div class="search-container">
                            <input type="text" id="columnSearchInput" placeholder="Search columns..." class="column-search">
                        </div>
                        <div class="flags-toggle-container">
                            <label class="flags-toggle-label">
                                <input type="checkbox" id="ignoreFlagsCheckbox" class="flags-toggle-input">
                                <span class="flags-toggle-text">Ignore flags during analysis</span>
                            </label>
                        </div>
                        <div class="action-buttons-container">
                            <button class="action-button add-btn add-to-outcomes">Add to Outcomes</button>
                            <button class="action-button add-btn add-to-expressions">Add to Expressions</button>
                        </div>
                    </div>
                    <div class="column-stats-table-container">
                        <table class="column-stats-table">
                            <thead>
                                <tr>
                                    <th class="select-column">
                                        <input type="checkbox" id="selectAllColumns" class="column-checkbox">
                                    </th>
                                    <th>Name</th>
                                    <th>Type</th>
                                    <th>Flags</th>
                                    <th>Range</th>
                                    <th>Distribution</th>
                                    <th>Preview</th>
                                </tr>
                            </thead>
                            <tbody id="columnStatsTableBody">
                                <!-- Column data will be inserted here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        statsContainer.innerHTML = layoutHtml;

        // Move the chosen-outcomes-expressions-panel to the overlay content
        const overlayContent = document.querySelector('.overlay-content');
        const chosenOutcomesHtml = `
            <div class="chosen-outcomes-expressions-panel">
                <div class="chosen-outcomes-content">
                    <div class="outcomes-expressions-panel">
                        <div class="panel-section-container">
                            <div class="panel-section outcomes-section">
                                <h4>Outcome Variables</h4>
                                <div class="outcomes-table-container">
                                    <table class="variables-table outcomes-table">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Transform</th>
                                                <th>Paired</th>
                                                <th>Timeseries</th>
                                            </tr>
                                        </thead>
                                        <tbody id="outcomesTableBody">
                                            <!-- Outcomes will be added here -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="panel-section expressions-section">
                                <h4>Expression Variables</h4>
                                <div class="expressions-table-container">
                                    <table class="variables-table expressions-table">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Transform</th>
                                                <th>Paired</th>
                                                <th>Timeseries</th>
                                            </tr>
                                        </thead>
                                        <tbody id="expressionsTableBody">
                                            <!-- Expressions will be added here -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        overlayContent.innerHTML = chosenOutcomesHtml;

        // Add click handlers for selecting outcomes and expressions
        document.querySelectorAll('.column-stats-table tbody tr').forEach(row => {
            row.addEventListener('click', function(e) {
                if (!e.target.closest('.action-buttons')) {  // Don't trigger on action buttons
                    const columnName = this.cells[1].textContent;
                    const columnType = this.cells[2].textContent;
                    
                    // Show selection modal
                    showVariableSelectionModal(columnName, columnType);
                }
            });
        });

        // Populate the columns table
        const tableBody = document.getElementById('columnStatsTableBody');
        if (stats.column_types && stats.column_types.columns) {
            const columns = stats.column_types.columns;
            const columnTypes = stats.column_types.column_types_list || [];
            
            columns.forEach((column, index) => {
                const columnType = columnTypes[index] || 'unknown';
                const missingCount = stats.missing_values_by_column[column] || 0;
                
                // Check if this column has outliers
                let hasOutliers = false;
                if ((columnType === 'numeric' || columnType === 'discrete') && 
                    stats.outlier_info && stats.outlier_info[column]) {
                    hasOutliers = stats.outlier_info[column].count > 0;
                }
                
                const row = document.createElement('tr');
                row.setAttribute('data-type', columnType);
                row.innerHTML = `
                    <td class="select-column">
                        <input type="checkbox" class="column-checkbox" data-column="${column}">
                    </td>
                    <td>${column}</td>
                    <td>
                        <span class="column-type ${columnType}">${columnType}</span>
                    </td>
                    <td>
                        ${hasOutliers ? `<span class="flag-indicator outlier" title="${stats.outlier_info[column].count} outliers (${stats.outlier_info[column].percentage.toFixed(1)}%)">⚠️</span>` : ''}
                        ${missingCount > 0 ? `<span class="flag-indicator missing" title="${missingCount} missing values (${((missingCount / stats.file_stats.rows) * 100).toFixed(1)}%)">❌</span>` : ''}
                    </td>
                    <td>${getColumnRange(column, columnType, stats)}</td>
                    <td class="data-preview-cell">
                        ${getDistributionInfo(column, columnType, stats)}
                    </td>
                    <td>
                        <button class="action-button preview-btn" data-column="${column}" data-type="${columnType}">Preview</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });

            // Add event listeners to the action buttons
            document.querySelectorAll('.preview-btn').forEach(button => {
            button.addEventListener('click', function() {
                const column = this.getAttribute('data-column');
                    const type = this.getAttribute('data-type');
                    showColumnPreview(column, type);
                });
            });
            
            // Add search functionality
            const searchInput = document.getElementById('columnSearchInput');
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                document.querySelectorAll('#columnStatsTableBody tr').forEach(row => {
                    const columnName = row.cells[1].textContent.toLowerCase();
                    if (columnName.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
        });
        }

        // After populating the table
        initializeEditButtons();

        // Add the select all functionality
        document.getElementById('selectAllColumns').addEventListener('change', function(e) {
            // Get all checkboxes in visible rows
            const visibleCheckboxes = document.querySelectorAll('#columnStatsTableBody tr:not([style*="display: none"]) .column-checkbox');
            visibleCheckboxes.forEach(checkbox => {
                checkbox.checked = e.target.checked;
            });
        });

        // Add the action buttons functionality
        document.querySelector('.add-to-outcomes').addEventListener('click', function() {
            // Get only visible rows' checkboxes (excluding the header checkbox)
            const visibleCheckedBoxes = Array.from(document.querySelectorAll('#columnStatsTableBody tr:not([style*="display: none"]) .column-checkbox:checked'));
            
            if (visibleCheckedBoxes.length > 0) {
                let successfulAdd = false;
                visibleCheckedBoxes.forEach(checkbox => {
                    const row = checkbox.closest('tr');
                    const columnName = row.cells[1].textContent;
                    const columnType = row.cells[2].querySelector('.column-type').textContent;
                    
                    // Only remove row if successfully added to outcomes list
                    if (addToVariableList('outcomesList', columnName, columnType)) {
                        // Remove the row from the table
                        row.remove();
                        successfulAdd = true;
                    }
                });
                
                // Show and expand overlay only on first successful addition
                if (successfulAdd && overlay.style.display === 'none') {
                    overlay.style.display = 'block';
                    overlay.classList.add('expanded');
                }
                
                // Uncheck all remaining checkboxes and the select all checkbox
                document.querySelectorAll('.column-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
                document.getElementById('selectAllColumns').checked = false;
            }
        });

        document.querySelector('.add-to-expressions').addEventListener('click', function() {
            // Get only visible rows' checkboxes (excluding the header checkbox)
            const visibleCheckedBoxes = Array.from(document.querySelectorAll('#columnStatsTableBody tr:not([style*="display: none"]) .column-checkbox:checked'));
            
            if (visibleCheckedBoxes.length > 0) {
                visibleCheckedBoxes.forEach(checkbox => {
                    const row = checkbox.closest('tr');
                    const columnName = row.cells[1].textContent;
                    const columnType = row.cells[2].querySelector('.column-type').textContent;
                    
                    // Only remove row if successfully added to expressions list
                    if (addToVariableList('expressionsList', columnName, columnType)) {
                        // Remove the row from the table
                        row.remove();
                    }
                });
                
                // Uncheck all remaining checkboxes and the select all checkbox
                document.querySelectorAll('.column-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
                document.getElementById('selectAllColumns').checked = false;
            }
        });
    }
    
    function getColumnRange(column, columnType, stats) {
        if (columnType === 'numeric' || columnType === 'discrete') {
            const columnStats = stats.distribution_analysis[column];
            if (columnStats && columnStats.descriptive_stats) {
                const min = columnStats.descriptive_stats.min;
                const max = columnStats.descriptive_stats.max;
                if (min !== undefined && max !== undefined) {
                    // Format numbers without decimals if they are integers
                    const formatNumber = (num) => {
                        return Number.isInteger(num) ? num.toString() : num.toFixed(2);
                    };
                    return `
                        <div class="range-container">
                            <span class="range-display" data-min="${min}" data-max="${max}">${formatNumber(min)} - ${formatNumber(max)}</span>
                            <a href="#" class="edit-icon" data-column="${column}" title="Edit range">✏️</a>
                        </div>`;
                }
            }
            return 'N/A';
        } else if (columnType === 'timeseries') {
            const timeStats = stats.datetime_stats[column];
            if (timeStats) {
                return `${timeStats.start_date} - ${timeStats.end_date}`;
            }
            return 'N/A';
        }
        return 'N/A';
    }

    function getDistributionInfo(column, columnType, stats) {
        if (columnType === 'numeric' || columnType === 'discrete') {
            const columnStats = stats.distribution_analysis[column];
            if (columnStats) {
                return `${columnStats.distribution_type || 'Unknown'}`;
            }
        } else if (columnType === 'categorical') {
            const catStats = stats.categorical_stats[column];
            if (catStats) {
                return `${catStats.unique_count} unique values`;
            }
        } else if (columnType === 'ordinal') {
            const ordStats = stats.ordinal_stats[column];
            if (ordStats) {
                return `${ordStats.unique_count} ordered values`;
            }
        } else if (columnType === 'boolean') {
            const boolStats = stats.boolean_stats[column];
            if (boolStats) {
                return `True: ${boolStats.true_percentage.toFixed(1)}%`;
            }
        } else if (columnType === 'timeseries') {
            const timeStats = stats.datetime_stats[column];
            if (timeStats) {
                return `Interval: ${timeStats.time_interval}`;
            }
        }
        return 'N/A';
    }

    // Add function to load and display smart recommendations
    function loadSmartRecommendations() {
        fetch('/api/smart-recommendations')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displaySmartRecommendations(data.recommendations);
                } else {
                    throw new Error(data.error || 'Failed to load recommendations');
                }
            })
            .catch(error => {
                console.error('Error loading recommendations:', error);
                document.getElementById('smartRecommendations').innerHTML = 
                    `<div class="error-message">Error loading recommendations: ${error.message}</div>`;
            });
    }

    function displaySmartRecommendations(recommendations) {
        const container = document.getElementById('smartRecommendations');
        let html = '<div class="recommendations-container">';
        
        // Create sections with lazy loading
        const sections = [
            {
                id: 'critical',
                title: 'Critical Issues',
                description: 'These issues must be addressed before proceeding with analysis.',
                data: recommendations.critical_issues,
                priority: 1
            },
            {
                id: 'high-priority',
                title: 'High Priority Recommendations',
                description: 'Important considerations that may affect your analysis.',
                data: recommendations.high_priority,
                priority: 2
            },
            {
                id: 'suggested',
                title: 'Suggested Analyses',
                description: 'Recommended statistical approaches based on your data structure.',
                data: recommendations.suggested_analyses,
                priority: 3
            },
            {
                id: 'quality',
                title: 'Data Quality Considerations',
                description: 'Issues that may affect data quality and reliability.',
                data: recommendations.data_quality,
                priority: 4
            },
            {
                id: 'methodological',
                title: 'Methodological Notes',
                description: 'General considerations for statistical analysis.',
                data: recommendations.methodological_notes,
                priority: 5
            }
        ];

        // Sort sections by priority
        sections.sort((a, b) => a.priority - b.priority);

        // Create section placeholders
        sections.forEach(section => {
            if (section.data.length > 0) {
                html += `
                    <div class="recommendations-section ${section.id}" id="${section.id}-section">
                        <h4>${section.title}</h4>
                        <p class="section-description">${section.description}</p>
                        <div class="recommendations-content" id="${section.id}-content">
                            <div class="loading-placeholder">Loading recommendations...</div>
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
        container.innerHTML = html;

        // Lazy load each section
        sections.forEach(section => {
            if (section.data.length > 0) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            loadSection(section);
                            observer.unobserve(entry.target);
                        }
                    });
                }, { threshold: 0.1 });

                const sectionElement = document.getElementById(`${section.id}-section`);
                if (sectionElement) {
                    observer.observe(sectionElement);
                }
            }
        });
    }

    function loadSection(section) {
        const contentElement = document.getElementById(`${section.id}-content`);
        if (!contentElement) return;

        const recommendationsHtml = section.data.map(rec => `
            <div class="recommendation-card ${section.id}">
                <h5>${rec.message}</h5>
                ${rec.details ? `
                    <div class="details">
                        ${Object.entries(rec.details).map(([key, value]) => `
                            <p><strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> 
                            ${typeof value === 'object' ? JSON.stringify(value) : value}</p>
                        `).join('')}
                    </div>
                ` : ''}
                <div class="recommendations-list">
                    <p class="suggested-tests">Suggested approaches: ${rec.suggested_tests.join(', ')}</p>
                    ${rec.references ? `
                        <p class="references">References: ${rec.references.join(', ')}</p>
                    ` : ''}
                </div>
            </div>
        `).join('');

        contentElement.innerHTML = recommendationsHtml;
    }

    function loadAnalysisHistory() {
        fetch('/api/analysis-history')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayAnalysisHistory(data.analyses);
                } else {
                    throw new Error(data.error || 'Failed to load analysis history');
                }
            })
            .catch(error => {
                console.error('Error loading analysis history:', error);
                document.getElementById('analysisHistory').innerHTML = `
                    <div class="error-message">
                        Failed to load analysis history: ${error.message}
                    </div>
                `;
            });
    }

    function displayAnalysisHistory(analyses) {
        const historyContent = document.getElementById('analysisHistory');
        if (!analyses || analyses.length === 0) {
            historyContent.innerHTML = '<p class="no-results-message">No analysis history available</p>';
            return;
        }

        // Store analyses in a closure for pagination
        let currentPage = 1;
        const recordsPerPage = 10;
        const totalPages = Math.ceil(analyses.length / recordsPerPage);

        function getCurrentPageAnalyses() {
            const start = (currentPage - 1) * recordsPerPage;
            const end = start + recordsPerPage;
            return analyses.slice(start, end);
        }

        function updatePagination() {
            const paginationInfo = document.getElementById('paginationInfo');
            const prevButton = document.getElementById('prevPage');
            const nextButton = document.getElementById('nextPage');

            paginationInfo.textContent = `Page ${currentPage} of ${totalPages}`;
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;
        }

        function renderTable() {
            const currentAnalyses = getCurrentPageAnalyses();
            
            let html = `
                <div class="history-actions">
                    <button id="deleteSelected" class="delete-button" disabled>Delete Selected</button>
                </div>
                <div class="history-panel">
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th style="width: 30px;"><input type="checkbox" id="selectAll"></th>
                                <th>Date & Time</th>
                                <th>Test Name</th>
                                <th>Input File</th>
                                <th>Modifications</th>
                                <th>Conclusion</th>
                                <th style="width: 100px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            currentAnalyses.forEach(analysis => {
                const date = new Date(analysis.date_time).toLocaleString();
                const modifications = analysis.modifications ? 
                    JSON.parse(analysis.modifications).length : 0;
                
                html += `
                    <tr>
                        <td><input type="checkbox" class="analysis-checkbox" data-id="${analysis.id}"></td>
                        <td>${date}</td>
                        <td>${analysis.test_name}</td>
                        <td>${analysis.input_file}</td>
                        <td>${modifications} modifications</td>
                        <td>${analysis.conclusion}</td>
                        <td>
                            <button class="details-button" data-id="${analysis.id}">Details</button>
                        </td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
                <div class="pagination-controls">
                    <button id="prevPage" class="pagination-button" disabled>Previous</button>
                    <span id="paginationInfo">Page ${currentPage} of ${totalPages}</span>
                    <button id="nextPage" class="pagination-button" disabled>Next</button>
                </div>
            `;

            historyContent.innerHTML = html;

            // Add event listeners for checkboxes
            const selectAll = document.getElementById('selectAll');
            const checkboxes = document.querySelectorAll('.analysis-checkbox');
            const deleteButton = document.getElementById('deleteSelected');

            selectAll.addEventListener('change', function() {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
                updateDeleteButton();
            });

            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', updateDeleteButton);
            });

            // Add event listeners for details buttons
            document.querySelectorAll('.details-button').forEach(button => {
                button.addEventListener('click', function() {
                    const analysisId = this.dataset.id;
                    const analysis = analyses.find(a => a.id === parseInt(analysisId));
                    if (analysis) {
                        showAnalysisDetails(analysis);
                    }
                });
            });

            // Add event listeners for pagination
            document.getElementById('prevPage').addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    renderTable();
                    updatePagination();
                }
            });

            document.getElementById('nextPage').addEventListener('click', () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderTable();
                    updatePagination();
                }
            });

            // Add event listener for delete button
            deleteButton.addEventListener('click', deleteSelectedAnalyses);
        }

        renderTable();
        updatePagination();
    }

    function updateDeleteButton() {
        const deleteButton = document.getElementById('deleteSelected');
        const checkedBoxes = document.querySelectorAll('.analysis-checkbox:checked');
        deleteButton.disabled = checkedBoxes.length === 0;
    }

    function deleteSelectedAnalyses() {
        const checkedBoxes = document.querySelectorAll('.analysis-checkbox:checked');
        const ids = Array.from(checkedBoxes).map(checkbox => checkbox.dataset.id);
        
        if (ids.length === 0) return;

        if (confirm(`Are you sure you want to delete ${ids.length} selected analysis(es)?`)) {
            fetch('/api/delete-analyses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ids: ids })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadAnalysisHistory(); // Reload the history
                } else {
                    alert('Error deleting analyses: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting analyses');
            });
        }
    }

    function showAnalysisDetails(analysis) {
        // Create modal content
        const modalContent = `
            <div class="modal-content">
                <h3>Analysis Details</h3>
                <div class="analysis-details-content">
                    <p><strong>Test Name:</strong> ${analysis.test_name}</p>
                    <p><strong>Date & Time:</strong> ${new Date(analysis.date_time).toLocaleString()}</p>
                    <p><strong>Input File:</strong> ${analysis.input_file}</p>
                    <p><strong>Modifications:</strong> ${analysis.modifications ? 
                        JSON.parse(analysis.modifications).length : 0}</p>
                    <div class="test-details">
                        <h4>Test Details:</h4>
                        <pre>${JSON.stringify(analysis.test_details, null, 2)}</pre>
                    </div>
                    <div class="conclusion">
                        <h4>Conclusion:</h4>
                        <p>${analysis.conclusion}</p>
                    </div>
                </div>
                <button class="close-modal">Close</button>
            </div>
        `;

        // Create and show modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = modalContent;
        document.body.appendChild(modal);

        // Add event listener for close button
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    function modifyData() {
        const modification = document.getElementById('deleteColumnText').value;
        if (!modification) {
            alert('Please enter a modification request');
            return;
        }

        fetch('/api/delete-columns-at-start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ modification: modification })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updatePreviewTable(data.preview);
                document.getElementById('deleteColumnText').value = '';
                alert('Modifications applied successfully');
            } else {
                console.error('Modification error:', data.error);
                alert(`Modification error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error applying modifications. Please try again.');
        });
    }

    // Reset DataManager when page is refreshed
    window.addEventListener('beforeunload', function() {
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(error => {
            console.error('Error resetting DataManager:', error);
        });
    });

    // Add event listener for delete column input
    const deleteColumnInput = document.getElementById('deleteColumnText');
    if (deleteColumnInput) {
        deleteColumnInput.addEventListener('input', function(e) {
            const input = e.target.value;
            const validationDiv = document.querySelector('.delete-column-validation');
            
            // Create validation div if it doesn't exist
            if (!validationDiv) {
                const newValidationDiv = document.createElement('div');
                newValidationDiv.className = 'delete-column-validation';
                e.target.parentNode.appendChild(newValidationDiv);
            }
            
            // Clear previous validation
            const validationElement = document.querySelector('.delete-column-validation');
            validationElement.innerHTML = '';
            
            if (input.trim()) {
                // Get column suggestions and validation state
                fetch('/api/column-suggestions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ input: input })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Display validation state
                        if (data.is_valid) {
                            // Show valid columns in green
                            validationElement.className = 'delete-column-validation valid';
                            validationElement.textContent = `Columns to delete: ${data.columns.join(', ')}`;
                        } else {
                            // Show error in red
                            validationElement.className = 'delete-column-validation invalid';
                            validationElement.textContent = data.error;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error validating columns:', error);
                    validationElement.className = 'delete-column-validation invalid';
                    validationElement.textContent = 'Error validating columns';
                });
            } else {
                // Show default error state when input is empty
                validationElement.className = 'delete-column-validation invalid';
                validationElement.textContent = 'No column specification provided';
            }
        });
    }

    // Function to show column preview with plots
    function showColumnPreview(column, type) {
        // Create modal container
        const modal = document.createElement('div');
        modal.className = 'plot-preview-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h4>Preview: ${column}</h4>
                    <button class="close-modal">×</button>
                </div>
                <div class="modal-body">
                    <div class="loading-spinner">Loading preview...</div>
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(modal);
        
        // Add show class after a brief delay to trigger animation
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
        
        // Close handlers
        const closeModal = () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300); // Wait for animation
        };
        
        modal.querySelector('.close-modal').addEventListener('click', closeModal);
        modal.addEventListener('click', e => {
            if (e.target === modal) closeModal();
        });
        
        // Fetch preview plots
        fetch(`/api/preview-plots/${encodeURIComponent(column)}`)
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(text);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' && data.plots && data.plots.preview) {
                    modal.querySelector('.modal-body').innerHTML = `
                        <img src="data:image/png;base64,${data.plots.preview}" 
                             alt="Preview plots for ${column}">
                    `;
                } else {
                    throw new Error(data.message || 'Failed to generate preview');
                }
            })
            .catch(error => {
                console.error('Error in plot generation:', error);
                modal.querySelector('.modal-body').innerHTML = `
                    <div class="error-message">
                        Error generating preview: ${error.message}
                        <br>
                        <small>Check browser console for more details</small>
                    </div>
                `;
            });
    }

    // Create editor modal if it doesn't exist
    if (!document.getElementById('editor-modal')) {
        const modalHtml = `
            <div id="editor-modal" class="modal">
                <div class="modal-content">
                    <h3>Edit Column Range</h3>
                    <div id="current-range-display" class="current-range"></div>
                    <div class="input-group">
                        <label for="start-index">Start Value:</label>
                        <input type="number" id="start-index" step="any">
                    </div>
                    <div class="input-group">
                        <label for="end-index">End Value:</label>
                        <input type="number" id="end-index" step="any">
                    </div>
                    <div id="validation-message" class="validation-message"></div>
                    <div id="editor-loading" class="loading-spinner" style="display: none;">
                        Applying changes...
                    </div>
                    <div class="modal-actions">
                        <button class="apply-changes proceed-button">Apply Changes</button>
                        <button class="close-modal action-button">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Initialize the editor modal to be hidden
    const editorModal = document.getElementById('editor-modal');
    if (editorModal) {
        editorModal.style.display = 'none';
        editorModal.classList.remove('show');
    }

    // Add event listeners for edit buttons
    function initializeEditButtons() {
        document.querySelectorAll('.edit-icon').forEach(icon => {
            icon.addEventListener('click', async function(e) {
                e.preventDefault();
                const row = this.closest('tr');
                const column = row.cells[1].textContent; // Get column name from second cell
                
                console.log('Column being edited:', column);
                console.log('Column type:', typeof column);
                console.log('Fetching initial column data and flags...');
                const response = await fetch('/api/column-data-and-flags', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ column: column })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Initial column state:', data);
                } else {
                    const errorData = await response.json();
                    console.error('Error fetching initial data:', errorData);
                }
                
                // Get the current min and max values from the data attributes
                const rangeCell = row.querySelector('.range-container');
                const rangeDisplay = rangeCell.querySelector('.range-display');
                const currentMin = parseFloat(rangeDisplay.getAttribute('data-min'));
                const currentMax = parseFloat(rangeDisplay.getAttribute('data-max'));

                // Format numbers without decimals if they are integers
                const formatNumber = (num) => {
                    return Number.isInteger(num) ? num.toString() : num.toFixed(2);
                };

                // Create inline edit form with current values
                rangeCell.innerHTML = `
                    <form class="range-edit-form">
                        <input type="number" class="range-input min-input" value="${formatNumber(currentMin)}" step="any">
                        <span>-</span>
                        <input type="number" class="range-input max-input" value="${formatNumber(currentMax)}" step="any">
                        <button type="submit" class="save-range">✓</button>
                        <button type="button" class="cancel-edit">✗</button>
                        <div class="validation-message"></div>
                    </form>
                `;

                // Show the form
                const form = rangeCell.querySelector('.range-edit-form');
                form.classList.add('active');
                
                // Store original values for cancel
                const originalContent = `
                    <div class="range-container">
                        <span class="range-display" data-min="${currentMin}" data-max="${currentMax}">${formatNumber(currentMin)} - ${formatNumber(currentMax)}</span>
                        <a href="#" class="edit-icon" data-column="${column}" title="Edit range">✏️</a>
                    </div>`;
                
                // Focus the first input
                form.querySelector('.min-input').focus();
                
                // Handle form submission
                form.addEventListener('submit', async function(e) {
                            e.preventDefault();
                    const minInput = this.querySelector('.min-input');
                    const maxInput = this.querySelector('.max-input');
                    const validationMessage = this.querySelector('.validation-message');
                    
                    const newMin = parseFloat(minInput.value);
                    const newMax = parseFloat(maxInput.value);
                    
                    console.log('Column being edited:', column);
                    console.log('Column type:', typeof column);
                    console.log('Updating column flags with:', {
                        column: column,
                        min_value: newMin,
                        max_value: newMax
                    });
                    
                    // Validate inputs
                            if (isNaN(newMin) || isNaN(newMax)) {
                                validationMessage.textContent = 'Please enter valid numbers';
                                return;
                            }
                            
                            if (newMin >= newMax) {
                        validationMessage.textContent = 'Minimum value must be less than maximum value';
                                return;
                            }
                            
                    try {
                        // Get initial column data and flags
                        const initialDataResponse = await fetch('/api/column-data-and-flags', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                            body: JSON.stringify({ column: column })
                        });
                        
                        if (initialDataResponse.ok) {
                            const initialData = await initialDataResponse.json();
                            console.log('Initial column state:', initialData);
                } else {
                            const errorData = await initialDataResponse.json();
                            console.error('Error fetching initial data:', errorData);
                        }
                        
                        // First, update the range flags
                        const flagResponse = await fetch('/api/update-column-flags', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                column: column,
                                min_value: newMin,
                                max_value: newMax
                            })
                        });
                        
                        // Debug log the response
                        console.log('Flag update response status:', flagResponse.status);
                        const flagData = await flagResponse.clone().json().catch(e => console.error('Error parsing flag response:', e));
                        console.log('Flag update response data:', flagData);
                        
                        if (!flagResponse.ok) {
                            throw new Error(flagData?.error || 'Failed to update column flags');
                        }
                        
                        // Get updated column data and flags after the change
                        const updatedDataResponse = await fetch('/api/column-data-and-flags', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ column: column })
                        });
                        
                        if (updatedDataResponse.ok) {
                            const updatedData = await updatedDataResponse.json();
                            console.log('Updated column state:', updatedData);
                } else {
                            const errorData = await updatedDataResponse.json();
                            console.error('Error fetching updated data:', errorData);
                        }

                        // Then, update the column statistics ignoring flags
                        const statsResponse = await fetch('/api/update-column-stats', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                column: column
                            })
                        });
                        
                        if (!statsResponse.ok) {
                            throw new Error('Failed to update column statistics');
                        }
                        
                        const result = await statsResponse.json();
                        if (result.success) {
                            // Update the display with new values and data attributes
                            const newStats = result.stats;
                            
                            // Create the updated row content
                            rangeCell.innerHTML = `
                                <div class="range-container">
                                    <span class="range-display" data-min="${newStats.min}" data-max="${newStats.max}">
                                        ${formatNumber(newStats.min)} - ${formatNumber(newStats.max)}
                                    </span>
                                    <a href="#" class="edit-icon" data-column="${column}" title="Edit range">✏️</a>
                                </div>`;
                                
                            // Update flag indicators if provided
                            const flagStats = result.flag_stats;
                            if (flagStats) {
                                const flagsCell = rangeCell.closest('tr').querySelector('td:nth-child(3)');
                                let flagsHtml = '';
                                
                                if (flagStats.outliers > 0) {
                                    flagsHtml += `<span class="flag-indicator outlier" title="${flagStats.outliers} outliers (${flagStats.outlier_percentage.toFixed(1)}%)">⚠️</span>`;
                                }
                                if (flagStats.missing > 0) {
                                    flagsHtml += `<span class="flag-indicator missing" title="${flagStats.missing} missing values (${flagStats.missing_percentage.toFixed(1)}%)">❌</span>`;
                                }
                                if (flagStats.outofbounds > 0) {
                                    flagsHtml += `<span class="flag-indicator outofbounds" title="${flagStats.outofbounds} values out of bounds (${flagStats.outofbounds_percentage.toFixed(1)}%)">⛔</span>`;
                                }
                                
                                flagsCell.innerHTML = flagsHtml;
                            }
                            
                            // Reinitialize the edit icon
                            initializeEditButtons();
                            
            } else {
                            throw new Error(result.error || 'Failed to update range');
            }
        } catch (error) {
                        console.error('Error updating range:', error);
                        validationMessage.textContent = error.message;
                    }
                });
                
                // Handle cancel button
                const cancelButton = form.querySelector('.cancel-edit');
                cancelButton.addEventListener('click', function() {
                    rangeCell.innerHTML = originalContent;
                    // Reinitialize the edit icon
                    initializeEditButtons();
                });
            });
        });
    }

    // Add event listeners for modal inputs
    const startInput = document.getElementById('start-index');
    const endInput = document.getElementById('end-index');
    
    if (startInput) startInput.addEventListener('input', validateInputs);
    if (endInput) endInput.addEventListener('input', validateInputs);
    
    // Close modal when clicking outside
    if (editorModal) {
        editorModal.addEventListener('click', (e) => {
            if (e.target.id === 'editor-modal') {
                closeEditorModal();
            }
        });
    }

    // Make initializeEditButtons available to other functions
    window.initializeEditButtons = initializeEditButtons;

    // Add styles for sticky header
    const styleSheet = document.createElement("style");
    styleSheet.textContent = `
        .column-stats-table-container {
            position: relative;
            overflow: auto;
            max-height: 500px;
        }

        .column-stats-table thead {
            position: sticky;
            top: 0;
            z-index: 10;
            background: white;
        }

        .column-stats-table thead tr {
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Optional: adds shadow for better separation */
        }

        .column-stats-table thead th {
            position: relative;
            background: white; /* Or match your table header background */
        }

        .column-stats-table thead th.select-column {
            z-index: 11; /* Ensure checkbox column stays on top */
        }

        .column-stats-table thead th input[type="checkbox"] {
            position: relative;
            z-index: 12; /* Ensure checkbox itself stays on top */
        }
    `;
    document.head.appendChild(styleSheet);

    // Add after the search input event listener
            
            // Add event listener for ignore flags checkbox
            const ignoreFlagsCheckbox = document.getElementById('ignoreFlagsCheckbox');
            if (ignoreFlagsCheckbox) {
                ignoreFlagsCheckbox.addEventListener('change', function(e) {
                    const isIgnoreFlags = e.target.checked;
                    // Store the state in a data attribute on the container
                    document.querySelector('.column-stats-panel').dataset.ignoreFlags = isIgnoreFlags;
                    
                    // You can add additional logic here to handle the flag state
                    console.log('Ignore flags during analysis:', isIgnoreFlags);
                });
            }
});

// Move modal-related functions outside DOMContentLoaded
function showEditorModal(currentStart, currentEnd) {
    const modal = document.getElementById('editor-modal');
    if (!modal) {
        console.error('Editor modal element not found!');
        return;
    }
    
    const startInput = document.getElementById('start-index');
    const endInput = document.getElementById('end-index');
    const currentRangeDisplay = document.getElementById('current-range-display');
    
    // Pre-set values before showing modal
    startInput.value = currentStart;
    endInput.value = currentEnd;
    currentRangeDisplay.textContent = `${currentStart}-${currentEnd}`;
    
    // Reset any previous validation states
    document.getElementById('validation-message').textContent = '';
    const applyButton = document.querySelector('.apply-changes');
    if (applyButton) {
        applyButton.disabled = false;
    }
    
    // Show modal immediately
    modal.style.display = 'flex';
    modal.classList.add('show');
    
    validateInputs();
}

function closeEditorModal() {
    const modal = document.getElementById('editor-modal');
    if (!modal) {
        console.error('Editor modal element not found!');
        return;
    }
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

function validateInputs() {
    const startInput = document.getElementById('start-index');
    const endInput = document.getElementById('end-index');
    const validationMessage = document.getElementById('validation-message');
    const applyButton = document.querySelector('.apply-changes');
    
    const start = parseInt(startInput.value);
    const end = parseInt(endInput.value);
    
    if (isNaN(start) || isNaN(end)) {
        validationMessage.textContent = 'Please enter valid numbers';
        applyButton.disabled = true;
        return false;
    }
    
    if (start < 0 || end < 0) {
        validationMessage.textContent = 'Indices must be non-negative';
        applyButton.disabled = true;
        return false;
    }
    
    if (start >= end) {
        validationMessage.textContent = 'Start index must be less than end index';
        applyButton.disabled = true;
        return false;
    }
    
    validationMessage.textContent = '';
    applyButton.disabled = false;
    return true;
}

async function applyColumnChanges(column) {
    if (!validateInputs()) return;
    
    const startInput = document.getElementById('start-index');
    const endInput = document.getElementById('end-index');
    const loadingElement = document.getElementById('editor-loading');
    
    if (loadingElement) loadingElement.style.display = 'flex';
    
    try {
        const response = await fetch('/api/update-column-range', {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                column: column,
                start_index: parseFloat(startInput.value),
                end_index: parseFloat(endInput.value)
                })
            });
            
        if (!response.ok) throw new Error('Failed to update column range');
        
        const result = await response.json();
        if (result.success) {
            closeEditorModal();
            // Refresh the data display
            loadDescriptiveStats();
            } else {
            throw new Error(result.error || 'Failed to update column range');
            }
        } catch (error) {
        console.error('Error updating column range:', error);
        const validationMessage = document.getElementById('validation-message');
        if (validationMessage) {
            validationMessage.textContent = error.message;
            validationMessage.style.color = 'red';
        }
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

// Add event listeners for real-time validation
    document.addEventListener('DOMContentLoaded', function() {
    const startInput = document.getElementById('start-index');
    const endInput = document.getElementById('end-index');
    const modal = document.getElementById('editor-modal');
    
    if (startInput) startInput.addEventListener('input', validateInputs);
    if (endInput) endInput.addEventListener('input', validateInputs);
    
    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'editor-modal') {
                closeEditorModal();
            }
        });
    }
});

function showVariableSelectionModal(columnName, columnType) {
    const modal = document.createElement('div');
    modal.className = 'modal variable-selection-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Select Variable Type for ${columnName}</h3>
            <p>Choose how this variable will be used in your analysis:</p>
            <div class="selection-options">
                <button class="selection-btn outcome-btn">Add as Outcome Variable</button>
                <button class="selection-btn expression-btn">Add as Expression Variable</button>
            </div>
            <button class="close-modal">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);

    // Add event listeners
    modal.querySelector('.outcome-btn').addEventListener('click', () => {
        addToVariableList('outcomesList', columnName, columnType);
        modal.remove();
    });

    modal.querySelector('.expression-btn').addEventListener('click', () => {
        addToVariableList('expressionsList', columnName, columnType);
        modal.remove();
    });

    modal.querySelector('.close-modal').addEventListener('click', () => {
        modal.remove();
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

function addToVariableList(tableId, columnName, columnType) {
    const tableBody = document.getElementById(tableId === 'outcomesList' ? 'outcomesTableBody' : 'expressionsTableBody');
    if (!tableBody) return false;

    // Check if already in table
    const existingRow = Array.from(tableBody.children).find(row => 
        row.querySelector('.var-name').textContent === columnName
    );
    if (existingRow) return false;

    const row = document.createElement('tr');
    row.className = 'selected-var-row';
    
    row.innerHTML = `
        <td>
            <span class="var-name">${columnName}</span>
            <button class="action-button remove-var" title="Remove">×</button>
        </td>
        <td>
            <select class="transform-select">
                <option value="none">None</option>
                <option value="log">Log</option>
                <option value="sqrt">Square Root</option>
                <option value="zscore">Z-Score</option>
                <option value="center">Center</option>
                <option value="scale">Scale</option>
            </select>
        </td>
        <td>
            <select class="paired-select">
                <option value="none">None</option>
                ${tableBody.querySelectorAll('tr').length > 0 ? 
                    Array.from(tableBody.querySelectorAll('tr')).map(r => 
                        `<option value="${r.querySelector('.var-name').textContent}">
                            ${r.querySelector('.var-name').textContent}
                        </option>`
                    ).join('') 
                    : ''
                }
            </select>
        </td>
        <td>
            <div class="timeseries-controls">
                <label class="switch">
                    <input type="checkbox" class="timeseries-toggle">
                    <span class="slider round"></span>
                </label>
                <select class="timeseries-type" disabled>
                    <option value="trend">Trend</option>
                    <option value="seasonal">Seasonal</option>
                    <option value="cyclic">Cyclic</option>
                </select>
            </div>
        </td>
    `;

    // Add event listeners
    const timeseriesToggle = row.querySelector('.timeseries-toggle');
    const timeseriesType = row.querySelector('.timeseries-type');
    
    timeseriesToggle.addEventListener('change', function() {
        timeseriesType.disabled = !this.checked;
    });

    row.querySelector('.remove-var').addEventListener('click', () => {
        // Remove from the outcomes/expressions table
        row.remove();
        
        // Update paired options for all remaining rows
        updatePairedOptions(tableBody);
        
        // Restore the row to the main table
        const mainTableBody = document.getElementById('columnStatsTableBody');
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-type', columnType);
        newRow.innerHTML = `
            <td class="select-column">
                <input type="checkbox" class="column-checkbox" data-column="${columnName}">
            </td>
            <td>${columnName}</td>
            <td>
                <span class="column-type ${columnType}">${columnType}</span>
            </td>
            <td></td>
            <td>${getColumnRange(columnName, columnType, window.currentStats)}</td>
            <td class="data-preview-cell">
                ${getDistributionInfo(columnName, columnType, window.currentStats)}
            </td>
            <td>
                <button class="action-button preview-btn" data-column="${columnName}" data-type="${columnType}">Preview</button>
            </td>
        `;
        
        mainTableBody.appendChild(newRow);
        
        // Reinitialize event listeners for the new row
        initializeEditButtons();
        newRow.querySelector('.preview-btn').addEventListener('click', function() {
            showColumnPreview(columnName, columnType);
        });
    });

    tableBody.appendChild(row);
    
    // Update paired options for all rows
    updatePairedOptions(tableBody);
    
    return true;
}

// Function to update paired options for all rows in a table
function updatePairedOptions(tableBody) {
    // Get counts from both tables
    const outcomesCount = document.getElementById('outcomesTableBody').querySelectorAll('tr').length;
    const expressionsCount = document.getElementById('expressionsTableBody').querySelectorAll('tr').length;
    
    const rows = tableBody.querySelectorAll('tr');
    rows.forEach(row => {
        const pairedSelect = row.querySelector('.paired-select');
        const currentValue = pairedSelect.value;
        const currentName = row.querySelector('.var-name').textContent;
        const isOutcome = row.closest('#outcomesTableBody') !== null;
        
        // Clear existing options
        pairedSelect.innerHTML = '<option value="none">------</option>';
        
        // Case 1: Single outcome, no expressions
        if (outcomesCount === 1 && expressionsCount === 0) {
            pairedSelect.disabled = true;
            return;
        }
        
        // Case 2: Single outcome, single expression
        if (outcomesCount === 1 && expressionsCount === 1) {
            // If this is the outcome row
            if (isOutcome) {
                // Add the expression as an option
                const expressionName = document.getElementById('expressionsTableBody')
                    .querySelector('.var-name').textContent;
                pairedSelect.innerHTML += `
                    <option value="${expressionName}" ${currentValue === expressionName ? 'selected' : ''}>
                        ${expressionName}
                    </option>
                `;
            } else {
                // Add the outcome as an option
                const outcomeName = document.getElementById('outcomesTableBody')
                    .querySelector('.var-name').textContent;
                pairedSelect.innerHTML += `
                    <option value="${outcomeName}" ${currentValue === outcomeName ? 'selected' : ''}>
                        ${outcomeName}
                    </option>
                `;
            }
            pairedSelect.disabled = false;
            return;
        }
        
        // For all other cases, enable the select and add appropriate options
        pairedSelect.disabled = false;
        
        // If this is an outcome row, add all expressions as options
        if (isOutcome) {
            document.getElementById('expressionsTableBody').querySelectorAll('tr').forEach(expressionRow => {
                const expressionName = expressionRow.querySelector('.var-name').textContent;
                pairedSelect.innerHTML += `
                    <option value="${expressionName}" ${currentValue === expressionName ? 'selected' : ''}>
                        ${expressionName}
                    </option>
                `;
            });
        } else {
            // If this is an expression row, add all outcomes as options
            document.getElementById('outcomesTableBody').querySelectorAll('tr').forEach(outcomeRow => {
                const outcomeName = outcomeRow.querySelector('.var-name').textContent;
                pairedSelect.innerHTML += `
                    <option value="${outcomeName}" ${currentValue === outcomeName ? 'selected' : ''}>
                        ${outcomeName}
                    </option>
                `;
            });
        }
    });
}

// Update the styles
const styleSheet = document.createElement("style");
styleSheet.textContent += `
    .variables-table select {
        width: 100%;
        padding: 4px 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 0.9em;
    }

    .variables-table select:disabled {
        background-color: #f5f5f5;
        cursor: not-allowed;
    }

    .timeseries-controls {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Switch styling */
    .switch {
        position: relative;
        display: inline-block;
        width: 40px;
        height: 20px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 2px;
        bottom: 2px;
        background-color: white;
        transition: .4s;
    }

    input:checked + .slider {
        background-color: #2196F3;
    }

    input:checked + .slider:before {
        transform: translateX(20px);
    }

    .slider.round {
        border-radius: 20px;
    }

    .slider.round:before {
        border-radius: 50%;
    }

    .variables-table .remove-var {
        float: right;
        padding: 0 4px;
        color: #f44336;
        font-size: 1.2em;
        background: transparent;
        border: none;
        cursor: pointer;
        opacity: 0.6;
    }

    .variables-table .remove-var:hover {
        opacity: 1;
    }

    .variables-table td {
        vertical-align: middle;
    }
`;
document.head.appendChild(styleSheet);

// Add this function at the end of the file
function adjustDescriptiveStatsSection() {
    const descriptiveStatsSection = document.getElementById('descriptiveStatsSection');
    const previewHeader = descriptiveStatsSection.querySelector('.preview-header');
    
    // Scroll the preview header to the top with smooth animation
    previewHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Calculate available height more precisely
    const windowHeight = window.innerHeight;
    const headerHeight = previewHeader.offsetHeight;
    
    // Set the height of the content area
    const previewContent = descriptiveStatsSection.querySelector('.preview-content');
    if (previewContent) {
        // Add some padding at the bottom (e.g., 20px)
        const bottomPadding = 20;
        const contentHeight = windowHeight - headerHeight - bottomPadding;
        
        // Apply styles to make the content area scrollable and full-height
        previewContent.style.height = `${contentHeight}px`;
        previewContent.style.overflowY = 'auto';
        
        // Add styles to ensure proper layout
        const styleSheet = document.createElement("style");
        styleSheet.textContent = `
            .preview-content {
                display: flex;
                flex-direction: column;
            }
            
            .stats-dashboard {
                flex: 1;
                min-height: 0; /* Important for nested flex scrolling */
            }
            
            .column-stats-table-container {
                flex: 1;
                overflow: auto;
            }
            
            .chosen-outcomes-expressions-panel {
                margin-top: 2px;
            }
        `;
        document.head.appendChild(styleSheet);
    }
}

// Modify the proceed button handler to include the new function
// Find the existing proceedButton click handler and add the adjustDescriptiveStatsSection call
// in both the success and non-deletion paths

document.getElementById('proceedButton').addEventListener('click', function() {
    const validationElement = document.querySelector('.delete-column-validation');
    const deleteColumnRequest = document.getElementById('deleteColumnText').value;
    
    // Hide the preview actions section immediately when proceed button is clicked
    document.querySelector('.preview-actions').style.display = 'none';
    
    if (deleteColumnRequest.trim()) {
        // ... existing deletion code ...
        
        fetch('/api/delete-columns-at-start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                columns: columnsToDelete
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // ... existing success code ...
                
                // Show analysis sections
                document.getElementById('descriptiveStatsSection').style.display = 'block';
                document.getElementById('analysisTabsSection').style.display = 'block';
                
                // Initialize collapsible functionality for descriptive stats
                initializeDescriptiveStatsCollapsible();
                
                // Reinitialize the preview collapsible functionality
                initializeCollapsiblePreview();
                
                // Initialize tabs
                initializeTabs();
                
                // Load descriptive stats
                loadDescriptiveStats();
                
                // Load smart recommendations
                loadSmartRecommendations();
                
                // Add this line to adjust the section after everything is initialized
                setTimeout(adjustDescriptiveStatsSection, 100); // Small delay to ensure content is rendered
            } else {
                // ... existing error handling ...
            }
        })
        .catch(error => {
            // ... existing error handling ...
        });
    } else {
        // If no columns specified, proceed without deletions
        document.getElementById('descriptiveStatsSection').style.display = 'block';
        document.getElementById('analysisTabsSection').style.display = 'block';
        initializeDescriptiveStatsCollapsible();
        initializeCollapsiblePreview();
        initializeTabs();
        loadDescriptiveStats();
        loadSmartRecommendations();
        
        // Add this line to adjust the section after everything is initialized
        setTimeout(adjustDescriptiveStatsSection, 100); // Small delay to ensure content is rendered
    }
});

// Add window resize handler to maintain proper height when window is resized
window.addEventListener('resize', function() {
    if (document.getElementById('descriptiveStatsSection').style.display === 'block') {
        adjustDescriptiveStatsSection();
    }
});

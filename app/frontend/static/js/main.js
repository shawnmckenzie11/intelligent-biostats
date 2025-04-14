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
    
    // Hide overlay panel initially
    overlay.style.display = 'none';

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
            const csvText = e.target.result;
            displayPreview(csvText);
            
            // Upload the full file without triggering analysis
            uploadFullFile(file)
                .catch(error => {
                    console.error('Error uploading file:', error);
                    alert('Error uploading file');
                });
        };
        reader.readAsText(file);
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
        
        // Show the overlay panel when data is loaded
        const overlay = document.querySelector('.analysis-overlay');
        overlay.style.display = 'block';
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
                        
                        // Hide the preview actions section
                        document.querySelector('.preview-actions').style.display = 'none';
                        
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
        const statsContainer = document.getElementById('descriptiveContent');
        if (!statsContainer) {
            console.error('Stats display container not found');
            return;
        }

        // Clear previous content
        statsContainer.innerHTML = '';

        // Create overall layout structure - now horizontal
        const layoutHtml = `
            <div class="stats-dashboard horizontal">
                <div class="file-stats-panel" title="File Statistics">
                    <div class="file-stats-content"></div>
                </div>
                <div class="column-stats-panel" title="Column Statistics">
                    <div class="search-container">
                        <input type="text" id="columnSearchInput" placeholder="Search columns..." class="column-search">
                    </div>
                    <div class="column-stats-table-container">
                        <table class="column-stats-table">
                            <thead>
                                <tr>
                                    <th>Column Name</th>
                                    <th>Type</th>
                                    <th>Missing Values</th>
                                    <th>Data Preview</th>
                                    <th>Actions</th>
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

        // Populate file statistics
        const fileStatsContent = statsContainer.querySelector('.file-stats-content');
        if (stats.file_stats) {
            const fileStats = stats.file_stats;
            fileStatsContent.innerHTML = `
                <div class="file-stats-grid compact">
                    <div class="stat-card">
                        <div class="stat-value">${fileStats.rows.toLocaleString()}</div>
                        <div class="stat-label">Rows</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${fileStats.columns.toLocaleString()}</div>
                        <div class="stat-label">Columns</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${fileStats.memory_usage}</div>
                        <div class="stat-label">Memory Usage</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${fileStats.missing_values.toLocaleString()}</div>
                        <div class="stat-label">Missing Values</div>
                    </div>
                </div>
                <div class="column-type-summary compact">
                    <div class="column-type-grid">
                        <div class="type-card">
                            <div class="type-count">${stats.column_types.numeric || 0}</div>
                            <div class="type-label">Numeric</div>
                        </div>
                        <div class="type-card">
                            <div class="type-count">${stats.column_types.categorical || 0}</div>
                            <div class="type-label">Categorical</div>
                        </div>
                        <div class="type-card">
                            <div class="type-count">${stats.column_types.boolean || 0}</div>
                            <div class="type-label">Boolean</div>
                        </div>
                        <div class="type-card">
                            <div class="type-count">${stats.column_types.datetime || 0}</div>
                            <div class="type-label">DateTime</div>
                        </div>
                    </div>
                </div>
            `;
        }

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
                if (columnType === 'numeric' && stats.outlier_info && stats.outlier_info[column]) {
                    hasOutliers = stats.outlier_info[column].count > 0;
                }
                
                // Create the row
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${column}</td>
                    <td>
                        <span class="column-type ${columnType}">${columnType}</span>
                        ${hasOutliers ? '<span class="outlier-indicator" title="Contains outliers">⚠️</span>' : ''}
                    </td>
                    <td>${missingCount} (${((missingCount / stats.file_stats.rows) * 100).toFixed(1)}%)</td>
                    <td class="data-preview-cell">
                        ${getDataPreviewForColumn(column, columnType, stats)}
                    </td>
                    <td class="action-buttons">
                        <button class="analyze-btn" data-column="${column}">Analyze</button>
                        <button class="visualize-btn" data-column="${column}">Visualize</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
            
            // Add event listeners to the action buttons
            document.querySelectorAll('.analyze-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const column = this.getAttribute('data-column');
                    console.log(`Analyze clicked for column: ${column}`);
                    // Here you would call a function to open the analysis panel for this column
                    // e.g. openAnalysisFor(column);
                });
            });
            
            document.querySelectorAll('.visualize-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const column = this.getAttribute('data-column');
                    console.log(`Visualize clicked for column: ${column}`);
                    // Here you would call a function to visualize this column
                    // e.g. visualizeColumn(column);
                });
            });
            
            // Add search functionality
            const searchInput = document.getElementById('columnSearchInput');
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                document.querySelectorAll('#columnStatsTableBody tr').forEach(row => {
                    const columnName = row.querySelector('td').textContent.toLowerCase();
                    if (columnName.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        }
    }
    
    function getDataPreviewForColumn(column, columnType, stats) {
        // Generate an appropriate data preview based on column type
        switch (columnType) {
            case 'numeric':
                if (stats.distribution_analysis && stats.distribution_analysis[column]) {
                    const analysis = stats.distribution_analysis[column];
                    return `
                        <div class="sparkline-container">
                            <div class="numeric-preview">
                                <span title="Skewness">S: ${analysis.skewness.toFixed(2)}</span>
                                <span title="Kurtosis">K: ${analysis.kurtosis.toFixed(2)}</span>
                </div>
                </div>
            `;
                }
                return '<div class="numeric-preview">No data available</div>';
                
            case 'categorical':
                if (stats.categorical_stats && stats.categorical_stats[column]) {
                    const catStats = stats.categorical_stats[column];
                    return `
                        <div class="categorical-preview">
                            <span>${catStats.unique_count} unique values</span>
                            <span>Most frequent: ${catStats.most_frequent.value}</span>
                        </div>
                    `;
                }
                return '<div class="categorical-preview">No data available</div>';
                
            case 'boolean':
                if (stats.boolean_stats && stats.boolean_stats[column]) {
                    const boolStats = stats.boolean_stats[column];
                    return `
                        <div class="boolean-preview">
                            <span>True: ${boolStats.true_count} (${boolStats.true_percentage.toFixed(1)}%)</span>
                        </div>
                    `;
                }
                return '<div class="boolean-preview">No data available</div>';
                
            case 'timeseries':
                if (stats.datetime_stats && stats.datetime_stats[column]) {
                    const dateStats = stats.datetime_stats[column];
                    return `
                        <div class="datetime-preview">
                            <span>${dateStats.time_interval}</span>
            </div>
        `;
                }
                return '<div class="datetime-preview">No data available</div>';
                
            default:
                return '<div class="data-preview">No preview available</div>';
        }
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
});

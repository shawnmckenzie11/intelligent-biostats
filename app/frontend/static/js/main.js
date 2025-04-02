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
        document.getElementById('descriptiveStatsSection').style.display = 'none'; // Hide initially
        modifySection.style.display = 'block';

        // Initialize collapsible functionality
        initializeCollapsiblePreview();
        initializeDescriptiveSection();
    }

    function initializeCollapsiblePreview() {
        const toggleButton = document.getElementById('togglePreview');
        const previewHeader = toggleButton.parentElement;
        const previewContent = document.getElementById('previewContent');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        // Set initial state (expanded)
        previewContent.style.maxHeight = '500px';
        
        // Add click handler to the entire header
        previewHeader.addEventListener('click', (e) => {
            // Prevent double-triggering if clicking the toggle button
            if (e.target === toggleButton || e.target === toggleIcon) {
                return;
            }
            
            const isCollapsed = previewContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                previewContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                previewContent.style.maxHeight = '500px';
            } else {
                // Collapse
                previewContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                previewContent.style.maxHeight = '0';
            }
        });
        
        // Keep the toggle button click handler
        toggleButton.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent header click from triggering
            const isCollapsed = previewContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                previewContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                previewContent.style.maxHeight = '500px';
            } else {
                // Collapse
                previewContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                previewContent.style.maxHeight = '0';
            }
        });
    }

    function initializeDescriptiveSection() {
        const toggleButton = document.getElementById('toggleDescriptive');
        const descriptiveHeader = toggleButton.parentElement;
        const descriptiveContent = document.getElementById('descriptiveContent');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        // Set initial state (collapsed)
        descriptiveContent.classList.add('collapsed');
        toggleIcon.style.transform = 'rotate(-90deg)';
        
        // Create a ResizeObserver to handle dynamic content changes
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                if (!descriptiveContent.classList.contains('collapsed')) {
                    // Get the total height of all content
                    const totalHeight = Array.from(descriptiveContent.children)
                        .reduce((height, child) => height + child.offsetHeight, 0);
                    descriptiveContent.style.maxHeight = `${totalHeight + 50}px`; // Add padding
                }
            }
        });

        // Start observing the content and its children
        resizeObserver.observe(descriptiveContent);
        descriptiveContent.childNodes.forEach(child => {
            if (child.nodeType === 1) { // Only observe element nodes
                resizeObserver.observe(child);
            }
        });
        
        // Add click handler to the entire header
        descriptiveHeader.addEventListener('click', (e) => {
            // Prevent double-triggering if clicking the toggle button
            if (e.target === toggleButton || e.target === toggleIcon) {
                return;
            }
            
            const isCollapsed = descriptiveContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                descriptiveContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                // Calculate and set the height needed for all content
                const totalHeight = Array.from(descriptiveContent.children)
                    .reduce((height, child) => height + child.offsetHeight, 0);
                descriptiveContent.style.maxHeight = `${totalHeight + 50}px`;
            } else {
                // Collapse
                descriptiveContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                descriptiveContent.style.maxHeight = '0';
            }
        });
        
        // Keep the toggle button click handler
        toggleButton.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent header click from triggering
            const isCollapsed = descriptiveContent.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                descriptiveContent.classList.remove('collapsed');
                toggleIcon.style.transform = 'rotate(0deg)';
                // Calculate and set the height needed for all content
                const totalHeight = Array.from(descriptiveContent.children)
                    .reduce((height, child) => height + child.offsetHeight, 0);
                descriptiveContent.style.maxHeight = `${totalHeight + 50}px`;
            } else {
                // Collapse
                descriptiveContent.classList.add('collapsed');
                toggleIcon.style.transform = 'rotate(-90deg)';
                descriptiveContent.style.maxHeight = '0';
            }
        });
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
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Add active class to corresponding pane
                const tabName = button.getAttribute('data-tab');
                const targetPane = document.getElementById(`${tabName}Tab`);
                if (targetPane) {
                    targetPane.classList.add('active');
                }

                // Load appropriate data based on tab
                if (tabName === 'analyses') {
                    getAnalysisOptions();
                } else if (tabName === 'recommendations') {
                    loadSmartRecommendations();
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

    // Modify the existing proceed button handler
    document.getElementById('proceedButton').addEventListener('click', function() {
        const modificationRequest = document.getElementById('modificationInput').value;
        
        if (modificationRequest.trim()) {
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
                
                if (data.success) {
                    // Update preview table with new data
                    if (data.preview) {
                    updatePreviewTable(data.preview);
                }
                
                    // Update status message
                    const statusElement = document.getElementById('modificationStatus');
                    statusElement.textContent = 'Modifications Applied Successfully';
                    statusElement.className = 'status-message success';
                    
                    // Hide modify section and show analysis tabs after a delay
                    setTimeout(() => {
                        document.getElementById('modifySection').style.display = 'none';
                        document.getElementById('descriptiveStatsSection').style.display = 'block'; // Show descriptive stats section
                        showAnalysisTabs(); // Show tabs and initialize
                        getAnalysisOptions(); // Refresh analysis options
                        loadDescriptiveStats(); // Load descriptive stats into collapsible section
                        loadSmartRecommendations(); // Load smart recommendations
                    }, 1500);
                } else {
                    throw new Error(data.error || 'Failed to apply modifications');
                }
            })
            .catch(error => {
                console.error('Modification error:', error);
                const statusElement = document.getElementById('modificationStatus');
                statusElement.textContent = 'Error: ' + error.message;
                statusElement.className = 'status-message error';
            });
        } else {
            // If no modifications, directly show analysis tabs
            document.getElementById('modifySection').style.display = 'none';
            document.getElementById('descriptiveStatsSection').style.display = 'block'; // Show descriptive stats section
            showAnalysisTabs(); // Show tabs and initialize
            getAnalysisOptions();
            loadDescriptiveStats(); // Load descriptive stats into collapsible section
            loadSmartRecommendations(); // Load smart recommendations
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

    function loadDescriptiveStats() {
        fetch('/api/descriptive-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayDescriptiveStats(data.stats);
                    initializeColumnPicker(data.stats.column_types.columns);
                } else {
                    throw new Error(data.error || 'Failed to load statistics');
                }
            })
            .catch(error => {
                console.error('Error loading descriptive stats:', error);
                document.querySelector('.stats-summary').innerHTML = 
                    `<div class="error-message">Error loading statistics: ${error.message}</div>`;
            });
    }

    function displayDescriptiveStats(stats) {
        const summaryHtml = `
            <div class="stats-card">
                <h4>File Statistics</h4>
                <p>Rows: ${stats.file_stats.rows} | Columns: ${stats.file_stats.columns}</p>
                <p>Memory: ${stats.file_stats.memory_usage}</p>
            </div>
            <div class="stats-card">
                <h4>Column Types</h4>
                <p>Numeric: ${stats.column_types.numeric} | Categorical: ${stats.column_types.categorical}</p>
                <p>Boolean: ${stats.column_types.boolean} | DateTime: ${stats.column_types.datetime}</p>
            </div>
        `;
        
        // Update the descriptive statistics collapsible section instead of the tab
        const descriptiveContent = document.getElementById('descriptiveContent');
        descriptiveContent.innerHTML = `
            <div class="stats-summary">${summaryHtml}</div>
            <div class="column-picker">
                <h4>Column Analysis</h4>
                <select id="columnSelect" class="column-select">
                    <option value="">Select a column...</option>
                    ${stats.column_types.columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                </select>
                <div class="column-stats">
                    <div id="columnStats"></div>
                    <div id="columnData"></div>
                </div>
            </div>
        `;

        // Initialize column picker event listener
        const select = document.getElementById('columnSelect');
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                fetchColumnData(e.target.value);
            } else {
                document.getElementById('columnStats').innerHTML = '';
                document.getElementById('columnData').innerHTML = '';
            }
        });
    }

    function initializeColumnPicker(columns) {
        const select = document.getElementById('columnSelect');
        select.innerHTML = '<option value="">Select a column...</option>' +
            columns.map(col => `<option value="${col}">${col}</option>`).join('');
            
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                fetchColumnData(e.target.value);
            } else {
                document.getElementById('columnStats').innerHTML = '';
                document.getElementById('columnData').innerHTML = '';
            }
        });
    }

    function fetchColumnData(columnName) {
        fetch(`/api/column-data/${encodeURIComponent(columnName)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    displayColumnData(data.column_data);
                } else {
                    throw new Error(data.error || 'Failed to load column data');
                }
            })
            .catch(error => {
                console.error('Error loading column data:', error);
                const statsContainer = document.getElementById('columnStats');
                const dataContainer = document.getElementById('columnData');
                
                statsContainer.innerHTML = `
                    <div class="error-message">
                        Error loading column data: ${error.message}
                        <br>
                        Please try refreshing the page or selecting a different column.
                    </div>
                `;
                dataContainer.innerHTML = '';
            });
    }

    function displayColumnData(columnData) {
        const statsContainer = document.getElementById('columnStats');
        const dataContainer = document.getElementById('columnData');
        
        // Clear previous content
        statsContainer.innerHTML = '';
        dataContainer.innerHTML = '';
        
        // Display statistics in a side-by-side layout
        let statsHtml = `
            <div class="stats-card">
                <h4>Basic Info</h4>
                <p><strong>Type:</strong> ${columnData.stats.Type}</p>
                <p><strong>Missing:</strong> ${columnData.stats['Missing Values']}</p>
                <p><strong>Unique:</strong> ${columnData.stats['Unique Values']}</p>
            </div>
        `;

        // Add type-specific statistics
        if (columnData.stats.Type === 'numeric' || columnData.stats.Type === 'discrete') {
            statsHtml += `
                <div class="stats-card">
                    <h4>Numeric Stats</h4>
                    <p><strong>Mean:</strong> ${columnData.stats.Mean}</p>
                    <p><strong>Median:</strong> ${columnData.stats.Median}</p>
                    <p><strong>Std Dev:</strong> ${columnData.stats['Std Dev']}</p>
                </div>
                <div class="stats-card">
                    <h4>Range</h4>
                    <p><strong>Min:</strong> ${columnData.stats.Min}</p>
                    <p><strong>Max:</strong> ${columnData.stats.Max}</p>
                </div>
            `;
        } else if (columnData.stats.Type === 'categorical') {
            statsHtml += `
                <div class="stats-card">
                    <h4>Distribution</h4>
                    <p><strong>Most Common:</strong> ${columnData.stats['Most Common']}</p>
                    <div class="value-distribution">
                        <strong>Top Values:</strong>
                        <ul>
                            ${Object.entries(columnData.stats['Value Distribution']).map(([val, count]) => 
                                `<li>${val}: ${count}</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } else if (columnData.stats.Type === 'boolean') {
            statsHtml += `
                <div class="stats-card">
                    <h4>Counts</h4>
                    <p><strong>True:</strong> ${columnData.stats['True Count']}</p>
                    <p><strong>False:</strong> ${columnData.stats['False Count']}</p>
                </div>
            `;
        } else if (columnData.stats.Type === 'timeseries') {
            statsHtml += `
                <div class="stats-card">
                    <h4>Time Range</h4>
                    <p><strong>Start:</strong> ${columnData.stats['Start Date']}</p>
                    <p><strong>End:</strong> ${columnData.stats['End Date']}</p>
                    <p><strong>Range:</strong> ${columnData.stats['Date Range']}</p>
                </div>
            `;
        }

        statsContainer.innerHTML = statsHtml;
        
        // Display plots in a 2x2 grid
        let plotsHtml = '<div class="plots-container">';
        Object.entries(columnData.plots).forEach(([plotType, plotData]) => {
            let plotTitle = '';
            switch(plotType) {
                case 'histogram':
                    plotTitle = 'Distribution';
                    break;
                case 'density':
                    plotTitle = 'Density Plot';
                    break;
                case 'boxplot':
                    plotTitle = 'Box Plot';
                    break;
                case 'qqplot':
                    plotTitle = 'Q-Q Plot';
                    break;
                case 'barplot':
                    plotTitle = 'Value Distribution';
                    break;
                case 'pie':
                    plotTitle = 'Distribution';
                    break;
                case 'dotplot':
                    plotTitle = 'Dot Plot';
                    break;
            }
            
            plotsHtml += `
                <div class="plot-card">
                    <h4>${plotTitle}</h4>
                    <div class="plot-container">
                        <img src="data:image/png;base64,${plotData}" alt="${plotTitle}" />
                    </div>
                </div>
            `;
        });
        plotsHtml += '</div>';
        
        dataContainer.innerHTML = plotsHtml;

        // Update the descriptive content height if it's expanded
        const descriptiveContent = document.getElementById('descriptiveContent');
        if (!descriptiveContent.classList.contains('collapsed')) {
            // Calculate and set the height needed for all content
            const totalHeight = Array.from(descriptiveContent.children)
                .reduce((height, child) => height + child.offsetHeight, 0);
            descriptiveContent.style.maxHeight = `${totalHeight + 50}px`;
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
});

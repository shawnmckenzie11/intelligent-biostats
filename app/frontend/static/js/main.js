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
                } else if (tabName === 'descriptive') {
                    loadDescriptiveStats();
                }
            });
        });
    }

    // Initialize tabs when document loads AND when analysis section is shown
    function showAnalysisTabs() {
        const analysisTabsSection = document.getElementById('analysisTabsSection');
        if (analysisTabsSection) {
            analysisTabsSection.style.display = 'block';
            initializeTabs(); // Reinitialize tabs when showing the section
            loadDescriptiveStats(); // Load initial stats since descriptive is the default tab
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
                        showAnalysisTabs(); // Show tabs and initialize
                        getAnalysisOptions(); // Refresh analysis options
                        loadDescriptiveStats(); // Refresh descriptive stats
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
            showAnalysisTabs(); // Show tabs and initialize
            getAnalysisOptions();
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

    // Enhanced search functionality for analysis options
    function initializeAnalysisSearch() {
        const searchInput = document.getElementById('analysisSearch');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                const searchTerm = this.value.toLowerCase().trim();
                const options = document.querySelectorAll('.analysis-option');
                let matchCount = 0;
                
                options.forEach(option => {
                    const name = option.querySelector('h3').textContent.toLowerCase();
                    const description = option.querySelector('.description').textContent.toLowerCase();
                    const requirements = option.querySelector('.requirements').textContent.toLowerCase();
                    
                    // Check if search term matches any part of the analysis option
                    const isMatch = name.includes(searchTerm) || 
                                  description.includes(searchTerm) || 
                                  requirements.includes(searchTerm);
                    
                    // Smooth transition for showing/hiding options
                    if (isMatch) {
                        option.style.display = '';
                        option.style.opacity = '1';
                        matchCount++;
                    } else {
                        option.style.opacity = '0';
                        setTimeout(() => {
                            option.style.display = 'none';
                        }, 200); // Match this with CSS transition duration
                    }
                });

                // Show message if no matches found
                const noResultsMsg = document.getElementById('noAnalysisResults');
                if (!noResultsMsg) {
                    const msg = document.createElement('div');
                    msg.id = 'noAnalysisResults';
                    msg.className = 'no-results-message';
                    document.getElementById('analysisOptions').appendChild(msg);
                }
                noResultsMsg.textContent = matchCount === 0 ? 'No matching analyses found' : '';
                noResultsMsg.style.display = matchCount === 0 ? 'block' : 'none';
            }, 150)); // Debounce delay of 150ms
        }
    }

    // Debounce function to limit how often the search updates
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Update displayAnalysisOptions to include search initialization
    function displayAnalysisOptions(options) {
        const analysisOptions = document.getElementById('analysisOptions');
        if (!analysisOptions) return;

        let optionsHtml = '';
        options.forEach(option => {
            optionsHtml += `
                <div class="analysis-option">
                    <h3>${option.name}</h3>
                    <div class="description">${option.description}</div>
                    <button class="proceed-button" 
                        ${!option.requirements_met ? 'disabled' : ''}
                        onclick="runAnalysis('${option.id}')">
                        Run Analysis
                    </button>
                    <div class="requirements">
                        Requirements: ${option.requirements}
                        <span class="requirements-status ${option.requirements_met ? 'requirements-met' : 'requirements-not-met'}">
                            (${option.requirements_met ? '✓ Met' : '✗ Not Met'})
                        </span>
                    </div>
                </div>
            `;
        });
        analysisOptions.innerHTML = optionsHtml;
        
        // Initialize search after options are displayed
        initializeAnalysisSearch();
    }

    // Function to run analysis (placeholder for now)
    function runAnalysis(analysisId) {
        console.log(`Running analysis: ${analysisId}`);
        // Implementation to be added later
    }

    // Add search functionality for analysis options
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('analysisSearch');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const options = document.querySelectorAll('.analysis-option');
                
                options.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    option.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    });

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
        
        document.querySelector('.stats-summary').innerHTML = summaryHtml;
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
        
        // Display critical issues first
        if (recommendations.critical_issues.length > 0) {
            html += `
                <div class="recommendations-section critical">
                    <h4>Critical Issues</h4>
                    <p class="section-description">These issues must be addressed before proceeding with analysis.</p>
                    ${recommendations.critical_issues.map(issue => `
                        <div class="recommendation-card critical">
                            <h5>${issue.message}</h5>
                            ${issue.details ? `
                                <div class="details">
                                    ${Object.entries(issue.details).map(([key, value]) => `
                                        <p><strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> 
                                        ${typeof value === 'object' ? JSON.stringify(value) : value}</p>
                                    `).join('')}
                                </div>
                            ` : ''}
                            <div class="recommendations-list">
                                <p class="suggested-tests">Suggested approaches: ${issue.suggested_tests.join(', ')}</p>
                                ${issue.references ? `
                                    <p class="references">References: ${issue.references.join(', ')}</p>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Display high priority recommendations
        if (recommendations.high_priority.length > 0) {
            html += `
                <div class="recommendations-section high-priority">
                    <h4>High Priority Recommendations</h4>
                    <p class="section-description">Important considerations that may affect your analysis.</p>
                    ${recommendations.high_priority.map(rec => `
                        <div class="recommendation-card high-priority">
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
                    `).join('')}
                </div>
            `;
        }
        
        // Display suggested analyses
        if (recommendations.suggested_analyses.length > 0) {
            html += `
                <div class="recommendations-section suggested">
                    <h4>Suggested Analyses</h4>
                    <p class="section-description">Recommended statistical approaches based on your data structure.</p>
                    ${recommendations.suggested_analyses.map(analysis => `
                        <div class="recommendation-card suggested">
                            <h5>${analysis.message}</h5>
                            ${analysis.details ? `
                                <div class="details">
                                    ${Object.entries(analysis.details).map(([key, value]) => `
                                        <p><strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> 
                                        ${typeof value === 'object' ? JSON.stringify(value) : value}</p>
                                    `).join('')}
                                </div>
                            ` : ''}
                            <div class="recommendations-list">
                                <p class="suggested-tests">Suggested tests: ${analysis.suggested_tests.join(', ')}</p>
                                ${analysis.references ? `
                                    <p class="references">References: ${analysis.references.join(', ')}</p>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Display data quality considerations
        if (recommendations.data_quality.length > 0) {
            html += `
                <div class="recommendations-section quality">
                    <h4>Data Quality Considerations</h4>
                    <p class="section-description">Issues that may affect data quality and reliability.</p>
                    ${recommendations.data_quality.map(issue => `
                        <div class="recommendation-card quality">
                            <h5>${issue.message}</h5>
                            ${issue.details ? `
                                <div class="details">
                                    ${Object.entries(issue.details).map(([key, value]) => `
                                        <p><strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> 
                                        ${typeof value === 'object' ? JSON.stringify(value) : value}</p>
                                    `).join('')}
                                </div>
                            ` : ''}
                            <div class="recommendations-list">
                                <p class="suggested-tests">Suggested approaches: ${issue.suggested_tests.join(', ')}</p>
                                ${issue.references ? `
                                    <p class="references">References: ${issue.references.join(', ')}</p>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Display methodological notes
        if (recommendations.methodological_notes.length > 0) {
            html += `
                <div class="recommendations-section methodological">
                    <h4>Methodological Notes</h4>
                    <p class="section-description">General considerations for statistical analysis.</p>
                    ${recommendations.methodological_notes.map(note => `
                        <div class="recommendation-card methodological">
                            <h5>${note.message}</h5>
                            <div class="recommendations-list">
                                <p class="suggested-tests">Suggested approaches: ${note.suggested_tests.join(', ')}</p>
                                ${note.references ? `
                                    <p class="references">References: ${note.references.join(', ')}</p>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
});

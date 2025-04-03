class RecommendationsManager {
    constructor() {
        this.overlayContent = document.querySelector('.overlay-content');
        this.recommendations = [];
        this.analysisHistory = [];
        this.currentAnalysis = null;
        // API key should be loaded from environment variables or server-side
        this.openaiApiKey = null;
    }

    // Initialize the recommendations system
    init() {
        this.clearOverlay();
        this.setupEventListeners();
    }

    // Clear the overlay content
    clearOverlay() {
        this.overlayContent.innerHTML = '';
    }

    // Setup event listeners for various actions
    setupEventListeners() {
        // Listen for file upload
        document.addEventListener('fileUploaded', () => {
            this.updateRecommendations();
        });

        // Listen for analysis history updates
        document.addEventListener('analysisHistoryUpdated', (e) => {
            this.analysisHistory = e.detail.history;
            this.updateRecommendations();
        });

        // Listen for current analysis changes
        document.addEventListener('analysisSelected', (e) => {
            this.currentAnalysis = e.detail.analysis;
            this.updateRecommendations();
        });

        // Listen for data modifications
        document.addEventListener('dataModified', (e) => {
            this.updateRecommendations();
        });
    }

    // Update recommendations based on current state
    async updateRecommendations() {
        this.clearOverlay();
        this.recommendations = [];

        // Add data-based recommendations
        await this.addDataBasedRecommendations();

        // Add analysis flow recommendations
        this.addAnalysisFlowRecommendations();

        // Display all recommendations
        this.displayRecommendations();
    }

    // Add recommendations based on current data state
    async addDataBasedRecommendations() {
        try {
            const response = await fetch('/api/descriptive-stats');
            if (!response.ok) {
                console.log('Data not yet available, skipping data-based recommendations');
                return;
            }
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                const columnTypes = stats.column_types;
                
                // Clear existing recommendations
                this.recommendations = [];
                
                // Check for categorical and boolean data
                const categoricalCols = columnTypes.columns.filter((col, index) => 
                    columnTypes.column_types_list[index] === 'categorical' || 
                    columnTypes.column_types_list[index] === 'boolean'
                );
                
                if (categoricalCols.length > 0) {
                    this.recommendations.push({
                        type: 'data-quality',
                        title: 'Categorical Data Detected',
                        message: `Your dataset contains ${categoricalCols.length} categorical variables. These are suitable for ANOVA, Chi-square tests, and other categorical analyses.`,
                        priority: 'high',
                        action: 'View Details',
                        details: {
                            columns: categoricalCols,
                            analysis_suggestions: ['ANOVA', 'Chi-square Test', 'Contingency Tables']
                        }
                    });
                }

                // Check for missing values using the pre-calculated data
                const missingValues = stats.file_stats.missing_values || 0;
                const missingValuesByColumn = stats.missing_values_by_column || {};
                
                if (missingValues > 0) {
                    const columnsWithMissing = Object.entries(missingValuesByColumn).map(([name, count]) => ({
                        name,
                        count
                    }));
                    
                    this.recommendations.push({
                        type: 'data-quality',
                        title: 'Missing Values Present',
                        message: `Your dataset contains ${missingValues} missing values. Consider handling these before analysis to avoid bias.`,
                        priority: 'high',
                        action: 'View Details',
                        details: {
                            total_missing: missingValues,
                            columns_with_missing: columnsWithMissing,
                            handling_suggestions: ['Imputation', 'Complete Case Analysis', 'Multiple Imputation']
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error fetching data-based recommendations:', error);
        }
    }

    // Add recommendations based on analysis flow
    addAnalysisFlowRecommendations() {
        if (this.analysisHistory.length > 0) {
            const lastAnalysis = this.analysisHistory[0];
            
            // Suggest complementary analyses
            this.recommendations.push({
                type: 'analysis-flow',
                title: 'Complementary Analysis',
                message: `Based on your recent ${lastAnalysis.type} analysis, consider running a complementary test.`,
                priority: 'medium',
                action: 'View complementary analyses'
            });
        }

        if (this.currentAnalysis) {
            // Suggest next steps based on current analysis
            this.recommendations.push({
                type: 'analysis-flow',
                title: 'Next Steps',
                message: `After completing this ${this.currentAnalysis.type} analysis, consider these follow-up tests.`,
                priority: 'medium',
                action: 'View next steps'
            });
        }
    }

    // Display all recommendations
    displayRecommendations() {
        // Sort recommendations by priority
        const priorityOrder = { 'high': 1, 'medium': 2, 'low': 3 };
        this.recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

        // Create recommendation cards
        this.recommendations.forEach(rec => {
            const card = this.createRecommendationCard(rec);
            this.overlayContent.appendChild(card);
        });
    }

    // Create a recommendation card
    createRecommendationCard(recommendation) {
        const card = document.createElement('div');
        card.className = `recommendation-card ${recommendation.type} ${recommendation.priority}`;
        
        let detailsHtml = '';
        if (recommendation.details) {
            if (recommendation.details.columns) {
                detailsHtml += `
                    <div class="details-section">
                        <h4>Affected Columns:</h4>
                        <ul>
                            ${recommendation.details.columns.map(col => `<li>${col}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            if (recommendation.details.columns_with_missing) {
                detailsHtml += `
                    <div class="details-section">
                        <h4>Columns with Missing Values:</h4>
                        <ul>
                            ${recommendation.details.columns_with_missing.map(col => 
                                `<li>${col.name}: ${col.count} missing values</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
            }
            if (recommendation.details.analysis_suggestions) {
                detailsHtml += `
                    <div class="details-section">
                        <h4>Suggested Analyses:</h4>
                        <ul>
                            ${recommendation.details.analysis_suggestions.map(analysis => 
                                `<li>${analysis}</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
            }
            if (recommendation.details.handling_suggestions) {
                detailsHtml += `
                    <div class="details-section">
                        <h4>Handling Suggestions:</h4>
                        <ul>
                            ${recommendation.details.handling_suggestions.map(suggestion => 
                                `<li>${suggestion}</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
            }
        }
        
        card.innerHTML = `
            <div class="card-header">
                <h3>${recommendation.title}</h3>
                <span class="priority-badge ${recommendation.priority}">${recommendation.priority}</span>
            </div>
            <div class="card-content">
                <p>${recommendation.message}</p>
                ${detailsHtml ? `
                    <div class="details" style="display: none;">
                        ${detailsHtml}
                    </div>
                ` : ''}
            </div>
            <div class="card-actions">
                <button class="action-button">${recommendation.action}</button>
            </div>
        `;
        
        // Add click handler for the action button
        const actionButton = card.querySelector('.action-button');
        const details = card.querySelector('.details');
        if (details) {
            actionButton.addEventListener('click', () => {
                details.style.display = details.style.display === 'none' ? 'block' : 'none';
                actionButton.textContent = details.style.display === 'none' ? recommendation.action : 'Hide Details';
            });
        }
        
        return card;
    }

    // Handle recommendation action
    handleRecommendationAction(recommendation) {
        // Dispatch custom event for the action
        const event = new CustomEvent('recommendationAction', {
            detail: {
                recommendation: recommendation,
                action: recommendation.action
            }
        });
        document.dispatchEvent(event);
    }
}

// Initialize the recommendations manager
const recommendationsManager = new RecommendationsManager();
document.addEventListener('DOMContentLoaded', () => {
    recommendationsManager.init();
}); 
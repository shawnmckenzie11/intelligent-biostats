class RecommendationsManager {
    constructor() {
        this.overlayContent = document.querySelector('.overlay-content');
        this.recommendations = [];
        this.analysisHistory = [];
        this.currentAnalysis = null;
        this.init();
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

                // Check for skewed data using the new createSkewedDataCard function
                const skewedCards = createSkewedDataCard(stats);
                if (skewedCards && skewedCards.length > 0) {
                    skewedCards.forEach(card => {
                        this.overlayContent.appendChild(card);
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
            if (recommendation.details.distribution_analysis) {
                detailsHtml += `
                    <div class="details-section">
                        <h4>Distribution Analysis:</h4>
                        <table class="details-table">
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th style="width: 20px;">S</th>
                                    <th style="width: 20px;">K</th>
                                    <th>Suggested Transformation</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.entries(recommendation.details.distribution_analysis).map(([col, analysis]) => `
                                    <tr>
                                        <td>${col}</td>
                                        <td style="text-align: right;">${analysis.skewness.toFixed(2)}</td>
                                        <td style="text-align: right;">${analysis.kurtosis.toFixed(2)}</td>
                                        <td>${analysis.transformation_suggestion}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
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

function createSkewedDataCard(stats) {
    if (!stats.distribution_analysis) return null;

    // Group columns by skewness type
    const skewGroups = {
        strongPositive: [],  // S > 1
        moderatePositive: [], // 0.5 < S <= 1
        strongNegative: [],  // S < -1
        moderateNegative: [], // -1 <= S < -0.5
        heavyTails: []      // K > 3.5
    };

    // Categorize columns based on skewness and kurtosis
    Object.entries(stats.distribution_analysis).forEach(([col, analysis]) => {
        const skewness = analysis.skewness;
        const kurtosis = analysis.kurtosis;

        // Prioritize severe skewness first
        if (skewness > 1) {
            skewGroups.strongPositive.push({ 
                col, 
                ...analysis,
                priority: 1,
                transformation_suggestion: "Log transformation (recommended for strong positive skew)"
            });
        } else if (skewness < -1) {
            skewGroups.strongNegative.push({ 
                col, 
                ...analysis,
                priority: 1,
                transformation_suggestion: "Square transformation (recommended for strong negative skew)"
            });
        } 
        // Then moderate skewness
        else if (skewness > 0.5 && skewness <= 1) {
            skewGroups.moderatePositive.push({ 
                col, 
                ...analysis,
                priority: 2,
                transformation_suggestion: "Square root transformation (recommended for moderate positive skew)"
            });
        } else if (skewness < -0.5 && skewness >= -1) {
            skewGroups.moderateNegative.push({ 
                col, 
                ...analysis,
                priority: 2,
                transformation_suggestion: "Square transformation (recommended for moderate negative skew)"
            });
        }
        
        // Finally, check for heavy tails if not already in a skewness group
        if (kurtosis > 3.5 && !skewGroups.strongPositive.some(item => item.col === col) && 
            !skewGroups.strongNegative.some(item => item.col === col) &&
            !skewGroups.moderatePositive.some(item => item.col === col) &&
            !skewGroups.moderateNegative.some(item => item.col === col)) {
            skewGroups.heavyTails.push({ 
                col, 
                ...analysis,
                priority: 3,
                transformation_suggestion: "Box-Cox transformation (recommended for heavy tails)"
            });
        }
    });

    // Create cards for each non-empty group
    const cards = [];
    
    // Strong Positive Skew Card
    if (skewGroups.strongPositive.length > 0) {
        cards.push(createSkewCard(
            'Strong Positive Skew Detected',
            'These columns show strong positive skewness (S > 1). Log transformation is recommended as it often helps with both skewness and kurtosis issues.',
            skewGroups.strongPositive,
            'high-priority'
        ));
    }

    // Strong Negative Skew Card
    if (skewGroups.strongNegative.length > 0) {
        cards.push(createSkewCard(
            'Strong Negative Skew Detected',
            'These columns show strong negative skewness (S < -1). Square transformation is recommended as it often helps with both skewness and kurtosis issues.',
            skewGroups.strongNegative,
            'high-priority'
        ));
    }

    // Moderate Positive Skew Card
    if (skewGroups.moderatePositive.length > 0) {
        cards.push(createSkewCard(
            'Moderate Positive Skew Detected',
            'These columns show moderate positive skewness (0.5 < S ≤ 1). Square root transformation is recommended.',
            skewGroups.moderatePositive,
            'suggested'
        ));
    }

    // Moderate Negative Skew Card
    if (skewGroups.moderateNegative.length > 0) {
        cards.push(createSkewCard(
            'Moderate Negative Skew Detected',
            'These columns show moderate negative skewness (-1 ≤ S < -0.5). Square transformation is recommended.',
            skewGroups.moderateNegative,
            'suggested'
        ));
    }

    // Heavy Tails Card
    if (skewGroups.heavyTails.length > 0) {
        cards.push(createSkewCard(
            'Heavy-Tailed Distribution Detected',
            'These columns show heavy tails (K > 3.5) without significant skewness. Box-Cox transformation is recommended.',
            skewGroups.heavyTails,
            'suggested'
        ));
    }

    return cards;
}

function createSkewCard(title, message, columns, priority) {
    const card = document.createElement('div');
    card.className = `recommendation-card ${priority}`;
    
    card.innerHTML = `
        <div class="card-header">
            <h3>${title}</h3>
            <span class="priority-badge ${priority}">${priority}</span>
        </div>
        <div class="card-content">
            <p>${message}</p>
            <div class="details" style="display: none;">
                <table class="details-table">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th style="width: 20px;">S</th>
                            <th style="width: 20px;">K</th>
                            <th>Suggested Transformation</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${columns.map(col => `
                            <tr>
                                <td>${col.col}</td>
                                <td style="text-align: right;">${col.skewness.toFixed(2)}</td>
                                <td style="text-align: right;">${col.kurtosis.toFixed(2)}</td>
                                <td>${col.transformation_suggestion}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="card-actions">
            <button class="action-button">View Details</button>
        </div>
    `;

    // Add click handler for the action button
    const actionButton = card.querySelector('.action-button');
    const details = card.querySelector('.details');
    actionButton.addEventListener('click', () => {
        details.style.display = details.style.display === 'none' ? 'block' : 'none';
        actionButton.textContent = details.style.display === 'none' ? 'View Details' : 'Hide Details';
    });

    return card;
} 
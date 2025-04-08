from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
from app.core.ai_engine import AIEngine
from app.core.database import AnalysisHistoryDB

analysis_bp = Blueprint('analysis', __name__)

# Initialize components
ai_engine = AIEngine()
db = AnalysisHistoryDB()

@analysis_bp.route('/descriptive', methods=['GET'])
def get_descriptive_stats():
    """Get descriptive statistics for the current dataset."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        stats = {
            'summary': current_df.describe().to_dict(),
            'correlation': current_df.corr().to_dict(),
            'missing_values': current_df.isnull().sum().to_dict()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/inferential', methods=['POST'])
def perform_inferential_analysis():
    """Perform inferential statistical analysis."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        analysis_params = request.json
        if not analysis_params:
            return jsonify({'error': 'No analysis parameters provided'}), 400
            
        # Add your inferential analysis logic here
        # Example: t-test, ANOVA, regression, etc.
        
        return jsonify({'success': True, 'results': {}})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/plot/<plot_type>', methods=['POST'])
def generate_plot(plot_type):
    """Generate various types of plots."""
    try:
        if current_df is None:
            return jsonify({'error': 'No data loaded'}), 400
            
        plot_params = request.json
        if not plot_params:
            return jsonify({'error': 'No plot parameters provided'}), 400
            
        # Generate plot based on type
        plt.figure(figsize=(10, 6))
        
        if plot_type == 'histogram':
            sns.histplot(data=current_df, x=plot_params.get('column'))
        elif plot_type == 'scatter':
            sns.scatterplot(data=current_df, x=plot_params.get('x'), y=plot_params.get('y'))
        elif plot_type == 'box':
            sns.boxplot(data=current_df, y=plot_params.get('column'))
        else:
            return jsonify({'error': 'Unsupported plot type'}), 400
            
        # Convert plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return jsonify({'plot': plot_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
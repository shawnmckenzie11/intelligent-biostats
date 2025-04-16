from flask import jsonify
from app.core.data_manager import DataManager

data_manager = DataManager()

@app.route('/api/data/preview', methods=['GET'])
def get_data_preview():
    if data_manager.data is None:
        return jsonify({'error': 'No data loaded'}), 400
        
    stats = data_manager.get_column_descriptive_stats()
    if stats:
        # Add debug logging
        for col, col_type in zip(stats['column_types']['columns'], 
                               stats['column_types']['column_types_list']):
            logger.debug(f"Sending column {col} with type {col_type} to frontend")
    
    return jsonify(data_manager.get_data_preview()) 
# intelligent-biostats

A smart biostatistics analysis tool powered by AI that provides comprehensive statistical analysis for biological data.

## Project Structure

This structure follows best practices and allows for scalable development. Here's what each main component does:

1. `app/core/`: Contains the main logic
   - `data_manager.py`: Handles the enhanced Pandas DataFrame with metadata
   - `ai_engine.py`: Manages AI recommendations and learning
   - `stats_engine.py`: Implements statistical analyses

2. `app/api/`: REST API implementation for web interface communication

3. `app/frontend/`: Web interface components
   - Separate static files (CSS, JS, assets)
   - Templates for dynamic content

4. `tests/`: Comprehensive test suite matching the core structure

5. `docs/`: Both API documentation and user guides

6. `config/`: Configuration management

This structure allows you to:
- Maintain separation of concerns
- Scale features independently
- Add new statistical analyses easily
- Implement comprehensive testing
- Provide clear documentation
- Handle frontend and backend separately


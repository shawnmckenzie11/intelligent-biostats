# Intelligent Biostats

A modern web application for intelligent statistical analysis and data visualization. This tool provides automated statistical recommendations and analysis workflows based on your data characteristics.

## Features

- Automated statistical analysis recommendations
- Interactive data visualization
- Support for various statistical tests:
  - One Sample T-Test
  - One Sample Median Test
  - Binomial Test
  - Chi-Square Goodness of Fit
  - Correlation Analysis
  - Simple Linear Regression
  - Multiple Regression
  - Independent Samples T-Test
  - Logistic Regression
- Data quality assessment
- Missing value analysis
- Distribution analysis and transformation suggestions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-biostats.git
cd intelligent-biostats
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python run.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload your CSV data file and follow the interactive analysis workflow

## Project Structure

```
intelligent-biostats/
├── app/                    # Main application package
│   ├── api/               # API endpoints
│   ├── core/              # Core business logic
│   ├── frontend/          # Frontend assets
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── logs/                  # Log files
├── tests/                 # Test suite
├── uploads/              # Uploaded files directory
└── temp/                 # Temporary files
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
This project follows PEP 8 style guidelines. To check your code:
```bash
flake8 .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and Python
- Uses pandas for data manipulation
- Visualization powered by matplotlib and seaborn


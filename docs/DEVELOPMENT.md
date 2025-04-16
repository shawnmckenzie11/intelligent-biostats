# Development Guide

## Setting Up Development Environment

### Prerequisites
- Python 3.7+
- Cursor IDE
- Git

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-biostats.git
cd intelligent-biostats
```

2. Install Cursor IDE:
- Download from [cursor.sh](https://cursor.sh)
- Install and open the application

3. Set up the development environment:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make setup script executable
chmod +x setup-cursor.sh

# Run Cursor setup
./setup-cursor.sh
```

4. Open project in Cursor IDE:
- File -> Open Folder -> Select project directory
- Verify Cursor rules are loaded in the bottom status bar

## Development Workflow

### 1. Cursor Rules
- UI changes must follow `ui-formatting-rules.mdc`
- Backend changes must follow `library-and-route-awareness.mdc`
- Rules are automatically enforced by Cursor IDE

### 2. Code Style
- Follow PEP 8 guidelines
- Run style checks:
```bash
flake8 .
```

### 3. Testing
- Write tests for new features
- Run tests before committing:
```bash
python -m pytest tests/
```

### 4. Git Workflow
- Create feature branches from `main`
- Follow commit message conventions
- GitHub Actions will validate Cursor rules

### 5. Documentation
- Update relevant documentation
- Keep docstrings current
- Document any new Cursor rules

## Troubleshooting

### Cursor Rules Not Loading
1. Verify file existence:
```bash
ls -la .cursor/rules/
ls -la .cursor-config.json
```

2. Run setup script:
```bash
./setup-cursor.sh
```

3. Restart Cursor IDE

### GitHub Actions
- Check Actions tab for validation results
- Fix any reported issues
- Re-run failed checks if needed

## Additional Resources

- [CURSOR_RULES.md](../CURSOR_RULES.md): Detailed rules documentation
- [Contributing Guide](../CONTRIBUTING.md): Contribution guidelines
- [GitHub Actions Workflows](../.github/workflows/): CI/CD configuration 
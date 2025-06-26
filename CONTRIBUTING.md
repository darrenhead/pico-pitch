# Contributing to PicoPitch

Thank you for your interest in contributing to PicoPitch! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Use clear, descriptive titles
- Include steps to reproduce bugs
- Mention your environment (OS, Python version)

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with clear commit messages
4. Add/update tests if applicable
5. Update documentation as needed
6. Submit a pull request with a clear description

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pico-pitch.git
cd pico-pitch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make your changes
# Test locally with ./run_app.sh
```

### Testing

Currently, modules can be tested individually:
```bash
python3 database_manager.py  # Test DB connection
python3 orchestrator.py      # Test orchestrator
```

We welcome contributions to add a proper test suite!

## Questions?

Feel free to open an issue for any questions about contributing.
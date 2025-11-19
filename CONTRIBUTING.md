# Contributing to MarketInsightPro

Thank you for your interest in contributing to MarketInsightPro! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

By participating in this project, you agree to:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/MarketInsightPro.git
   cd MarketInsightPro
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/DeepMoney/MarketInsightPro.git
   ```

4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Git

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install development dependencies**:
   ```bash
   pip install pytest pytest-cov pytest-mock flake8 black isort
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your local PostgreSQL credentials
   ```

4. **Initialize the database**:
   ```bash
   # Database will auto-initialize on first run
   streamlit run app.py
   ```

### Using Docker for Development

```bash
# Build and run with docker-compose
docker-compose up

# Run tests in Docker
docker-compose run --rm app pytest
```

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

- **Bug fixes**: Fix issues in the codebase
- **New features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Code quality**: Refactoring, optimization
- **UI/UX improvements**: Enhance user interface

### Contribution Workflow

1. **Check existing issues** to see if your contribution is already being worked on
2. **Create an issue** if one doesn't exist (for bugs or features)
3. **Discuss your approach** in the issue before starting work
4. **Write your code** following our coding standards
5. **Add tests** for new functionality
6. **Update documentation** as needed
7. **Submit a pull request**

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: Maximum 127 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Prefer double quotes for strings
- **Imports**: Group and sort imports (use `isort`)

### Code Formatting

We use the following tools:

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .
```

### Code Structure

- **Modularity**: Keep functions and classes focused and single-purpose
- **Documentation**: Add docstrings to all functions, classes, and modules
- **Type hints**: Use type hints where appropriate
- **Error handling**: Handle errors gracefully with clear messages

### Docstring Format

Use Google-style docstrings:

```python
def calculate_metrics(trades_df: pd.DataFrame) -> dict:
    """
    Calculate performance metrics from trade data.

    Args:
        trades_df: DataFrame containing trade records with columns:
                   entry_time, exit_time, pnl, etc.

    Returns:
        Dictionary containing calculated metrics including:
        win_rate, profit_factor, sharpe_ratio, etc.

    Raises:
        ValueError: If trades_df is empty or missing required columns
    """
    pass
```

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix (e.g., `test_analytics.py`)
- Name test functions with `test_` prefix
- Use descriptive test names that explain what is being tested

### Test Structure

```python
import pytest
from analytics_engine import calculate_all_metrics

def test_calculate_metrics_with_valid_data():
    """Test metric calculation with valid trade data"""
    # Arrange
    trades_df = create_sample_trades()

    # Act
    metrics = calculate_all_metrics(trades_df)

    # Assert
    assert metrics['win_rate'] > 0
    assert metrics['profit_factor'] > 0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_analytics.py

# Run specific test
pytest tests/test_analytics.py::test_calculate_metrics_with_valid_data

# Run tests matching pattern
pytest -k "metric"
```

### Test Coverage

- Aim for **80%+ code coverage**
- All new features must include tests
- Bug fixes should include regression tests

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** and ensure they pass:
   ```bash
   pytest
   ```

3. **Check code formatting**:
   ```bash
   black --check .
   isort --check-only .
   flake8 .
   ```

4. **Update documentation** if needed

### PR Guidelines

1. **Title**: Use a clear, descriptive title
   - Good: "Add Sharpe ratio calculation to analytics engine"
   - Bad: "Update analytics"

2. **Description**: Include:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Screenshots (for UI changes)
   - Related issue numbers

3. **Commits**:
   - Use clear, descriptive commit messages
   - Follow conventional commits format:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs:` for documentation
     - `test:` for tests
     - `refactor:` for refactoring
     - `chore:` for maintenance

4. **Size**: Keep PRs focused and reasonably sized
   - If your PR is large, consider splitting it into smaller PRs

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Reporting Bugs

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Test with latest version** to ensure bug still exists
3. **Gather information** about the bug

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.11]
- PostgreSQL version: [e.g. 14.5]
- Browser: [e.g. Chrome 120]

**Additional context**
Any other context about the problem.
```

## Suggesting Enhancements

### Enhancement Guidelines

1. **Check existing issues/PRs** for similar suggestions
2. **Provide clear use case** for the enhancement
3. **Consider backwards compatibility**
4. **Be open to discussion** about implementation

### Enhancement Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Mockups, examples, or other context.
```

## Getting Help

If you need help:

- **Check the documentation**: See `primedoc.md` and `README.md`
- **Ask in issues**: Open an issue with the `question` label
- **Review existing code**: Look at similar implementations in the codebase

## Recognition

Contributors will be recognized in:

- GitHub contributors list
- Release notes for significant contributions
- `CONTRIBUTORS.md` file (if created)

Thank you for contributing to MarketInsightPro!

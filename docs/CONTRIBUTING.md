# Contributing to CoreRecon SOC

Thank you for your interest in contributing to CoreRecon SOC! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and professional environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/CoreRecon_SOC.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for linting

```bash
# Format code
black app/ tests/
isort app/ tests/

# Run linters
flake8 app/ tests/
mypy app/
```

### JavaScript/TypeScript
- Follow Airbnb JavaScript Style Guide
- Use TypeScript for all new code
- Use Prettier for formatting
- Use ESLint for linting

```bash
cd frontend
npm run format
npm run lint
```

## Testing Requirements

### Unit Tests
- All new features must include unit tests
- Maintain minimum 80% code coverage
- Use pytest for Python tests
- Use Jest for JavaScript tests

```bash
# Run Python tests
pytest tests/ --cov=app --cov-report=html

# Run JavaScript tests
cd frontend && npm test
```

### Integration Tests
- Test API endpoints end-to-end
- Test WebSocket connections
- Test database transactions

### Security Tests
- Run SAST scans before submitting PR
- Run dependency vulnerability scans

```bash
# Security scans
bandit -r app/
pip-audit
```

## Pull Request Process

1. **Branch Naming**:
   - Feature: `feature/short-description`
   - Bug fix: `fix/short-description`
   - Documentation: `docs/short-description`
   - Security: `security/short-description`

2. **Commit Messages**:
   - Use conventional commits format
   - Examples:
     - `feat: Add incident timeline visualization`
     - `fix: Resolve WebSocket connection timeout`
     - `docs: Update API documentation`
     - `security: Patch SQL injection vulnerability`

3. **PR Template**:
   - Fill out the entire PR template
   - Link related issues
   - Include test results
   - Add screenshots for UI changes
   - Complete all checklist items

4. **Review Process**:
   - At least one approval required
   - All CI checks must pass
   - Security scan must pass
   - No merge conflicts

## Security Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Instead:
1. Email security@corerecon-soc.local (or use GitHub Security Advisories)
2. Include detailed description
3. Provide steps to reproduce
4. Suggest a fix if possible

## Documentation

- Update relevant documentation for all changes
- Add docstrings to all public functions and classes
- Update API documentation for endpoint changes
- Add examples for complex features

### Docstring Format (Python)
```python
def process_alert(alert_id: int, severity: str) -> Alert:
    """
    Process an incoming alert and determine escalation.

    Args:
        alert_id: Unique identifier for the alert
        severity: Alert severity level (critical, high, medium, low)

    Returns:
        Alert: Processed alert object with enriched data

    Raises:
        AlertNotFoundError: If alert_id does not exist
        ValidationError: If severity is invalid

    Example:
        >>> alert = process_alert(12345, "critical")
        >>> print(alert.status)
        'assigned'
    """
    pass
```

## Detection Rule Contributions

When contributing detection rules:

1. Test with historical data (minimum 30 days)
2. Document false positive scenarios
3. Map to MITRE ATT&CK techniques
4. Provide sample logs
5. Include testing instructions
6. Document data source requirements

## Accessibility Requirements

All UI contributions must meet:

- WCAG 2.2 AA standards
- Keyboard navigation support
- Screen reader compatibility
- Minimum 4.5:1 color contrast
- Focus indicators visible

Test with:
```bash
cd frontend
npm run test:a11y
```

## Performance Guidelines

- API endpoints should respond within 200ms (p95)
- Database queries optimized with proper indexes
- Large operations should be asynchronous
- WebSocket messages should be < 1KB

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open a discussion in GitHub Discussions
- Check existing issues and PRs
- Review documentation

Thank you for contributing to CoreRecon SOC!

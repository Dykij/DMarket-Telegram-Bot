# Contributing to DMarket Telegram Bot

**Версия**: 3.0
**Последнее обновление**: 17 декабря 2025 г.

---

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Environment Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/dmarket-telegram-bot.git
   cd dmarket-telegram-bot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

## Code Style Guidelines

We follow PEP 8 style guidelines with some specific conventions:

### Python Code Style
- Use **Black** for code formatting (max line length: 88)
- Use **Ruff** for linting and import sorting
- Use **MyPy** for type checking
- Write comprehensive docstrings for all functions and classes
- Use type hints wherever possible

### Code Quality Standards
- Minimum 80% test coverage required
- All tests must pass before submitting PR
- No linting errors allowed
- All functions and classes must have docstrings

### Running Code Quality Checks
```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make type-check

# Run all quality checks
make qa
```

## Testing Guidelines

### Writing Tests
- Write unit tests for all new functionality
- Use pytest for testing framework
- Mock external API calls
- Test both success and failure scenarios
- Include edge cases and error conditions

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_specific_file.py

# Run tests in parallel
pytest -n auto
```

### Test Structure
```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── fixtures/          # Test fixtures
└── conftest.py       # Pytest configuration
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   make qa
   make test-cov
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for adding tests
   - `refactor:` for code refactoring
   - `style:` for formatting changes
   - `chore:` for maintenance tasks

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Create a Pull Request**
   - Use the PR template
   - Provide clear description of changes
   - Link relevant issues
   - Add screenshots for UI changes

### Pull Request Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Test coverage is maintained/improved
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] Commit messages follow conventional commits

## Issue Reporting

When reporting bugs, please include:

1. **Bug Description**: Clear and concise description
2. **Steps to Reproduce**: Detailed steps
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, bot version
6. **Logs**: Relevant error messages or logs

### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 20.04]
 - Python Version: [e.g. 3.9.0]
 - Bot Version: [e.g. 1.0.0]

**Additional Context**
Add any other context about the problem.
```

## Feature Requests

When requesting features, please include:

1. **Feature Description**: Clear description of the feature
2. **Use Case**: Why this feature is needed
3. **Proposed Solution**: How you think it should work
4. **Alternatives**: Alternative solutions considered
5. **Additional Context**: Any other relevant information

## Development Workflow

### Branch Naming Convention
- `feature/feature-name` for new features
- `fix/bug-description` for bug fixes
- `docs/update-description` for documentation updates
- `refactor/component-name` for refactoring

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release after merge
5. GitHub Actions will handle deployment

## Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Unacceptable Behavior
Examples of unacceptable behavior include:
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Getting Help

- 📖 Read the [documentation](docs/)
- 💬 Join our [Discussions](https://github.com/your-username/dmarket-telegram-bot/discussions)
- 🐛 Report bugs in [Issues](https://github.com/your-username/dmarket-telegram-bot/issues)
- 📧 Contact maintainers directly for security issues

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor appreciation posts

Thank you for contributing! 🎉

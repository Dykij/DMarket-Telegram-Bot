#!/bin/bash
# ============================================================================
# DMarket Telegram Bot - postCreate Script
# ============================================================================
# Runs after the container is created and features are installed
# Installs project dependencies and configures development tools
# ============================================================================

set -e

echo "📦 Installing project dependencies..."

# ============================================================================
# COLORS FOR OUTPUT
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# WORKSPACE SETUP
# ============================================================================
WORKSPACE_DIR="/workspaces/DMarket-Telegram-Bot"
cd "$WORKSPACE_DIR"

# Activate virtual environment
VENV_DIR="$WORKSPACE_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    success "Virtual environment activated"
else
    error "Virtual environment not found! Run onCreate.sh first."
    exit 1
fi

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
info "Installing project dependencies from requirements.txt..."

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    success "Requirements installed successfully"
else
    warning "requirements.txt not found"
fi

# Install in editable mode with dev dependencies
info "Installing package in editable mode with dev dependencies..."

if [ -f "pyproject.toml" ]; then
    pip install -e ".[dev]" || {
        warning "Could not install with [dev] extras, trying without..."
        pip install -e .
    }
    success "Package installed in editable mode"
fi

# ============================================================================
# PRE-COMMIT HOOKS
# ============================================================================
info "Setting up pre-commit hooks..."

if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    success "Pre-commit hooks installed"
else
    warning ".pre-commit-config.yaml not found, skipping pre-commit setup"
fi

# ============================================================================
# DATABASE MIGRATIONS
# ============================================================================
info "Checking database migrations..."

if [ -f "alembic.ini" ]; then
    # Wait for PostgreSQL to be ready
    info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if pg_isready -h postgres -p 5432 -U dmarket_user -d dmarket_bot 2>/dev/null; then
            success "PostgreSQL is ready"
            break
        fi
        sleep 1
    done

    # Run migrations
    if command -v alembic &> /dev/null; then
        info "Running database migrations..."
        alembic upgrade head 2>/dev/null || warning "Migration failed or no migrations to apply"
    fi
else
    info "No alembic.ini found, skipping migrations"
fi

# ============================================================================
# MYPY STUBS
# ============================================================================
info "Installing type stubs..."

pip install --quiet types-requests types-redis types-PyYAML 2>/dev/null || true
success "Type stubs installed"

# ============================================================================
# VERIFY INSTALLATION
# ============================================================================
info "Verifying installation..."

echo ""
echo "🔍 Installed packages versions:"
echo "--------------------------------"
python --version
pip show python-telegram-bot 2>/dev/null | grep -E "Name|Version" || echo "python-telegram-bot: not found"
pip show httpx 2>/dev/null | grep -E "Name|Version" || echo "httpx: not found"
pip show pytest 2>/dev/null | grep -E "Name|Version" || echo "pytest: not found"
pip show ruff 2>/dev/null | grep -E "Name|Version" || echo "ruff: not found"
pip show mypy 2>/dev/null | grep -E "Name|Version" || echo "mypy: not found"
echo ""

# ============================================================================
# QUICK CHECKS
# ============================================================================
info "Running quick validation checks..."

# Ruff check (non-blocking)
echo "📝 Ruff lint check:"
python -m ruff check src/ --output-format=concise --exit-zero 2>&1 | head -10 || true

echo ""
echo "=========================================="
echo "🎉 postCreate setup complete!"
echo "=========================================="
echo ""
echo "📚 Quick Start Commands:"
echo "  • make test      - Run tests"
echo "  • make lint      - Run linter"
echo "  • make fix       - Auto-fix issues"
echo "  • make check     - Full code check"
echo "  • make run       - Start the bot"
echo ""
echo "⚠️  Remember to update .env with your API keys!"
echo "📖 See docs/QUICK_START.md for more info"

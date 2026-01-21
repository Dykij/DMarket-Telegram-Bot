#!/bin/bash
# ============================================================================
# DMarket Telegram Bot - onCreate Script
# ============================================================================
# Runs once when the container is first created
# Sets up the development environment
# ============================================================================

set -e

echo "🚀 Starting DMarket Bot development environment setup..."

# ============================================================================
# COLORS FOR OUTPUT
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
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

if [ ! -d "$WORKSPACE_DIR" ]; then
    error "Workspace directory not found: $WORKSPACE_DIR"
    exit 1
fi

cd "$WORKSPACE_DIR"

# ============================================================================
# ENVIRONMENT FILE
# ============================================================================
info "Setting up environment file..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        success "Created .env from .env.example"
        warning "Remember to update .env with your actual credentials!"
    else
        warning ".env.example not found, creating minimal .env"
        cat > .env << 'EOF'
# DMarket Telegram Bot - Development Environment
ENVIRONMENT=development
DEBUG=true
DRY_RUN=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dmarket_user:dmarket_password@postgres:5432/dmarket_bot
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=your_token_here
DMARKET_PUBLIC_KEY=your_public_key
DMARKET_SECRET_KEY=your_secret_key
EOF
    fi
else
    info ".env file already exists"
fi

# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================
info "Creating required directories..."

mkdir -p data logs .mypy_cache .pytest_cache .ruff_cache htmlcov
success "Created project directories"

# ============================================================================
# GIT CONFIGURATION
# ============================================================================
info "Configuring Git..."

# Safe directory for devcontainer
git config --global --add safe.directory "$WORKSPACE_DIR"

# Git LFS setup
if command -v git-lfs &> /dev/null; then
    git lfs install --local
    success "Git LFS configured"
fi

# ============================================================================
# PYTHON VERSION CHECK
# ============================================================================
info "Checking Python version..."

PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    success "Python $PYTHON_VERSION detected (meets 3.11+ requirement)"
else
    error "Python 3.11+ required, found $PYTHON_VERSION"
    exit 1
fi

# ============================================================================
# VIRTUAL ENVIRONMENT
# ============================================================================
info "Setting up virtual environment..."

VENV_DIR="$WORKSPACE_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python -m venv "$VENV_DIR"
    success "Virtual environment created at $VENV_DIR"
else
    info "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip setuptools wheel
success "pip upgraded to latest version"

echo ""
echo "=========================================="
echo "🎉 onCreate setup complete!"
echo "=========================================="
echo ""
echo "Next: postCreate.sh will install dependencies"

#!/bin/bash
# ============================================================================
# DMarket Telegram Bot - postStart Script
# ============================================================================
# Runs each time the container starts
# Performs startup checks and displays welcome message
# ============================================================================

# ============================================================================
# COLORS FOR OUTPUT
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# WORKSPACE SETUP
# ============================================================================
WORKSPACE_DIR="/workspaces/DMarket-Telegram-Bot"
cd "$WORKSPACE_DIR" 2>/dev/null || exit 0

# Activate virtual environment
VENV_DIR="$WORKSPACE_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate" 2>/dev/null
fi

# ============================================================================
# DISPLAY WELCOME BANNER
# ============================================================================
clear 2>/dev/null || true

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║   ██████╗ ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗███████╗████████╗        ║"
echo "║   ██╔══██╗████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝        ║"
echo "║   ██║  ██║██╔████╔██║███████║██████╔╝█████╔╝ █████╗     ██║           ║"
echo "║   ██║  ██║██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗ ██╔══╝     ██║           ║"
echo "║   ██████╔╝██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗███████╗   ██║           ║"
echo "║   ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝           ║"
echo "║                                                                       ║"
echo "║                 🤖 Telegram Trading Bot                               ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# SERVICES STATUS CHECK
# ============================================================================
echo -e "${BOLD}📊 Services Status:${NC}"
echo "─────────────────────────────────────────"

# Check PostgreSQL
if pg_isready -h postgres -p 5432 -U dmarket_user -d dmarket_bot 2>/dev/null; then
    echo -e "  PostgreSQL:  ${GREEN}● Running${NC} (postgres:5432)"
else
    echo -e "  PostgreSQL:  ${RED}○ Not available${NC}"
fi

# Check Redis
if redis-cli -h redis ping 2>/dev/null | grep -q PONG; then
    echo -e "  Redis:       ${GREEN}● Running${NC} (redis:6379)"
else
    echo -e "  Redis:       ${RED}○ Not available${NC}"
fi

# Check Python environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "  Python venv: ${GREEN}● Activated${NC} ($VIRTUAL_ENV)"
else
    echo -e "  Python venv: ${YELLOW}○ Not activated${NC}"
fi

echo ""

# ============================================================================
# ENVIRONMENT CHECK
# ============================================================================
echo -e "${BOLD}🔧 Environment:${NC}"
echo "─────────────────────────────────────────"
echo "  Python:     $(python --version 2>&1 | cut -d' ' -f2)"
echo "  Workspace:  $WORKSPACE_DIR"
echo "  DRY_RUN:    ${DRY_RUN:-true}"
echo "  LOG_LEVEL:  ${LOG_LEVEL:-INFO}"
echo ""

# ============================================================================
# .ENV FILE CHECK
# ============================================================================
if [ -f "$WORKSPACE_DIR/.env" ]; then
    # Check if important variables are set
    if grep -q "your_token_here\|your_public_key\|your_secret_key" "$WORKSPACE_DIR/.env" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Warning: Please update .env with your actual API credentials!${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  Warning: .env file not found! Copy from .env.example${NC}"
    echo ""
fi

# ============================================================================
# QUICK COMMANDS REFERENCE
# ============================================================================
echo -e "${BOLD}🚀 Quick Commands:${NC}"
echo "─────────────────────────────────────────"
echo "  make test      Run tests"
echo "  make lint      Run linter (Ruff)"
echo "  make fix       Auto-fix code issues"
echo "  make check     Full code check"
echo "  make qa        Quality assurance"
echo "  make run       Start the bot"
echo ""
echo "  pytest tests/  Run specific tests"
echo "  ruff check .   Lint all files"
echo "  mypy src/      Type check"
echo ""

# ============================================================================
# DOCUMENTATION LINKS
# ============================================================================
echo -e "${BOLD}📚 Documentation:${NC}"
echo "─────────────────────────────────────────"
echo "  Quick Start:  docs/QUICK_START.md"
echo "  Arbitrage:    docs/ARBITRAGE.md"
echo "  API Spec:     docs/DMARKET_API_FULL_SPEC.md"
echo "  Security:     SECURITY.md"
echo ""

# ============================================================================
# SAFETY REMINDER
# ============================================================================
echo -e "${YELLOW}${BOLD}⚠️  Safety Reminder:${NC}"
echo "─────────────────────────────────────────"
echo -e "  DRY_RUN mode is ${GREEN}ENABLED${NC} by default."
echo "  The bot will NOT execute real trades."
echo "  Set DRY_RUN=false in .env for real trading."
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

#!/bin/bash
# GitHub Copilot Agent - Automated Activation Script (Linux/macOS)
# Version: 1.0
# Date: 2025-12-14

echo "========================================"
echo "GitHub Copilot Agent Activation Helper"
echo "========================================"
echo ""

REPO="Dykij/DMarket-Telegram-Bot"
BASE_URL="https://github.com/$REPO"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) not found"
    echo ""
    echo "Install instructions:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo ""
    read -p "Continue without gh? (manual setup) [y/N]: " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi

    echo ""
    echo "Opening browser for manual setup..."

    # Open URLs based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$BASE_URL/labels"
        sleep 1
        open "$BASE_URL/settings"
        sleep 1
        open "$BASE_URL/settings/actions"
    else
        xdg-open "$BASE_URL/labels" 2>/dev/null
        sleep 1
        xdg-open "$BASE_URL/settings" 2>/dev/null
        sleep 1
        xdg-open "$BASE_URL/settings/actions" 2>/dev/null
    fi

    echo ""
    echo "📋 Manual steps:"
    echo "1. Create 6 labels"
    echo "2. Enable Copilot Agent (Settings → Copilot)"
    echo "3. Set Actions permissions"
    echo ""
    echo "See .github/ACTIVATION_GUIDE.md for details"
    exit 0
fi

echo "✅ GitHub CLI found"
echo ""

# Check authentication
echo "Checking GitHub authentication..."
if ! gh auth status &> /dev/null; then
    echo "⚠️  Not authenticated with GitHub"
    echo ""
    echo "Starting authentication..."
    gh auth login

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Authentication failed. Exiting."
        exit 1
    fi
fi

echo "✅ Authenticated with GitHub"
echo ""

# Create labels
echo "========================================"
echo "Creating Labels"
echo "========================================"
echo ""

declare -a labels=(
    "copilot-task:0E8A16:Task for GitHub Copilot Coding Agent"
    "copilot-test:1D76DB:Test coverage improvement task"
    "copilot-refactor:FBCA04:Code refactoring task"
    "copilot-docs:5319E7:Documentation update task"
    "copilot-security:D93F0B:Security fix task"
    "copilot-bugfix:EE0701:Bug fix task"
)

LABELS_CREATED=0
for label in "${labels[@]}"; do
    IFS=':' read -r name color description <<< "$label"
    echo -n "Creating label: $name..."

    if gh label create "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null; then
        echo " ✅"
        ((LABELS_CREATED++))
    else
        echo " ⚠️  Already exists or failed"
    fi
done

echo ""
echo "✅ Labels: $LABELS_CREATED/6 created"
echo ""

# Check workflows
echo "========================================"
echo "Checking Workflows"
echo "========================================"
echo ""

echo "Fetching workflow list..."
if gh workflow list --repo "$REPO" | grep -i copilot; then
    echo ""
else
    echo "⚠️  No Copilot workflows found yet"
fi

# Manual steps reminder
echo ""
echo "========================================"
echo "Manual Steps Required"
echo "========================================"
echo ""

echo "⚠️  The following require web browser:"
echo ""
echo "1. Enable Copilot Agent:"
echo "   $BASE_URL/settings"
echo "   → Code and automation → Copilot"
echo "   → Enable 'Copilot coding agent'"
echo ""
echo "2. Configure Actions permissions:"
echo "   $BASE_URL/settings/actions"
echo "   → Workflow permissions: 'Read and write'"
echo "   → Allow GitHub Actions to create PRs"
echo ""
echo "3. Create test issue:"
echo "   $BASE_URL/issues/new/choose"
echo "   → Select 'Copilot Task' template"
echo ""

read -p "Open these pages in browser now? [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Opening browser tabs..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$BASE_URL/settings"
        sleep 1
        open "$BASE_URL/settings/actions"
        sleep 1
        open "$BASE_URL/issues/new/choose"
    else
        xdg-open "$BASE_URL/settings" 2>/dev/null
        sleep 1
        xdg-open "$BASE_URL/settings/actions" 2>/dev/null
        sleep 1
        xdg-open "$BASE_URL/issues/new/choose" 2>/dev/null
    fi
fi

echo ""
echo "========================================"
echo "Automated Setup Complete!"
echo "========================================"
echo ""

echo "✅ Labels created: $LABELS_CREATED/6"
echo "⏳ Manual steps: 3 remaining (~10 minutes)"
echo ""

echo "📚 Documentation:"
echo "   .github/ACTIVATION_GUIDE.md"
echo "   .github/COPILOT_AGENT_GUIDE.md"
echo ""

echo "Next: Complete manual steps in browser"
echo ""

# Create completion marker
cat > .github/.copilot-setup-status.json << EOF
{
  "labels_created": $([ $LABELS_CREATED -eq 6 ] && echo "true" || echo "false"),
  "automated_setup_completed": true,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "manual_steps_remaining": 3
}
EOF

chmod +x .github/activate-copilot.sh
echo "✅ Status saved to .github/.copilot-setup-status.json"
echo ""

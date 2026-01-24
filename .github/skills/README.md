# DMarket-Telegram-Bot Skills Repository

**Version**: 1.0.0  
**Last Updated**: 2026-01-24

## Overview

This directory contains all AI agent skills for the DMarket-Telegram-Bot project. Skills are organized by team and functionality for easy discovery and maintenance.

## Directory Structure

```
.github/skills/
├── core/           # Core functionality skills
├── trading/        # Trading and arbitrage skills
├── ml/             # Machine learning skills
├── security/       # Security and monitoring skills
├── devops/         # DevOps and infrastructure skills
├── CODEOWNERS      # Access control
└── README.md       # This file
```

## Skills Index

### 📦 Core Skills (3 skills)

| Skill ID | Name | Status | Team | Version |
|----------|------|--------|------|---------|
| `skill-orchestrator` | Skill Orchestrator | approved | @core-team | 1.0.0 |
| `skill-profiler` | Skill Profiler | approved | @core-team | 1.0.0 |
| `skillsmp-integration` | SkillsMP Integration | approved | @core-team | 1.0.0 |

### 💰 Trading Skills (3 skills)

| Skill ID | Name | Status | Team | Version |
|----------|------|--------|------|---------|
| `ai-arbitrage-predictor` | AI Arbitrage Predictor | approved | @trading-team | 1.0.0 |
| `ai-backtester` | AI Backtester | approved | @trading-team | 1.0.0 |
| `risk-assessment` | Risk Assessment | approved | @trading-team | 1.0.0 |

### 🤖 ML Skills (3 skills)

| Skill ID | Name | Status | Team | Version |
|----------|------|--------|------|---------|
| `ensemble-builder` | Ensemble Builder | approved | @ml-team | 1.0.0 |
| `advanced-feature-selector` | Feature Selector | approved | @ml-team | 1.0.0 |
| `nlp-command-handler` | NLP Command Handler | approved | @ml-team | 1.0.0 |

### 🔒 Security Skills (1 skill)

| Skill ID | Name | Status | Team | Version |
|----------|------|--------|------|---------|
| `ai-threat-detector` | AI Threat Detector | approved | @security-team | 1.0.0 |

## Skill Lifecycle

### Statuses

- **draft** - In development, not ready for use
- **in-review** - Submitted for review
- **approved** - Approved and ready for production use
- **deprecated** - Outdated, migration recommended
- **archived** - No longer maintained

### Approval Process

1. **Create** skill in appropriate team directory
2. **Submit** Pull Request with skill files
3. **Review** by 2+ team members (see CODEOWNERS)
4. **Validate** automatic checks (syntax, security, tests)
5. **Approve** by tech lead
6. **Merge** and status updated to "approved"

## Adding a New Skill

1. Choose appropriate team directory (`core`, `trading`, `ml`, `security`, `devops`)
2. Create skill subdirectory: `.github/skills/{team}/{skill-id}/`
3. Add `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: "your-skill-id"
   version: "1.0.0"
   status: "draft"
   team: "@your-team"
   category: "category"
   description: "Brief description"
   author: "your-name"
   created_date: "YYYY-MM-DD"
   review_required: true
   ---
   ```
4. Add optional files:
   - `scripts/` - Helper scripts
   - `templates/` - Code templates
   - `tests/` - Skill tests
   - `resources/` - Additional resources
5. Submit Pull Request
6. Wait for reviews and approval

## Usage

### GitHub Copilot

Skills in `.github/skills/` are automatically discovered by GitHub Copilot with native Agent Skills support.

### VS Code

1. Install GitHub Copilot extension
2. Skills are auto-loaded from `.github/skills/`
3. Use `@workspace` to activate skills

### CLI

```bash
# List all skills
python scripts/skills_cli.py list

# Search skills
python scripts/skills_cli.py search "arbitrage"

# Get skill info
python scripts/skills_cli.py info ai-arbitrage-predictor

# Validate skills
python scripts/skills_cli.py validate
```

## Migration from Legacy Structure

Legacy skills in `src/*/SKILL_*.md` are being migrated to `.github/skills/`. Migration status tracked in #TBD.

## Documentation

- **Analysis**: `docs/SKILLSMP_LATEST_IMPROVEMENTS_2026.md`
- **Implementation Status**: `SKILLSMP_COMPLETE_IMPLEMENTATION_STATUS.md`
- **Phase 2 Features**: `docs/SKILLSMP_PHASE2_ADVANCED_FEATURES.md`

## Support

- **Issues**: Report via GitHub Issues
- **Questions**: Contact @core-team
- **Contributions**: See CONTRIBUTING.md

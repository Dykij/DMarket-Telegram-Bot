---
name: Bug Report 🐛
about: Create a report to help us improve the DMarket Telegram Bot
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''

---

## 🐛 Bug Description
<!-- A clear and concise description of what the bug is -->



## 🔄 Steps To Reproduce
<!-- Steps to reproduce the behavior -->

1. Configure bot with '...'
2. Run command '....'
3. Set parameters '....'
4. See error

## ✅ Expected Behavior
<!-- A clear description of what you expected to happen -->



## ❌ Actual Behavior
<!-- What actually happened -->



## 📋 Error Logs
<!-- Paste relevant error logs here -->

```
Paste logs here
```

## 🖥️ Environment
<!-- Please complete the following information -->

- **OS**: [e.g. Windows 11, Ubuntu 22.04, macOS 14]
- **Python Version**: [e.g. 3.11.9, 3.12.1]
- **Bot Version**: [e.g. 1.0.0]
- **Installation Method**: [e.g. pip, Poetry, Docker]
- **Database**: [e.g. PostgreSQL 15, SQLite]

## 📸 Screenshots
<!-- If applicable, add screenshots to help explain your problem -->



## 🔧 Configuration
<!-- Relevant parts of your config (REMOVE SENSITIVE DATA!) -->

```yaml
# Example: config.yaml settings that might be relevant
```

## 🎯 Arbitrage Level
<!-- Which arbitrage level were you using? -->

- [ ] Boost ($0.50-$3)
- [ ] Standard ($3-$10)
- [ ] Medium ($10-$30)
- [ ] Advanced ($30-$100)
- [ ] Pro ($100+)
- [ ] N/A

## 🎮 Game
<!-- Which game were you trading? -->

- [ ] CS:GO/CS2
- [ ] Dota 2
- [ ] TF2
- [ ] Rust
- [ ] All games

## 📝 Additional Context
<!-- Add any other context about the problem here -->



## ✅ Checklist
<!-- Please check the following -->

- [ ] I have searched existing issues
- [ ] I have read the documentation
- [ ] I have included all relevant information
- [ ] I have removed sensitive data (API keys, tokens)
- [ ] I can reproduce this bug consistently

---

**Helpful Commands for Debugging**:
```bash
# Enable debug logging
export DEBUG=1

# Check bot status
python -m src --dry-run

# Run diagnostics
python scripts/diagnostics.py

# View logs
tail -f logs/bot.log
```

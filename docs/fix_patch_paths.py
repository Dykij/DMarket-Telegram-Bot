"""Script to fix patch paths in test_dmarket_status.py."""

import re
from pathlib import Path

# Read file
file_path = Path("tests/telegram_bot/handlers/test_dmarket_status.py")
text = file_path.read_text(encoding="utf-8")

# Fix all patch paths
old_pattern = r'patch\("src\.dmarket\.arbitrage_scanner\.check_user_balance"\)'
new_pattern = 'patch("src.telegram_bot.handlers.dmarket_status.check_user_balance")'

text_fixed = re.sub(old_pattern, new_pattern, text)

# Count fixes
count = text.count("src.dmarket.arbitrage_scanner.check_user_balance")

# Write back
file_path.write_text(text_fixed, encoding="utf-8")

print(f"✅ Fixed {count} patch paths")
print("   Old: src.dmarket.arbitrage_scanner.check_user_balance")
print("   New: src.telegram_bot.handlers.dmarket_status.check_user_balance")

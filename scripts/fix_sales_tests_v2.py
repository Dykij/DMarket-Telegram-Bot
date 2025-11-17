"""Скрипт V2 для автоматического исправления тестов SalesAnalyzer."""

import re

test_file = (
    r"d:\Dmarket\DMarket-Telegram-Bot\DMarket-Telegram-Bot"
    r"\tests\dmarket\test_arbitrage_sales_analysis.py"
)

with open(test_file, encoding="utf-8") as f:
    content = f.read()

# Паттерн: все вхождения get_sales_history.return_value
pattern = (
    r"mock_dmarket_api\.get_sales_history\.return_value = "
    r'(sample_\w+_sales_data|\{"sales": \[\]\})'
)


def replace_mock(match):
    data = match.group(1)
    if data == '{"sales": []}':
        return """# Мокаем get_market_items
    mock_dmarket_api.get_market_items.return_value = {"items": []}"""
    return f"""# Мокаем get_market_items и _request
    mock_dmarket_api.get_market_items.return_value = {{
        "items": [{{"itemId": "item_1", "title": "Test"}}]
    }}
    mock_dmarket_api._request.return_value = {data}"""


content = re.sub(pattern, replace_mock, content)

with open(test_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Исправлено! Проверьте: {test_file}")

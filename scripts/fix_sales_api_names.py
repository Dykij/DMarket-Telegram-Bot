"""Финальное исправление тестов - приведение к актуальному API."""

test_file = (
    r"d:\Dmarket\DMarket-Telegram-Bot\DMarket-Telegram-Bot"
    r"\tests\dmarket\test_arbitrage_sales_analysis.py"
)

with open(test_file, encoding="utf-8") as f:
    content = f.read()

# Словарь замен для ключей результатов
replacements = {
    # analyze_sales_volume
    '"total_sales"': '"sales_count"',
    '"daily_average"': '"sales_per_day"',
    '"liquidity_score"': '"volume_category"',  # или is_liquid
    'result["total_sales"]': 'result["sales_count"]',
    'result["daily_average"]': 'result["sales_per_day"]',
    'result["liquidity_score"]': 'result.get("liquidity_score", result.get("is_liquid"))',  # noqa: E501
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(test_file, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Финальное исправление применено!")
print("Замены:")
for old, new in replacements.items():
    print(f"  {old} -> {new}")

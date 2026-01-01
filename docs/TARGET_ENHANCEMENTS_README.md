# Расширенная система таргетов (Buy Orders) - Январь 2026

## 📋 Обзор улучшений

Этот документ описывает новые возможности системы управления таргетами (buy orders) на DMarket, добавленные в январе 2026 года.

## 🆕 Новые возможности

### 1. **Пакетное создание ордеров** (`create_batch_target`)
Создание одного ордера на несколько предметов.

**Файлы:**
- `src/dmarket/targets/batch_operations.py`
- `src/dmarket/models/target_enhancements.py` (BatchTargetItem)

**Примеры:**
```python
from src.dmarket.targets.batch_operations import create_batch_target
from src.dmarket.models.target_enhancements import BatchTargetItem

items = [
    BatchTargetItem(title="AK-47 | Redline (FT)", attrs={"floatPartValue": "0.25"}),
    BatchTargetItem(title="AK-47 | Redline (MW)", attrs={"floatPartValue": "0.12"}),
]

result = await create_batch_target(
    api_client=api,
    game="csgo",
    items=items,
    price=70.80,  # Общая цена
    total_amount=2
)
```

**Выгоды:**
- Экономия API запросов (1 вместо N)
- Быстрее создание множественных ордеров
- Автоматическое распределение цены

---

### 2. **Обнаружение существующих ордеров** (`detect_existing_orders`)
Проверка наличия ордеров до создания новых.

**Файлы:**
- `src/dmarket/targets/batch_operations.py`
- `src/dmarket/models/target_enhancements.py` (ExistingOrderInfo)

**Примеры:**
```python
from src.dmarket.targets.batch_operations import detect_existing_orders

info = await detect_existing_orders(
    api_client=api,
    game="csgo",
    title="AK-47 | Redline (Field-Tested)",
    user_id="12345"
)

if info.has_user_order:
    print(f"У вас уже есть ордер по цене ${info.user_order['price']}")

print(f"Всего ордеров: {info.total_orders}")
print(f"Лучшая цена: ${info.best_price}")
print(f"Рекомендуемая: ${info.recommended_price}")
```

**Выгоды:**
- Предотвращение дубликатов
- Анализ конкуренции
- Рекомендации по ценам

---

### 3. **Фильтры по стикерам (CS:GO)** (`StickerFilter`)
Создание ордеров с требованиями к стикерам.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import StickerFilter

# Конкретный стикер
filter1 = StickerFilter(
    sticker_names=["iBUYPOWER | Katowice 2014 (Holo)"],
    min_stickers=1
)

# Категория + холо
filter2 = StickerFilter(
    sticker_categories=["Katowice 2014"],
    min_stickers=3,
    holo=True
)
```

**Выгоды:**
- Точная покупка нужных скинов
- Экономия на комиссиях
- Важно для коллекционеров

---

### 4. **Фильтры по редкости (Dota 2, TF2)** (`RarityFilter`)
Создание ордеров с требованиями к редкости.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import RarityFilter, RarityLevel

# Только Arcana
filter1 = RarityFilter(rarity=RarityLevel.ARCANA)

# От Mythical до Immortal
filter2 = RarityFilter(
    min_rarity_index=3,  # Mythical
    max_rarity_index=5   # Immortal
)
```

**Выгоды:**
- Защита от покупки не той редкости
- Важно для Dota 2 трейдеров

---

### 5. **Конфигурация автоперебития** (`TargetOverbidConfig`)
Автоматическое повышение цены при конкуренции.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import TargetOverbidConfig

config = TargetOverbidConfig(
    enabled=True,
    max_overbid_percent=2.0,      # Макс +2% от начальной
    min_price_gap=0.01,           # Минимум $0.01 разница
    check_interval_seconds=300,    # Проверка каждые 5 мин
    max_overbids_per_day=10       # Макс 10 перебитий в день
)
```

**Выгоды:**
- Ордер всегда первый в очереди
- Защита от "войн перебития"
- Автоматизация мониторинга

---

### 6. **Мониторинг диапазона цен** (`PriceRangeConfig`)
Отслеживание выхода цены за пределы диапазона.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import (
    PriceRangeConfig,
    PriceRangeAction
)

# Отменить если цена выходит из диапазона
config1 = PriceRangeConfig(
    min_price=8.0,
    max_price=15.0,
    action_on_breach=PriceRangeAction.CANCEL
)

# Автокорректировка цены
config2 = PriceRangeConfig(
    min_price=8.0,
    max_price=15.0,
    action_on_breach=PriceRangeAction.ADJUST
)
```

**Выгоды:**
- Защита от переплаты
- Адаптация к рынку
- Контроль рисков

---

### 7. **Контроль лимитов перевыставлений** (`RelistLimitConfig`)
Ограничение количества перевыставлений ордера.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket/models/target_enhancements import (
    RelistLimitConfig,
    RelistAction
)

config = RelistLimitConfig(
    max_relists=5,                    # Макс 5 перевыставлений
    reset_period_hours=24,            # Сброс каждые 24ч
    action_on_limit=RelistAction.PAUSE  # Пауза при лимите
)
```

**Выгоды:**
- Контроль расходов
- Выход из невыгодной конкуренции
- Прозрачность истории

---

### 8. **Дефолтные параметры** (`TargetDefaults`)
Общие настройки для всех ордеров.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import TargetDefaults

defaults = TargetDefaults(
    default_amount=1,
    default_price_strategy="market_minus_5_percent",
    default_overbid_config=TargetOverbidConfig(enabled=True),
    default_max_conditions=10
)

manager = TargetManager(api_client=api, defaults=defaults)
```

**Выгоды:**
- Меньше кода
- Единообразие настроек
- Легко менять стратегию

---

### 9. **Проверка количества условий** (`validate_target_conditions`)
Валидация лимитов DMarket API.

**Файлы:**
- `src/dmarket/targets/enhanced_validators.py`

**Примеры:**
```python
from src.dmarket.targets.enhanced_validators import validate_target_conditions

target = {
    "Attrs": {"floatPartValue": "0.15", "paintSeed": [1, 2, 3]},
    "stickerFilter": StickerFilter(...),
    "rarityFilter": RarityFilter(...)
}

is_valid, message, suggestions = validate_target_conditions(target)
if not is_valid:
    print(message)  # "Too many conditions: 12/10"
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

**Выгоды:**
- Предотвращение ошибок API
- Подсказки по оптимизации
- Экономия запросов

---

### 10. **Расширенные сообщения об ошибках** (`TargetOperationResult`)
Детальные результаты операций.

**Файлы:**
- `src/dmarket/models/target_enhancements.py`

**Примеры:**
```python
from src.dmarket.models.target_enhancements import TargetOperationResult

result = await manager.create_target(...)

if not result.success:
    print(result.message)      # Краткое: "Price too low"
    print(result.reason)       # Детально: "Price $4.50 is below minimum $5.00"
    print(result.error_code)   # Код: "PRICE_TOO_LOW"

    for suggestion in result.suggestions:
        print(f"💡 {suggestion}")  # "Set price to at least $5.00"
```

**Выгоды:**
- Понятные ошибки
- Конкретные действия
- Лучший UX

---

## 📁 Структура файлов

```
src/dmarket/
├── models/
│   ├── market_models.py (существующий)
│   └── target_enhancements.py (НОВЫЙ) - все новые модели
├── targets/
│   ├── manager.py (существующий)
│   ├── validators.py (существующий)
│   ├── competition.py (существующий)
│   ├── enhanced_validators.py (НОВЫЙ) - расширенные валидаторы
│   └── batch_operations.py (НОВЫЙ) - пакетные операции

tests/dmarket/targets/
├── test_batch_operations.py (TODO)
├── test_enhanced_validators.py (TODO)
├── test_sticker_filters.py (TODO)
├── test_rarity_filters.py (TODO)
└── test_target_enhancements.py (TODO)
```

## 📚 Документация

- `docs/DMARKET_API_FULL_SPEC.md` - полная спецификация DMarket API
- `docs/ARBITRAGE.md` - руководство по арбитражу и таргетам

## 🧪 Тестирование

Создать тесты для новых функций:

```bash
pytest tests/dmarket/targets/test_batch_operations.py -v
pytest tests/dmarket/targets/test_enhanced_validators.py -v
```

## 🔄 Миграция

Существующий код продолжит работать без изменений. Новые функции опциональны.

### До:
```python
# Старый способ - все еще работает
await manager.create_target("csgo", "AK-47 | Redline (FT)", 10.00)
```

### После (с новыми возможностями):
```python
# Новый способ - с расширенными функциями
from src.dmarket.models.target_enhancements import StickerFilter

result = await manager.create_target(
    game="csgo",
    title="AK-47 | Redline (FT)",
    price=10.00,
    sticker_filter=StickerFilter(holo=True, min_stickers=3)
)

if result.success:
    print(f"✅ {result.reason}")
else:
    print(f"❌ {result.reason}")
    for suggestion in result.suggestions:
        print(f"  💡 {suggestion}")
```

## ⚠️ Важные заметки

1. **API Лимиты**: DMarket ограничивает количество условий в ордере (обычно 10)
2. **Стикеры**: Только для CS:GO
3. **Редкость**: Только для Dota 2 и TF2
4. **Цены**: Всегда в центах в API, в долларах в наших функциях
5. **Batch**: Максимум 100 предметов в одном batch запросе

## 🚀 Следующие шаги

1. ✅ Создать базовые модели и валидаторы
2. ⏳ Добавить поддержку в TargetManager
3. ⏳ Создать контроллеры перебития и перевыставлений
4. ⏳ Написать тесты
5. ⏳ Обновить документацию
6. ⏳ Создать примеры использования

---

**Версия**: 1.0.0
**Дата**: 1 января 2026 г.
**Автор**: DMarket Telegram Bot Team

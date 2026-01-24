# 🎓 Учебные материалы для курса Deep Learning

**Для студентов курса**: [deep_learning_pytorch](https://github.com/FUlyankin/deep_learning_pytorch)

Этот репозиторий (DMarket-Telegram-Bot) может быть использован как практическая база для изучения deep learning на реальном production проекте.

---

## 🚀 Быстрый старт для студентов

### Шаг 1: Клонирование и настройка

```bash
# Клонировать репозиторий
git clone https://github.com/Dykij/DMarket-Telegram-Bot.git
cd DMarket-Telegram-Bot

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Установить PyTorch (для заданий курса)
pip install torch torchvision torchaudio
```

### Шаг 2: Конфигурация для учебных целей

```bash
# Создать .env файл из шаблона
cp .env.example .env

# Отредактировать .env (используйте demo-режим для начала)
# DMARKET_PUBLIC_KEY=demo
# DMARKET_SECRET_KEY=demo
# TELEGRAM_BOT_TOKEN=optional_for_ml_tasks
```

### Шаг 3: Запуск тестов (проверка установки)

```bash
# Запустить только ML тесты (быстро)
pytest tests/ml/ -v

# Запустить все тесты (медленно, ~5 минут)
pytest tests/ -v

# Запустить с coverage
pytest tests/ml/ --cov=src/ml --cov-report=html
```

### Шаг 4: Изучить архитектуру ML системы

```bash
# Открыть документацию
cat docs/ML_AI_GUIDE.md

# Посмотреть структуру ML модулей
tree src/ml/
```

---

## 📚 Учебные задания по неделям

### Неделя 1-2: Знакомство с проектом

**Задание**: Изучить архитектуру бота и ML pipeline

**Файлы для изучения**:
- `README.md` - общий обзор проекта
- `docs/ARCHITECTURE.md` - архитектура
- `src/ml/enhanced_predictor.py` - ансамбль моделей
- `src/ml/feature_extractor.py` - feature engineering

**Вопросы для самопроверки**:
1. Сколько признаков извлекается для каждого предмета?
2. Какие модели входят в ансамбль?
3. Как реализована async обработка в ML pipeline?

**Дедлайн**: Не требуется (ознакомительное)

---

## 💡 Основные возможности для обучения

### 1. Production ML Infrastructure
- Async/await паттерны
- Feature engineering (32 признака)
- Model ensemble (RF + XGBoost + GB)
- Real-time inference

### 2. Testing (7654+ тестов)
- Unit tests для ML кода
- Property-based testing (Hypothesis)
- Integration tests
- VCR.py для API mocking

### 3. Data Pipeline
- ETL процессы
- Data validation (Pydantic)
- Batch processing
- Streaming data

### 4. Deployment
- Docker multi-stage build
- PostgreSQL + Redis
- Monitoring (Prometheus)
- Structured logging

---

## 📖 Документация

Основные документы для изучения:

1. **[DEEP_LEARNING_COURSE_INTEGRATION.md](../docs/DEEP_LEARNING_COURSE_INTEGRATION.md)** ⭐
   - Полный анализ применимости бота для курса
   - 7 способов использования в обучении
   - Интеграция в учебный план
   - Примеры заданий

2. **[ML_AI_GUIDE.md](../docs/ML_AI_GUIDE.md)**
   - Архитектура ML системы
   - Feature engineering
   - Model training
   - Best practices

3. **[ARCHITECTURE.md](../docs/ARCHITECTURE.md)**
   - Общая архитектура проекта
   - Data flow
   - Модули и зависимости

4. **[TESTING_COMPLETE_GUIDE.md](../docs/TESTING_COMPLETE_GUIDE.md)**
   - Как тестировать ML код
   - Примеры тестов
   - Coverage metrics

---

## 🛠️ Структура учебных материалов

```
educational_materials/
├── README.md                    # Этот файл
├── assignments/                 # Шаблоны заданий
│   ├── week11_lstm_template.py
│   ├── week12_seq2seq_template.py
│   └── final_project_template.py
├── notebooks/                   # Jupyter notebooks
│   ├── 01_intro_to_bot.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_sklearn_to_pytorch.ipynb
└── projects/                    # Примеры проектов
    ├── price_prediction/
    ├── time_series_forecasting/
    ├── nlp_item_analysis/
    └── rl_trading_agent/
```

---

## 🎯 Предлагаемые темы для проектов

### 1. Price Prediction с PyTorch
Заменить scikit-learn модель на нейросеть

### 2. Time Series Forecasting с LSTM
Прогнозирование цен на N дней вперед

### 3. NLP для названий предметов
BERT embeddings для классификации

### 4. Reinforcement Learning Trading Agent
DQN/PPO для автоматической торговли

---

## 🆘 FAQ

**Q: Нужны ли реальные API ключи?**  
A: Нет, можно использовать demo-режим

**Q: Можно ли использовать Google Colab?**  
A: Да, полностью совместимо

**Q: Сколько времени на обучение моделей?**  
A: LSTM: 10-30 минут (GPU), Transformer: 30-60 минут (GPU)

**Q: Как задать вопрос?**  
A: GitHub Issues с тегом `[educational]` или Telegram чат курса

---

## 📞 Поддержка

**Курс deep_learning_pytorch**:
- 💬 Telegram: https://t.me/+BvoZ8PGnkmw5Mjcy
- 📧 Email: filfonul@gmail.com

**DMarket-Telegram-Bot**:
- 🐛 Issues: https://github.com/Dykij/DMarket-Telegram-Bot/issues
- 📖 Docs: `docs/`

---

**Удачи в обучении! 🚀**

_Если проект помог - поставьте ⭐ на GitHub!_

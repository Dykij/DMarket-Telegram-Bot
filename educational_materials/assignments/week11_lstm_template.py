"""
Задание для курса deep_learning_pytorch: Week 11 - LSTM для прогнозирования цен

Цель: Реализовать LSTM модель на PyTorch для прогнозирования цен игровых предметов
      и сравнить результаты с baseline (scikit-learn RandomForest из бота).

Дедлайн: 2 недели
Баллы: 100 (из них 20 бонусных)

Критерии оценки:
- [ ] Модель реализована и обучена (30 баллов)
- [ ] MAE < 0.5 USD на тестовой выборке (20 баллов)
- [ ] Написаны unit-тесты (20 баллов)
- [ ] Документация в README.md (15 баллов)
- [ ] Визуализация результатов (15 баллов)
- [ ] БОНУС: MAE < 0.3 USD (10 баллов)
- [ ] БОНУС: Inference latency < 30ms (10 баллов)
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, List
import asyncio

# Импорты из бота (для сравнения)
from src.ml.enhanced_predictor import EnhancedPricePredictor
from src.ml.feature_extractor import EnhancedFeatureExtractor
from src.dmarket.dmarket_api import DMarketAPI


# ============================================================================
# ЗАДАНИЕ 1: Реализовать Dataset для временных рядов (15 баллов)
# ============================================================================

class PriceTimeSeriesDataset(Dataset):
    """Dataset для последовательностей цен.
    
    Args:
        data: Массив цен (N, features)
        window_size: Размер окна для LSTM (default: 7 дней)
        horizon: На сколько дней вперед прогнозировать (default: 1)
    
    Returns:
        X: (batch, seq_len, features) - входная последовательность
        y: (batch, 1) - целевая цена
    """
    
    def __init__(
        self,
        data: np.ndarray,
        window_size: int = 7,
        horizon: int = 1
    ):
        self.data = data
        self.window_size = window_size
        self.horizon = horizon
        
        # TODO: Реализовать инициализацию
        # Подсказка: нужно создать последовательности
        # Пример: если data = [1,2,3,4,5] и window_size=3, horizon=1
        # то X = [[1,2,3], [2,3,4]], y = [4, 5]
        pass
    
    def __len__(self) -> int:
        # TODO: Вернуть количество последовательностей
        pass
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # TODO: Вернуть пару (X, y) для индекса idx
        pass


# ============================================================================
# ЗАДАНИЕ 2: Реализовать LSTM модель (30 баллов)
# ============================================================================

class PriceLSTM(nn.Module):
    """LSTM модель для прогнозирования цен.
    
    Архитектура:
        - LSTM layers (1-3 слоя)
        - Dropout для регуляризации
        - Fully connected layer на выходе
    
    Args:
        input_size: Количество признаков (default: 32)
        hidden_size: Размер скрытого состояния (default: 64)
        num_layers: Количество LSTM слоев (default: 2)
        dropout: Dropout probability (default: 0.2)
    """
    
    def __init__(
        self,
        input_size: int = 32,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # TODO: Реализовать архитектуру
        # Подсказка: используйте nn.LSTM, nn.Dropout, nn.Linear
        
        # Пример структуры:
        # self.lstm = nn.LSTM(...)
        # self.dropout = nn.Dropout(...)
        # self.fc = nn.Linear(...)
        pass
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input tensor (batch, seq_len, input_size)
        
        Returns:
            Output tensor (batch, 1) - предсказанная цена
        """
        # TODO: Реализовать forward pass
        # Подсказка: LSTM возвращает (output, (h_n, c_n))
        # Нужно использовать последний hidden state
        pass
    
    def init_hidden(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Инициализировать скрытое состояние LSTM."""
        # TODO: Вернуть (h_0, c_0) с нулями
        pass


# ============================================================================
# ЗАДАНИЕ 3: Реализовать training loop (25 баллов)
# ============================================================================

async def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 50,
    learning_rate: float = 0.001,
    device: str = "cpu"
) -> dict:
    """Обучить LSTM модель.
    
    Args:
        model: LSTM модель
        train_loader: DataLoader для обучения
        val_loader: DataLoader для валидации
        epochs: Количество эпох
        learning_rate: Learning rate
        device: 'cpu' или 'cuda'
    
    Returns:
        dict с метриками: train_loss, val_loss, best_val_mae
    """
    
    # Перенести модель на device
    model = model.to(device)
    
    # TODO: Определить loss function и optimizer
    # Подсказка: для регрессии используйте nn.MSELoss() или nn.L1Loss()
    criterion = None  # TODO
    optimizer = None  # TODO
    
    # Для сохранения лучшей модели
    best_val_mae = float('inf')
    best_model_state = None
    
    # Метрики
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        # ============ Training ============
        model.train()
        train_loss = 0.0
        
        for batch_idx, (X_batch, y_batch) in enumerate(train_loader):
            # TODO: Реализовать training step
            # 1. Перенести данные на device
            # 2. Forward pass
            # 3. Вычислить loss
            # 4. Backward pass
            # 5. Optimizer step
            pass
        
        # ============ Validation ============
        model.eval()
        val_loss = 0.0
        val_mae = 0.0
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                # TODO: Реализовать validation step
                # 1. Forward pass
                # 2. Вычислить loss и MAE
                pass
        
        # Сохранить лучшую модель
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            best_model_state = model.state_dict()
        
        # Логирование (каждые 5 эпох)
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val MAE: {val_mae:.4f}")
    
    # Загрузить лучшую модель
    model.load_state_dict(best_model_state)
    
    return {
        "train_losses": train_losses,
        "val_losses": val_losses,
        "best_val_mae": best_val_mae
    }


# ============================================================================
# ЗАДАНИЕ 4: Сравнение с baseline (10 баллов)
# ============================================================================

async def compare_with_baseline(
    lstm_model: nn.Module,
    test_data: np.ndarray,
    test_labels: np.ndarray
) -> dict:
    """Сравнить LSTM с baseline (scikit-learn из бота).
    
    Args:
        lstm_model: Обученная LSTM модель
        test_data: Тестовые данные
        test_labels: Истинные значения
    
    Returns:
        dict с результатами сравнения
    """
    
    # 1. Предсказания LSTM
    lstm_model.eval()
    with torch.no_grad():
        # TODO: Получить предсказания LSTM
        lstm_predictions = None  # TODO
    
    # 2. Предсказания baseline
    baseline = EnhancedPricePredictor()
    # TODO: Получить предсказания baseline
    baseline_predictions = None  # TODO
    
    # 3. Вычислить метрики
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    results = {
        "lstm": {
            "mae": None,  # TODO
            "rmse": None,  # TODO
            "r2": None,  # TODO
        },
        "baseline": {
            "mae": None,  # TODO
            "rmse": None,  # TODO
            "r2": None,  # TODO
        }
    }
    
    # 4. Вычислить улучшение
    results["improvement_percent"] = None  # TODO
    
    return results


# ============================================================================
# ЗАДАНИЕ 5: Визуализация (15 баллов)
# ============================================================================

def visualize_results(
    true_prices: np.ndarray,
    lstm_predictions: np.ndarray,
    baseline_predictions: np.ndarray,
    save_path: str = "results.png"
) -> None:
    """Визуализировать результаты прогнозирования.
    
    Создать график с 3 линиями:
    1. Истинные цены (черная)
    2. LSTM предсказания (синяя)
    3. Baseline предсказания (красная)
    
    Args:
        true_prices: Истинные цены
        lstm_predictions: Предсказания LSTM
        baseline_predictions: Предсказания baseline
        save_path: Путь для сохранения графика
    """
    import matplotlib.pyplot as plt
    
    # TODO: Создать график
    # Подсказка: используйте plt.plot(), plt.legend(), plt.savefig()
    pass


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

async def main():
    """Главная функция для выполнения задания."""
    
    print("=" * 80)
    print("LSTM Price Prediction - Week 11 Assignment")
    print("=" * 80)
    
    # 1. Загрузить данные
    print("\n[1/6] Загрузка данных...")
    # TODO: Загрузить данные из DMarket API или использовать demo-данные
    
    # 2. Подготовить датасет
    print("\n[2/6] Подготовка датасета...")
    # TODO: Создать train/val/test split
    
    # 3. Создать модель
    print("\n[3/6] Создание модели...")
    model = PriceLSTM(
        input_size=32,
        hidden_size=64,
        num_layers=2,
        dropout=0.2
    )
    print(f"Параметров в модели: {sum(p.numel() for p in model.parameters())}")
    
    # 4. Обучить модель
    print("\n[4/6] Обучение модели...")
    # TODO: Вызвать train_model()
    
    # 5. Сравнить с baseline
    print("\n[5/6] Сравнение с baseline...")
    # TODO: Вызвать compare_with_baseline()
    
    # 6. Визуализация
    print("\n[6/6] Визуализация результатов...")
    # TODO: Вызвать visualize_results()
    
    print("\n" + "=" * 80)
    print("Задание выполнено!")
    print("=" * 80)
    
    # TODO: Вывести финальные метрики
    print("\nФинальные метрики:")
    print("  LSTM MAE: ?.??? USD")
    print("  Baseline MAE: ?.??? USD")
    print("  Improvement: ??.?%")
    
    # TODO: Проверить критерии оценки
    print("\nКритерии оценки:")
    print("  [?] Модель обучена: ??? баллов")
    print("  [?] MAE < 0.5: ??? баллов")
    print("  [?] Тесты написаны: ??? баллов")
    print("  [?] Документация: ??? баллов")
    print("  [?] Визуализация: ??? баллов")
    print("\n  ИТОГО: ???/100 баллов")


if __name__ == "__main__":
    # Запустить задание
    asyncio.run(main())

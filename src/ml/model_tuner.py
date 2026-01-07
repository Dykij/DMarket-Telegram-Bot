"""Модуль для автоматической настройки и оптимизации ML моделей.

Реализует лучшие практики scikit-learn:
1. Cross-Validation (KFold, TimeSeriesSplit)
2. GridSearchCV для подбора гиперпараметров
3. Pipeline для предотвращения утечки данных
4. Feature Selection с SelectKBest
5. Model Evaluation с несколькими метриками

Основано на официальной документации scikit-learn:
- https://scikit-learn.org/stable/modules/cross_validation.html
- https://scikit-learn.org/stable/modules/grid_search.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import logging
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class CVStrategy(StrEnum):
    """Стратегии кросс-валидации."""

    KFOLD = "kfold"  # Стандартная K-Fold CV
    TIME_SERIES = "time_series"  # TimeSeriesSplit для временных рядов
    STRATIFIED = "stratified"  # StratifiedKFold для классификации


class ScoringMetric(StrEnum):
    """Метрики для оценки моделей."""

    # Регрессия
    MAE = "neg_mean_absolute_error"
    MSE = "neg_mean_squared_error"
    RMSE = "neg_root_mean_squared_error"
    R2 = "r2"

    # Классификация
    ACCURACY = "accuracy"
    F1 = "f1"
    PRECISION = "precision"
    RECALL = "recall"


@dataclass
class TuningResult:
    """Результат настройки гиперпараметров."""

    best_params: dict[str, Any]
    best_score: float
    cv_results: dict[str, Any]
    best_estimator: Any

    # Метаданные
    model_name: str
    scoring: str
    cv_folds: int
    total_fits: int
    tuning_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> str:
        """Получить краткую сводку результатов."""
        return (
            f"Model: {self.model_name}\n"
            f"Best Score: {self.best_score:.4f}\n"
            f"Best Params: {self.best_params}\n"
            f"CV Folds: {self.cv_folds}\n"
            f"Total Fits: {self.total_fits}\n"
            f"Time: {self.tuning_time_seconds:.1f}s"
        )


@dataclass
class EvaluationResult:
    """Результат оценки модели."""

    train_scores: list[float]
    test_scores: list[float]
    mean_train_score: float
    mean_test_score: float
    std_train_score: float
    std_test_score: float

    # Дополнительные метрики
    feature_importances: dict[str, float] | None = None
    overfitting_ratio: float = 0.0  # train/test score ratio

    def is_overfitting(self, threshold: float = 0.15) -> bool:
        """Проверить, есть ли переобучение."""
        if self.mean_train_score == 0:
            return False
        ratio = abs(self.mean_train_score - self.mean_test_score) / abs(self.mean_train_score)
        return ratio > threshold


class ModelTuner:
    """Класс для настройки и оптимизации ML моделей.
    
    Использует лучшие практики scikit-learn:
    - Pipeline для безопасной предобработки
    - GridSearchCV/RandomizedSearchCV для подбора параметров
    - Cross-validation для оценки качества
    
    Example:
        >>> tuner = ModelTuner()
        >>> result = tuner.tune_random_forest(X_train, y_train)
        >>> print(result.best_params)
    """

    # Предустановленные грids для разных моделей
    RANDOM_FOREST_PARAM_GRID = {
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, 15, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }

    GRADIENT_BOOSTING_PARAM_GRID = {
        "n_estimators": [50, 100, 150],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1, 0.2],
        "min_samples_split": [2, 5, 10],
    }

    XGBOOST_PARAM_GRID = {
        "n_estimators": [50, 100, 200],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.8, 0.9, 1.0],
        "colsample_bytree": [0.8, 0.9, 1.0],
    }

    RIDGE_PARAM_GRID = {
        "alpha": [0.1, 0.5, 1.0, 5.0, 10.0],
    }

    def __init__(
        self,
        cv_strategy: CVStrategy = CVStrategy.TIME_SERIES,
        cv_folds: int = 5,
        scoring: ScoringMetric = ScoringMetric.MAE,
        n_jobs: int = -1,
        random_state: int = 42,
    ):
        """Инициализация тюнера.
        
        Args:
            cv_strategy: Стратегия кросс-валидации
            cv_folds: Количество фолдов
            scoring: Метрика для оптимизации
            n_jobs: Количество параллельных потоков (-1 = все)
            random_state: Seed для воспроизводимости
        """
        self.cv_strategy = cv_strategy
        self.cv_folds = cv_folds
        self.scoring = scoring
        self.n_jobs = n_jobs
        self.random_state = random_state

        self._sklearn_available = self._check_sklearn()

    def _check_sklearn(self) -> bool:
        """Проверить доступность sklearn."""
        try:
            import sklearn
            return True
        except ImportError:
            logger.warning("scikit-learn not available")
            return False

    def _get_cv_splitter(self, n_samples: int) -> Any:
        """Получить splitter для кросс-валидации."""
        if not self._sklearn_available:
            return None

        from sklearn.model_selection import (
            KFold,
            StratifiedKFold,
            TimeSeriesSplit,
        )

        if self.cv_strategy == CVStrategy.TIME_SERIES:
            return TimeSeriesSplit(n_splits=self.cv_folds)
        elif self.cv_strategy == CVStrategy.STRATIFIED:
            return StratifiedKFold(
                n_splits=self.cv_folds,
                shuffle=True,
                random_state=self.random_state,
            )
        else:
            return KFold(
                n_splits=self.cv_folds,
                shuffle=True,
                random_state=self.random_state,
            )

    def create_pipeline(
        self,
        model: Any,
        use_scaling: bool = True,
        use_feature_selection: bool = False,
        n_features_to_select: int | None = None,
    ) -> Any:
        """Создать Pipeline для предобработки и модели.
        
        Pipeline предотвращает утечку данных при кросс-валидации,
        применяя preprocessing только к training data в каждом fold.
        
        Args:
            model: ML модель
            use_scaling: Использовать StandardScaler
            use_feature_selection: Использовать SelectKBest
            n_features_to_select: Количество признаков для отбора
            
        Returns:
            sklearn.pipeline.Pipeline
        """
        if not self._sklearn_available:
            return model

        from sklearn.feature_selection import SelectKBest, f_regression
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        steps = []

        # 1. Imputer для обработки NaN
        steps.append(("imputer", SimpleImputer(strategy="median")))

        # 2. Scaling (опционально)
        if use_scaling:
            steps.append(("scaler", StandardScaler()))

        # 3. Feature Selection (опционально)
        if use_feature_selection and n_features_to_select:
            steps.append((
                "feature_selection",
                SelectKBest(f_regression, k=n_features_to_select)
            ))

        # 4. Модель
        steps.append(("model", model))

        return Pipeline(steps)

    def tune_random_forest(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: dict[str, list] | None = None,
        use_randomized: bool = False,
        n_iter: int = 50,
    ) -> TuningResult:
        """Настроить RandomForestRegressor.
        
        Args:
            X: Признаки
            y: Целевая переменная
            param_grid: Сетка параметров (по умолчанию предустановленная)
            use_randomized: Использовать RandomizedSearchCV (быстрее)
            n_iter: Количество итераций для RandomizedSearchCV
            
        Returns:
            TuningResult с лучшими параметрами
        """
        if not self._sklearn_available:
            return self._fallback_result("RandomForest")

        from sklearn.ensemble import RandomForestRegressor

        model = RandomForestRegressor(random_state=self.random_state, n_jobs=-1)
        grid = param_grid or self.RANDOM_FOREST_PARAM_GRID

        return self._run_grid_search(
            model=model,
            param_grid=grid,
            X=X,
            y=y,
            model_name="RandomForestRegressor",
            use_randomized=use_randomized,
            n_iter=n_iter,
        )

    def tune_gradient_boosting(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: dict[str, list] | None = None,
        use_randomized: bool = False,
        n_iter: int = 50,
    ) -> TuningResult:
        """Настроить GradientBoostingRegressor."""
        if not self._sklearn_available:
            return self._fallback_result("GradientBoosting")

        from sklearn.ensemble import GradientBoostingRegressor

        model = GradientBoostingRegressor(random_state=self.random_state)
        grid = param_grid or self.GRADIENT_BOOSTING_PARAM_GRID

        return self._run_grid_search(
            model=model,
            param_grid=grid,
            X=X,
            y=y,
            model_name="GradientBoostingRegressor",
            use_randomized=use_randomized,
            n_iter=n_iter,
        )

    def tune_xgboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: dict[str, list] | None = None,
        use_randomized: bool = True,
        n_iter: int = 50,
    ) -> TuningResult:
        """Настроить XGBRegressor (если доступен)."""
        try:
            from xgboost import XGBRegressor
        except ImportError:
            logger.warning("XGBoost not available")
            return self._fallback_result("XGBoost")

        model = XGBRegressor(
            random_state=self.random_state,
            n_jobs=-1,
            objective="reg:squarederror",
        )
        grid = param_grid or self.XGBOOST_PARAM_GRID

        return self._run_grid_search(
            model=model,
            param_grid=grid,
            X=X,
            y=y,
            model_name="XGBRegressor",
            use_randomized=use_randomized,
            n_iter=n_iter,
        )

    def tune_ridge(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: dict[str, list] | None = None,
    ) -> TuningResult:
        """Настроить Ridge Regression."""
        if not self._sklearn_available:
            return self._fallback_result("Ridge")

        from sklearn.linear_model import Ridge

        model = Ridge()
        grid = param_grid or self.RIDGE_PARAM_GRID

        return self._run_grid_search(
            model=model,
            param_grid=grid,
            X=X,
            y=y,
            model_name="Ridge",
            use_randomized=False,
            n_iter=10,
        )

    def _run_grid_search(
        self,
        model: Any,
        param_grid: dict[str, list],
        X: np.ndarray,
        y: np.ndarray,
        model_name: str,
        use_randomized: bool = False,
        n_iter: int = 50,
    ) -> TuningResult:
        """Запустить GridSearchCV или RandomizedSearchCV."""
        import time

        from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

        cv = self._get_cv_splitter(len(X))

        # Создаём pipeline
        pipeline = self.create_pipeline(model)

        # Адаптируем param_grid для pipeline
        pipeline_param_grid = {
            f"model__{k}": v for k, v in param_grid.items()
        }

        start_time = time.time()

        if use_randomized:
            search = RandomizedSearchCV(
                estimator=pipeline,
                param_distributions=pipeline_param_grid,
                n_iter=n_iter,
                cv=cv,
                scoring=self.scoring.value,
                n_jobs=self.n_jobs,
                random_state=self.random_state,
                return_train_score=True,
            )
        else:
            search = GridSearchCV(
                estimator=pipeline,
                param_grid=pipeline_param_grid,
                cv=cv,
                scoring=self.scoring.value,
                n_jobs=self.n_jobs,
                return_train_score=True,
            )

        try:
            search.fit(X, y)
            elapsed = time.time() - start_time

            # Убираем префикс "model__" из параметров
            best_params = {
                k.replace("model__", ""): v
                for k, v in search.best_params_.items()
            }

            return TuningResult(
                best_params=best_params,
                best_score=-search.best_score_ if "neg" in self.scoring.value else search.best_score_,
                cv_results=dict(search.cv_results_),
                best_estimator=search.best_estimator_,
                model_name=model_name,
                scoring=self.scoring.value,
                cv_folds=self.cv_folds,
                total_fits=len(search.cv_results_["mean_test_score"]) * self.cv_folds,
                tuning_time_seconds=elapsed,
            )

        except Exception as e:
            logger.error(f"Grid search failed: {e}")
            return self._fallback_result(model_name)

    def _fallback_result(self, model_name: str) -> TuningResult:
        """Возвращает результат по умолчанию при ошибке."""
        return TuningResult(
            best_params={},
            best_score=0.0,
            cv_results={},
            best_estimator=None,
            model_name=model_name,
            scoring=self.scoring.value,
            cv_folds=self.cv_folds,
            total_fits=0,
            tuning_time_seconds=0.0,
        )

    def evaluate_model(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> EvaluationResult:
        """Оценить модель с кросс-валидацией.
        
        Использует cross_val_score для получения train и test scores
        на каждом fold, что позволяет оценить переобучение.
        
        Args:
            model: Обученная модель или pipeline
            X: Признаки
            y: Целевая переменная
            feature_names: Названия признаков для feature importance
            
        Returns:
            EvaluationResult с метриками
        """
        if not self._sklearn_available:
            return EvaluationResult(
                train_scores=[],
                test_scores=[],
                mean_train_score=0.0,
                mean_test_score=0.0,
                std_train_score=0.0,
                std_test_score=0.0,
            )

        from sklearn.model_selection import cross_validate

        cv = self._get_cv_splitter(len(X))

        results = cross_validate(
            model,
            X,
            y,
            cv=cv,
            scoring=self.scoring.value,
            return_train_score=True,
            n_jobs=self.n_jobs,
        )

        train_scores = results["train_score"].tolist()
        test_scores = results["test_score"].tolist()

        # Feature importances (если доступно)
        feature_importances = None
        if hasattr(model, "feature_importances_") and feature_names:
            importances = model.feature_importances_
            feature_importances = dict(zip(feature_names, importances))
        elif hasattr(model, "named_steps"):
            # Pipeline case
            final_model = model.named_steps.get("model")
            if hasattr(final_model, "feature_importances_") and feature_names:
                importances = final_model.feature_importances_
                feature_importances = dict(zip(feature_names, importances))

        mean_train = float(np.mean(train_scores))
        mean_test = float(np.mean(test_scores))

        return EvaluationResult(
            train_scores=train_scores,
            test_scores=test_scores,
            mean_train_score=abs(mean_train) if "neg" in self.scoring.value else mean_train,
            mean_test_score=abs(mean_test) if "neg" in self.scoring.value else mean_test,
            std_train_score=float(np.std(train_scores)),
            std_test_score=float(np.std(test_scores)),
            feature_importances=feature_importances,
            overfitting_ratio=abs(mean_train - mean_test) / abs(mean_train) if mean_train != 0 else 0.0,
        )

    def compare_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        models: list[str] | None = None,
    ) -> dict[str, EvaluationResult]:
        """Сравнить несколько моделей.
        
        Args:
            X: Признаки
            y: Целевая переменная
            models: Список названий моделей (по умолчанию все)
            
        Returns:
            Dict с результатами для каждой модели
        """
        models = models or ["random_forest", "gradient_boosting", "ridge"]
        results = {}

        model_classes = {
            "random_forest": self._create_random_forest,
            "gradient_boosting": self._create_gradient_boosting,
            "ridge": self._create_ridge,
            "xgboost": self._create_xgboost,
        }

        for model_name in models:
            if model_name not in model_classes:
                continue

            try:
                model = model_classes[model_name]()
                if model is not None:
                    pipeline = self.create_pipeline(model)
                    pipeline.fit(X, y)
                    results[model_name] = self.evaluate_model(pipeline, X, y)
            except Exception as e:
                logger.warning(f"Failed to evaluate {model_name}: {e}")

        return results

    def _create_random_forest(self) -> Any:
        """Создать RandomForest с базовыми параметрами."""
        if not self._sklearn_available:
            return None
        from sklearn.ensemble import RandomForestRegressor
        return RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=self.random_state,
            n_jobs=-1,
        )

    def _create_gradient_boosting(self) -> Any:
        """Создать GradientBoosting с базовыми параметрами."""
        if not self._sklearn_available:
            return None
        from sklearn.ensemble import GradientBoostingRegressor
        return GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.random_state,
        )

    def _create_ridge(self) -> Any:
        """Создать Ridge с базовыми параметрами."""
        if not self._sklearn_available:
            return None
        from sklearn.linear_model import Ridge
        return Ridge(alpha=1.0)

    def _create_xgboost(self) -> Any:
        """Создать XGBoost с базовыми параметрами."""
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=self.random_state,
                n_jobs=-1,
            )
        except ImportError:
            return None


class AutoMLSelector:
    """Автоматический выбор лучшей модели.
    
    Сравнивает несколько моделей, тюнит гиперпараметры
    и выбирает лучшую на основе кросс-валидации.
    
    Example:
        >>> selector = AutoMLSelector()
        >>> best_model, results = selector.select_best_model(X, y)
        >>> print(results.summary())
    """

    def __init__(
        self,
        cv_folds: int = 5,
        scoring: ScoringMetric = ScoringMetric.MAE,
        time_budget_seconds: int = 300,
    ):
        """Инициализация AutoML.
        
        Args:
            cv_folds: Количество фолдов CV
            scoring: Метрика для оптимизации
            time_budget_seconds: Временной бюджет (секунд)
        """
        self.cv_folds = cv_folds
        self.scoring = scoring
        self.time_budget_seconds = time_budget_seconds

        self.tuner = ModelTuner(
            cv_strategy=CVStrategy.TIME_SERIES,
            cv_folds=cv_folds,
            scoring=scoring,
        )

    def select_best_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        include_xgboost: bool = True,
    ) -> tuple[Any, dict[str, TuningResult]]:
        """Выбрать лучшую модель.
        
        Args:
            X: Признаки
            y: Целевая переменная
            include_xgboost: Включить XGBoost в сравнение
            
        Returns:
            Tuple (лучшая модель, dict с результатами всех моделей)
        """
        import time

        results = {}
        start_time = time.time()
        time_per_model = self.time_budget_seconds // 4

        # 1. RandomForest
        if time.time() - start_time < self.time_budget_seconds:
            logger.info("Tuning RandomForest...")
            results["random_forest"] = self.tuner.tune_random_forest(
                X, y, use_randomized=True, n_iter=30
            )

        # 2. GradientBoosting
        if time.time() - start_time < self.time_budget_seconds:
            logger.info("Tuning GradientBoosting...")
            results["gradient_boosting"] = self.tuner.tune_gradient_boosting(
                X, y, use_randomized=True, n_iter=30
            )

        # 3. XGBoost (опционально)
        if include_xgboost and time.time() - start_time < self.time_budget_seconds:
            logger.info("Tuning XGBoost...")
            results["xgboost"] = self.tuner.tune_xgboost(
                X, y, use_randomized=True, n_iter=30
            )

        # 4. Ridge (быстро)
        if time.time() - start_time < self.time_budget_seconds:
            logger.info("Tuning Ridge...")
            results["ridge"] = self.tuner.tune_ridge(X, y)

        # Выбираем лучшую модель
        best_model = None
        best_score = float("inf") if "neg" in self.scoring.value else float("-inf")

        for name, result in results.items():
            if result.best_estimator is None:
                continue

            is_better = (
                result.best_score < best_score
                if "neg" in self.scoring.value
                else result.best_score > best_score
            )

            if is_better:
                best_score = result.best_score
                best_model = result.best_estimator

        return best_model, results

    def get_recommendations(
        self,
        results: dict[str, TuningResult],
    ) -> list[str]:
        """Получить рекомендации на основе результатов.
        
        Args:
            results: Результаты сравнения моделей
            
        Returns:
            Список рекомендаций
        """
        recommendations = []

        if not results:
            recommendations.append("No results available. Check if sklearn is installed.")
            return recommendations

        # Сортируем по score
        sorted_results = sorted(
            [(name, r) for name, r in results.items() if r.best_estimator is not None],
            key=lambda x: x[1].best_score,
            reverse="neg" not in self.scoring.value,
        )

        if not sorted_results:
            recommendations.append("No models were successfully trained.")
            return recommendations

        best_name, best_result = sorted_results[0]

        recommendations.append(
            f"✅ Best model: {best_name} (Score: {best_result.best_score:.4f})"
        )

        # Проверяем разницу между моделями
        if len(sorted_results) >= 2:
            second_name, second_result = sorted_results[1]
            diff = abs(best_result.best_score - second_result.best_score)
            if diff < 0.01:
                recommendations.append(
                    f"⚠️ {second_name} is very close. Consider ensemble."
                )

        # Рекомендации по конкретным моделям
        if best_name == "random_forest":
            recommendations.append("💡 RandomForest is robust to outliers.")
        elif best_name == "gradient_boosting":
            recommendations.append("💡 GradientBoosting may overfit. Monitor train/test gap.")
        elif best_name == "xgboost":
            recommendations.append("💡 XGBoost is fast. Consider early stopping in production.")
        elif best_name == "ridge":
            recommendations.append("💡 Ridge is simple but may underfit complex patterns.")

        return recommendations

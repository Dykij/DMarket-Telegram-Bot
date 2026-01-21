"""Tests for EnsembleBuilder and AdvancedFeatureSelector in model_tuner."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Check if sklearn is available
try:
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# Skip all tests if sklearn is not available
pytestmark = pytest.mark.skipif(
    not SKLEARN_AVAILABLE,
    reason="scikit-learn not installed"
)


@pytest.fixture
def sample_data():
    """Generate sample training data."""
    np.random.seed(42)
    X = np.random.randn(200, 10)
    # Create target with some predictable pattern
    y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(200) * 0.1
    return X, y


@pytest.fixture
def feature_names():
    """Generate sample feature names."""
    return [f"feature_{i}" for i in range(10)]


class TestEnsembleBuilder:
    """Test cases for EnsembleBuilder class."""

    def test_ensemble_builder_init(self):
        """Test EnsembleBuilder initialization."""
        from src.ml.model_tuner import EnsembleBuilder

        builder = EnsembleBuilder(cv_folds=5, random_state=42)

        assert builder.cv_folds == 5
        assert builder.random_state == 42
        assert builder._sklearn_available is True

    def test_create_voting_ensemble(self, sample_data):
        """Test creating a voting ensemble."""
        from src.ml.model_tuner import EnsembleBuilder

        X, y = sample_data
        builder = EnsembleBuilder(cv_folds=3)

        ensemble = builder.create_voting_ensemble(X, y, include_xgboost=False)

        assert ensemble is not None
        # Check it can predict
        predictions = ensemble.predict(X[:10])
        assert len(predictions) == 10
        assert all(np.isfinite(predictions))

    def test_voting_ensemble_with_weights(self, sample_data):
        """Test voting ensemble with custom weights."""
        from src.ml.model_tuner import EnsembleBuilder

        X, y = sample_data
        builder = EnsembleBuilder()

        # Custom weights for 3 models (rf, gb, ridge)
        ensemble = builder.create_voting_ensemble(
            X, y,
            include_xgboost=False,
            weights=[0.5, 0.3, 0.2],
        )

        assert ensemble is not None
        predictions = ensemble.predict(X[:5])
        assert len(predictions) == 5

    def test_calculate_weights(self, sample_data):
        """Test automatic weight calculation."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import Ridge

        from src.ml.model_tuner import EnsembleBuilder

        X, y = sample_data
        builder = EnsembleBuilder(cv_folds=3)

        estimators = [
            ("rf", RandomForestRegressor(n_estimators=10, random_state=42)),
            ("ridge", Ridge(alpha=1.0)),
        ]

        weights = builder._calculate_weights(estimators, X, y)

        assert len(weights) == 2
        assert all(w > 0 for w in weights)
        assert abs(sum(weights) - 1.0) < 0.001  # Weights sum to 1


class TestAdvancedFeatureSelector:
    """Test cases for AdvancedFeatureSelector class."""

    def test_feature_selector_init(self):
        """Test AdvancedFeatureSelector initialization."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        selector = AdvancedFeatureSelector(random_state=42)

        assert selector.random_state == 42
        assert selector._sklearn_available is True

    def test_select_from_model_median(self, sample_data, feature_names):
        """Test feature selection with median threshold."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        X_selected, selected_names = selector.select_from_model(
            X, y,
            feature_names=feature_names,
            threshold="median",
        )

        # Should select approximately half of features
        assert X_selected.shape[1] <= X.shape[1]
        assert X_selected.shape[1] > 0
        assert len(selected_names) == X_selected.shape[1]

    def test_select_from_model_max_features(self, sample_data, feature_names):
        """Test feature selection with max_features limit."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        X_selected, selected_names = selector.select_from_model(
            X, y,
            feature_names=feature_names,
            max_features=5,
        )

        assert X_selected.shape[1] <= 5
        assert len(selected_names) == X_selected.shape[1]

    def test_recursive_feature_elimination(self, sample_data, feature_names):
        """Test recursive feature elimination."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        X_selected, selected_names, rankings = selector.recursive_feature_elimination(
            X, y,
            feature_names=feature_names,
            n_features_to_select=5,
        )

        assert X_selected.shape[1] == 5
        assert len(selected_names) == 5
        assert len(rankings) == len(feature_names)
        # All selected features should have rank 1
        assert all(rankings[name] == 1 for name in selected_names)

    def test_get_feature_importance_rf(self, sample_data, feature_names):
        """Test feature importance with random forest method."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        importance = selector.get_feature_importance(
            X, y,
            feature_names=feature_names,
            method="random_forest",
        )

        assert len(importance) == len(feature_names)
        assert all(v >= 0 for v in importance.values())
        # Importance should be sorted (highest first)
        values = list(importance.values())
        assert values == sorted(values, reverse=True)

    def test_get_feature_importance_permutation(self, sample_data, feature_names):
        """Test feature importance with permutation method."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        importance = selector.get_feature_importance(
            X, y,
            feature_names=feature_names,
            method="permutation",
        )

        assert len(importance) == len(feature_names)

    def test_invalid_method_raises_error(self, sample_data, feature_names):
        """Test that invalid method raises ValueError."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        with pytest.raises(ValueError, match="Unknown method"):
            selector.get_feature_importance(
                X, y,
                feature_names=feature_names,
                method="invalid_method",
            )


class TestIntegration:
    """Integration tests for ensemble and feature selection."""

    def test_feature_selection_then_ensemble(self, sample_data, feature_names):
        """Test combining feature selection with ensemble building."""
        from src.ml.model_tuner import AdvancedFeatureSelector, EnsembleBuilder

        X, y = sample_data

        # Step 1: Select features
        selector = AdvancedFeatureSelector()
        X_selected, selected_names = selector.select_from_model(
            X, y,
            feature_names=feature_names,
            max_features=5,
        )

        # Step 2: Build ensemble on selected features
        builder = EnsembleBuilder(cv_folds=3)
        ensemble = builder.create_voting_ensemble(
            X_selected, y,
            include_xgboost=False,
        )

        # Step 3: Verify ensemble works
        predictions = ensemble.predict(X_selected[:10])
        assert len(predictions) == 10

    def test_rfe_with_model_tuner(self, sample_data, feature_names):
        """Test RFE combined with model tuning."""
        from src.ml.model_tuner import AdvancedFeatureSelector, ModelTuner

        X, y = sample_data

        # Step 1: Feature selection with RFE
        selector = AdvancedFeatureSelector()
        X_selected, selected_names, _ = selector.recursive_feature_elimination(
            X, y,
            feature_names=feature_names,
            n_features_to_select=5,
        )

        # Step 2: Tune model on selected features
        tuner = ModelTuner(cv_folds=3)
        result = tuner.tune_ridge(X_selected, y)

        assert result.best_params is not None
        assert result.best_score > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_feature_names(self, sample_data):
        """Test with empty feature names."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        X, y = sample_data
        selector = AdvancedFeatureSelector()

        X_selected, selected_names = selector.select_from_model(
            X, y,
            feature_names=None,
        )

        assert X_selected.shape[1] <= X.shape[1]
        assert selected_names == []

    def test_single_feature(self):
        """Test with single feature."""
        from src.ml.model_tuner import AdvancedFeatureSelector

        np.random.seed(42)
        X = np.random.randn(100, 1)
        y = X[:, 0] * 2 + np.random.randn(100) * 0.1

        selector = AdvancedFeatureSelector()
        X_selected, _ = selector.select_from_model(X, y, max_features=1)

        assert X_selected.shape[1] == 1

    def test_few_samples(self):
        """Test with very few samples."""
        from src.ml.model_tuner import EnsembleBuilder

        np.random.seed(42)
        X = np.random.randn(20, 5)
        y = X[:, 0] * 2

        builder = EnsembleBuilder(cv_folds=2)
        ensemble = builder.create_voting_ensemble(X, y, include_xgboost=False)

        assert ensemble is not None

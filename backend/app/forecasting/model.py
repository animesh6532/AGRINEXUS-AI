"""
Forecasting models for the AgriNexus-AI backend.
Implements various time-series forecasting algorithms for agricultural prices.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import logging

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.seasonal import seasonal_decompose
    HAS_STATSMODELS = True
except ImportError:
    ARIMA = None
    ETSModel = None
    ExponentialSmoothing = None
    seasonal_decompose = None
    HAS_STATSMODELS = False


from ..core.logging import logger


@dataclass
class ForecastPoint:
    """Represents a single forecast point."""
    date: date
    predicted_price: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


@dataclass
class ForecastResult:
    """Represents the result of a forecasting operation."""
    commodity: str
    market: Optional[str]
    state: Optional[str]
    forecast_date: date  # Date when forecast was generated
    horizon_days: int
    model_name: str
    forecast: List[ForecastPoint]
    metrics: Dict[str, float]
    trend: str  # "increasing", "decreasing", "stable"


class BaseForecastModel(ABC):
    """Abstract base class for forecasting models."""

    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.training_data: Optional[pd.Series] = None
        self.model = None

    @abstractmethod
    def fit(self, data: pd.Series) -> None:
        """Fit the model to training data."""
        pass

    @abstractmethod
    def predict(self, steps: int) -> List[float]:
        """Generate forecasts for future time steps."""
        pass

    def predict_with_confidence(
        self,
        steps: int,
        confidence_interval: float = 0.95
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Generate forecasts with confidence intervals.
        Default implementation returns None for confidence intervals.
        Override in subclasses that support confidence intervals.

        Args:
            steps: Number of future steps to forecast
            confidence_interval: Confidence level (e.g., 0.95 for 95%)

        Returns:
            Tuple of (forecasts, lower_bounds, upper_bounds)
        """
        forecasts = self.predict(steps)
        # Return None for confidence intervals if not supported
        lower_bounds = [None] * len(forecasts)
        upper_bounds = [None] * len(forecasts)
        return forecasts, lower_bounds, upper_bounds

    def calculate_metrics(
        self,
        actual: List[float],
        predicted: List[float]
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics.

        Args:
            actual: Actual values
            predicted: Predicted values

        Returns:
            Dictionary of metric names and values
        """
        if len(actual) != len(predicted):
            raise ValueError("Actual and predicted arrays must have same length")

        if len(actual) == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        # Calculate metrics
        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)

        # Calculate MAPE (avoid division by zero)
        mape_values = []
        for a, p in zip(actual, predicted):
            if a != 0:
                mape_values.append(abs((a - p) / a) * 100)
            else:
                mape_values.append(0.0)  # If actual is zero, error is zero if predicted is zero

        mape = np.mean(mape_values) if mape_values else 0.0

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape)
        }


class NaiveForecastModel(BaseForecastModel):
    """Naive forecasting model - uses last observed value."""

    def __init__(self):
        super().__init__("Naive")

    def fit(self, data: pd.Series) -> None:
        """Fit the model (just store the last value)."""
        self.training_data = data.copy()
        self.is_fitted = True
        logger.debug(f"Fitted {self.name} model with {len(data)} observations")

    def predict(self, steps: int) -> List[float]:
        """Generate forecasts using last observed value."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.training_data is None or len(self.training_data) == 0:
            raise ValueError("No training data available")

        last_value = self.training_data.iloc[-1]
        return [float(last_value)] * steps


class MovingAverageForecastModel(BaseForecastModel):
    """Moving average forecasting model."""

    def __init__(self, window_size: int = 7):
        super().__init__(f"MovingAverage_{window_size}")
        self.window_size = window_size

    def fit(self, data: pd.Series) -> None:
        """Fit the model (just store the data)."""
        self.training_data = data.copy()
        self.is_fitted = True
        logger.debug(
            f"Fitted {self.name} model with {len(data)} observations "
            f"(window={self.window_size})"
        )

    def predict(self, steps: int) -> List[float]:
        """Generate forecasts using moving average."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.training_data is None or len(self.training_data) < self.window_size:
            # Fallback to naive if not enough data
            logger.warning(
                f"Not enough data for moving average (need {self.window_size}, "
                f"got {len(self.training_data) if self.training_data is not None else 0}). "
                f"Falling back to naive forecast."
            )
            naive_model = NaiveForecastModel()
            naive_model.training_data = self.training_data
            naive_model.is_fitted = True
            return naive_model.predict(steps)

        # Calculate moving average of last window_size observations
        recent_data = self.training_data.iloc[-self.window_size:]
        ma_value = recent_data.mean()
        return [float(ma_value)] * steps


class ExponentialSmoothingForecastModel(BaseForecastModel):
    """Exponential smoothing forecasting model (Holt-Winters)."""

    def __init__(
        self,
        trend: Optional[str] = "add",
        seasonal: Optional[str] = None,
        seasonal_periods: Optional[int] = None
    ):
        trend_str = trend if trend else "none"
        seasonal_str = seasonal if seasonal else "none"
        super().__init__(
            f"ETS_{trend_str}_{seasonal_str}"
            f"_{seasonal_periods if seasonal_periods else 'no'}"
        )
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.model_fit = None

    def fit(self, data: pd.Series) -> None:
        """Fit the exponential smoothing model."""
        if len(data) < 2:
            raise ValueError("Need at least 2 observations to fit ETS model")

        self.training_data = data.copy()

        try:
            # Handle case where we don't have enough data for seasonality
            if self.seasonal and self.seasonal_periods:
                if len(data) < 2 * self.seasonal_periods:
                    logger.warning(
                        f"Not enough data for seasonal ETS (need {2 * self.seasonal_periods}, "
                        f"got {len(data)}. Falling back to non-seasonal."
                    )
                    self.seasonal = None
                    self.seasonal_periods = None

            if ExponentialSmoothing is None:
                raise ImportError("statsmodels is not installed")

            # Fit the model
            self.model = ExponentialSmoothing(
                self.training_data,
                trend=self.trend,
                seasonal=self.seasonal,
                seasonal_periods=self.seasonal_periods
            )
            self.model_fit = self.model.fit()
            self.is_fitted = True
            logger.debug(f"Fitted {self.name} model with {len(data)} observations")

        except Exception as e:
            logger.warning(
                f"Failed to fit ETS model ({self.name}): {e}. "
                f"Falling back to simple naive forecast."
            )
            self.is_fitted = True
            self.model_fit = None

    def predict(self, steps: int) -> List[float]:
        """Generate forecasts using the fitted ETS model."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.model_fit is None or not hasattr(self.model_fit, "forecast"):
            last_value = self.training_data.iloc[-1] if self.training_data is not None and len(self.training_data) > 0 else 0.0
            return [float(last_value)] * steps

        try:
            forecast_obj = self.model_fit.forecast(steps)
            if hasattr(forecast_obj, 'tolist'):
                return [float(x) for x in forecast_obj.tolist()]
            else:
                return [float(forecast_obj)] * steps
        except Exception as e:
            logger.error(f"Error generating ETS forecast: {e}")
            last_value = self.training_data.iloc[-1] if self.training_data is not None else 0.0
            return [float(last_value)] * steps

    def predict_with_confidence(
        self,
        steps: int,
        confidence_interval: float = 0.95
    ) -> Tuple[List[float], List[float], List[float]]:
        """Generate forecasts with confidence intervals."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.model_fit is None or not hasattr(self.model_fit, "forecast"):
            forecasts = self.predict(steps)
            return forecasts, [None] * len(forecasts), [None] * len(forecasts)

        try:
            forecast_obj = self.model_fit.forecast(steps)
            conf_int = self.model_fit.get_forecast(steps).conf_int(
                alpha=1 - confidence_interval
            )

            forecasts = [float(x) for x in forecast_obj]
            lower_bounds = [float(x) for x in conf_int.iloc[:, 0]]
            upper_bounds = [float(x) for x in conf_int.iloc[:, 1]]

            return forecasts, lower_bounds, upper_bounds
        except Exception as e:
            logger.error(f"Error generating ETS forecast with confidence: {e}")
            forecasts = self.predict(steps)
            return forecasts, [None] * len(forecasts), [None] * len(forecasts)


class ARIMAForecastModel(BaseForecastModel):
    """ARIMA forecasting model."""

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None
    ):
        order_str = f"{order[0]}{order[1]}{order[2]}"
        seasonal_str = (
            f"{seasonal_order[0]}{seasonal_order[1]}{seasonal_order[2]}{seasonal_order[3]}"
            if seasonal_order else "none"
        )
        super().__init__(f"ARIMA_{order_str}_{seasonal_str}")
        self.order = order
        self.seasonal_order = seasonal_order
        self.model_fit = None

    def fit(self, data: pd.Series) -> None:
        """Fit the ARIMA model."""
        if len(data) < 10:
            raise ValueError("Need at least 10 observations to fit ARIMA model")

        self.training_data = data.copy()

        try:
            if ARIMA is None:
                raise ImportError("statsmodels is not installed")

            self.model = ARIMA(
                self.training_data,
                order=self.order,
                seasonal_order=self.seasonal_order
            )
            self.model_fit = self.model.fit()
            self.is_fitted = True
            logger.debug(
                f"Fitted {self.name} model with {len(data)} observations "
                f"(order={self.order}, seasonal={self.seasonal_order})"
            )
        except Exception as e:
            logger.warning(
                f"Failed to fit ARIMA model ({self.name}): {e}. "
                f"Falling back to simple naive forecast."
            )
            self.is_fitted = True
            self.model_fit = None

    def predict(self, steps: int) -> List[float]:
        """Generate forecasts using the fitted ARIMA model."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.model_fit is None or not hasattr(self.model_fit, "forecast"):
            last_value = self.training_data.iloc[-1] if self.training_data is not None and len(self.training_data) > 0 else 0.0
            return [float(last_value)] * steps

        try:
            forecast_obj = self.model_fit.forecast(steps)
            if hasattr(forecast_obj, 'tolist'):
                return [float(x) for x in forecast_obj.tolist()]
            else:
                return [float(forecast_obj)] * steps
        except Exception as e:
            logger.error(f"Error generating ARIMA forecast: {e}")
            last_value = self.training_data.iloc[-1] if self.training_data is not None else 0.0
            return [float(last_value)] * steps

    def predict_with_confidence(
        self,
        steps: int,
        confidence_interval: float = 0.95
    ) -> Tuple[List[float], List[float], List[float]]:
        """Generate forecasts with confidence intervals."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if self.model_fit is None or not hasattr(self.model_fit, "forecast"):
            forecasts = self.predict(steps)
            return forecasts, [None] * len(forecasts), [None] * len(forecasts)


        try:
            forecast_obj = self.model_fit.forecast(steps)
            conf_int = self.model_fit.get_forecast(steps).conf_int(
                alpha=1 - confidence_interval
            )

            forecasts = [float(x) for x in forecast_obj]
            lower_bounds = [float(x) for x in conf_int.iloc[:, 0]]
            upper_bounds = [float(x) for x in conf_int.iloc[:, 1]]

            return forecasts, lower_bounds, upper_bounds
        except Exception as e:
            logger.error(f"Error generating ARIMA forecast with confidence: {e}")
            # Fall back to point forecasts without confidence
            forecasts = self.predict(steps)
            return forecasts, [None] * len(forecasts), [None] * len(forecasts)


def create_forecast_model(model_type: str, **kwargs) -> BaseForecastModel:
    """
    Factory function to create forecasting models.

    Args:
        model_type: Type of model to create ("naive", "moving_average", "ets", "arima")
        **kwargs: Additional parameters for specific model types

    Returns:
        Configured forecasting model instance
    """
    model_type = model_type.lower()

    if model_type == "naive":
        return NaiveForecastModel()
    elif model_type == "moving_average":
        window_size = kwargs.get("window_size", 7)
        return MovingAverageForecastModel(window_size=window_size)
    elif model_type == "ets":
        trend = kwargs.get("trend", "add")
        seasonal = kwargs.get("seasonal", None)
        seasonal_periods = kwargs.get("seasonal_periods", None)
        return ExponentialSmoothingForecastModel(
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods
        )
    elif model_type == "arima":
        order = kwargs.get("order", (1, 1, 1))
        seasonal_order = kwargs.get("seasonal_order", None)
        return ARIMAForecastModel(
            order=order,
            seasonal_order=seasonal_order
        )
    else:
        logger.warning(f"Unknown model type '{model_type}'. Defaulting to naive.")
        return NaiveForecastModel()
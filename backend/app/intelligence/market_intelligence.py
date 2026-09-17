"""
Market intelligence layer for the Market Forecast backend.
Derives actionable insights and signals from market data and forecasts.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

import numpy as np

from ..core.logging import logger
from ..database import connection, models, repository
from ..forecasting.forecast_service import ForecastResult
from ..services.market_service import MarketService


class MarketIntelligence:
    """
    Market intelligence service that derives signals and insights
    from market data, forecasts, and other relevant information.
    """

    def __init__(self, db: connection.Session):
        self.db = db
        self.market_service = MarketService(db)
        logger.debug("Initialized MarketIntelligence service")

    def analyze_market_trend(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze recent market trends for a commodity.

        Args:
            commodity: Commodity name to analyze
            state: State name filter (optional)
            district: District name filter (optional)
            market: Market name filter (optional)
            lookback_days: Number of days to look back for trend analysis

        Returns:
            Dictionary containing trend analysis signals
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        # Get historical observations
        observations = self.market_service.get_historical_prices(
            commodity=commodity,
            start_date=start_date,
            end_date=end_date,
            state=state,
            district=district,
            market=market
        )

        if len(observations) < 2:
            return {
                "trend": "insufficient_data",
                "signal_strength": 0.0,
                "recent_change_percent": 0.0,
                "volatility": 0.0,
                "data_points": len(observations),
                "analysis_period_days": lookback_days
            }

        # Extract prices and dates
        prices = [obs["modal_price"] for obs in observations]
        dates = [
            obs["observation_date"] if isinstance(obs["observation_date"], date)
            else datetime.fromisoformat(obs["observation_date"]).date()
            for obs in observations
        ]

        # Calculate recent change (last 7 days vs previous 7 days)
        if len(prices) >= 14:
            recent_avg = np.mean(prices[-7:])
            previous_avg = np.mean(prices[-14:-7])
            recent_change_percent = (
                ((recent_avg - previous_avg) / previous_avg) * 100
                if previous_avg != 0 else 0.0
            )
        elif len(prices) >= 2:
            # Use first and last if not enough for 7-day comparison
            recent_change_percent = (
                ((prices[-1] - prices[0]) / prices[0]) * 100
                if prices[0] != 0 else 0.0
            )
        else:
            recent_change_percent = 0.0

        # Calculate volatility (standard deviation of returns)
        if len(prices) >= 2:
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
            volatility = np.std(returns) * 100 if returns else 0.0  # As percentage
        else:
            volatility = 0.0

        # Determine trend direction
        if recent_change_percent > 1.0:  # More than 1% increase
            trend = "increasing"
            signal_strength = min(abs(recent_change_percent) / 10.0, 1.0)  # Normalize
        elif recent_change_percent < -1.0:  # More than 1% decrease
            trend = "decreasing"
            signal_strength = min(abs(recent_change_percent) / 10.0, 1.0)
        else:
            trend = "stable"
            signal_strength = 1.0 - (abs(recent_change_percent) / 2.0)  # Higher strength for stability
            signal_strength = max(0.0, min(signal_strength, 1.0))

        return {
            "trend": trend,
            "signal_strength": float(signal_strength),
            "recent_change_percent": float(recent_change_percent),
            "volatility": float(volatility),
            "data_points": len(observations),
            "analysis_period_days": lookback_days,
            "latest_price": float(prices[-1]) if prices else 0.0,
            "latest_date": dates[-1].isoformat() if dates else None
        }

    def analyze_forecast_outlook(
        self,
        forecast_result: ForecastResult
    ) -> Dict[str, Any]:
        """
        Analyze forecast results to derive outlook signals.

        Args:
            forecast_result: ForecastResult to analyze

        Returns:
            Dictionary containing forecast outlook signals
        """
        if not forecast_result.forecast:
            return {
                "forecast_trend": "no_data",
                "forecast_change_percent": 0.0,
                "forecast_confidence": "low",
                "risk_level": "unknown"
            }

        # Extract forecast prices
        forecast_prices = [fp.predicted_price for fp in forecast_result.forecast]
        forecast_dates = [fp.date for fp in forecast_result.forecast]

        if len(forecast_prices) < 2:
            return {
                "forecast_trend": "insufficient_data",
                "forecast_change_percent": 0.0,
                "forecast_confidence": "low",
                "risk_level": "unknown"
            }

        # Calculate forecast change (first to last day)
        first_price = forecast_prices[0]
        last_price = forecast_prices[-1]
        forecast_change_percent = (
            ((last_price - first_price) / first_price) * 100
            if first_price != 0 else 0.0
        )

        # Determine forecast trend
        if forecast_change_percent > 2.0:  # More than 2% increase over forecast horizon
            forecast_trend = "increasing"
        elif forecast_change_percent < -2.0:  # More than 2% decrease
            forecast_trend = "decreasing"
        else:
            forecast_trend = "stable"

        # Assess forecast confidence based on model metrics
        mae = forecast_result.metrics.get("mae", 0.0)
        rmse = forecast_result.metrics.get("rmse", 0.0)
        mape = forecast_result.metrics.get("mape", 0.0)

        # Normalize confidence based on error rates (lower error = higher confidence)
        # These thresholds are somewhat arbitrary but reasonable for agricultural prices
        if mape < 5.0:
            confidence = "high"
        elif mape < 15.0:
            confidence = "medium"
        else:
            confidence = "low"

        # Assess risk level based on volatility and trend uncertainty
        volatility = self._estimate_forecast_volatility(forecast_prices)
        if volatility > 10.0 or abs(forecast_change_percent) > 20.0:
            risk_level = "high"
        elif volatility > 5.0 or abs(forecast_change_percent) > 10.0:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "forecast_trend": forecast_trend,
            "forecast_change_percent": float(forecast_change_percent),
            "forecast_confidence": confidence,
            "risk_level": risk_level,
            "forecast_horizon_days": len(forecast_prices),
            "forecast_start_price": float(first_price),
            "forecast_end_price": float(last_price),
            "model_used": forecast_result.model_name
        }

    async def get_market_signals(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        forecast_horizon: int = 7
    ) -> Dict[str, Any]:
        """
        Get comprehensive market signals combining trend analysis and forecast outlook.

        Args:
            commodity: Commodity name to analyze
            state: State name filter (optional)
            district: District name filter (optional)
            market: Market name filter (optional)
            forecast_horizon: Number of days to forecast ahead

        Returns:
            Dictionary containing combined market signals
        """
        logger.info(
            f"Generating market signals for {commodity} "
            f"(horizon: {forecast_horizon} days)"
        )

        # Get current market data
        latest_price_data = self.market_service.get_latest_price(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )

        # Analyze recent market trends
        trend_analysis = self.analyze_market_trend(
            commodity=commodity,
            state=state,
            district=district,
            market=market,
            lookback_days=30
        )

        # Generate forecast
        forecast_result = None
        try:
            from ..forecasting.forecast_service import ForecastService
            forecast_service = ForecastService(self.db)
            forecast_result = await forecast_service.generate_forecast(
                commodity=commodity,
                horizon_days=forecast_horizon,
                state=state,
                district=district,
                market=market,
                model_type="ets"  # Default to ETS for intelligence layer
            )
        except ValueError as e:
            # Expected condition: not enough legitimate historical data.
            # Do not fabricate a forecast; continue with the other signals.
            logger.warning(f"Forecast skipped for market signals: {e}")
            forecast_result = None
        except Exception as e:
            logger.error(f"Error generating forecast for market signals: {e}")
            # Create a minimal forecast result for error case
            forecast_result = None

        # Analyze forecast outlook and build a response-ready forecast analysis
        if forecast_result:
            outlook = self.analyze_forecast_outlook(forecast_result)
            forecast_points = [
                {
                    "date": point.date,
                    "predicted_price": point.predicted_price,
                    "confidence_lower": point.confidence_lower,
                    "confidence_upper": point.confidence_upper,
                }
                for point in forecast_result.forecast
            ]
            forecast_model = forecast_result.model_name
            forecast_metrics = forecast_result.metrics
        else:
            outlook = {
                "forecast_trend": "insufficient_data",
                "forecast_change_percent": 0.0,
                "forecast_confidence": "low",
                "risk_level": "unknown",
            }
            forecast_points = []
            forecast_model = "ets"
            forecast_metrics = {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        # Map non-standard outlook trends to a response-valid trend value
        outlook_trend = outlook.get("forecast_trend", "stable")
        response_trend = (
            outlook_trend
            if outlook_trend in ("increasing", "decreasing", "stable")
            else "stable"
        )

        forecast_analysis = {
            "commodity": commodity,
            "market": market,
            "state": state,
            "current_price": latest_price_data["modal_price"] if latest_price_data else 0.0,
            "forecast_horizon_days": forecast_horizon,
            "forecast": forecast_points,
            "trend": response_trend,
            "model": forecast_model,
            "metrics": forecast_metrics,
            # Additional outlook details consumed by signal generation
            "forecast_trend": outlook_trend,
            "forecast_change_percent": outlook.get("forecast_change_percent", 0.0),
            "forecast_confidence": outlook.get("forecast_confidence", "low"),
            "risk_level": outlook.get("risk_level", "unknown"),
        }

        # Combine signals into actionable insights
        signals = self._generate_actionable_signals(
            trend_analysis,
            forecast_analysis,
            latest_price_data
        )

        return {
            "commodity": commodity,
            "market": market,
            "state": state,
            "district": district,
            "timestamp": datetime.utcnow().isoformat(),
            "latest_price": latest_price_data,
            "trend_analysis": trend_analysis,
            "forecast_analysis": forecast_analysis,
            "actionable_signals": signals,
            "forecast_horizon_days": forecast_horizon
        }

    def _estimate_forecast_volatility(
        self,
        forecast_prices: List[float]
    ) -> float:
        """
        Estimate volatility from forecast price series.

        Args:
            forecast_prices: List of forecasted prices

        Returns:
            Volatility estimate as percentage
        """
        if len(forecast_prices) < 2:
            return 0.0

        # Calculate percentage changes between consecutive forecast points
        changes = []
        for i in range(1, len(forecast_prices)):
            if forecast_prices[i-1] != 0:
                change = ((forecast_prices[i] - forecast_prices[i-1]) / forecast_prices[i-1]) * 100
                changes.append(abs(change))

        return np.mean(changes) if changes else 0.0

    def _generate_actionable_signals(
        self,
        trend_analysis: Dict[str, Any],
        forecast_analysis: Dict[str, Any],
        latest_price_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable trading/signaling insights from analysis.

        Args:
            trend_analysis: Recent trend analysis results
            forecast_analysis: Forecast outlook analysis
            latest_price_data: Latest price information

        Returns:
            List of actionable signal dictionaries
        """
        signals = []

        # Signal 1: Trend continuation signal
        recent_trend = trend_analysis.get("trend", "stable")
        forecast_trend = forecast_analysis.get("forecast_trend", "stable")
        recent_change = trend_analysis.get("recent_change_percent", 0.0)
        forecast_change = forecast_analysis.get("forecast_change_percent", 0.0)

        if recent_trend == forecast_trend and recent_trend != "stable":
            # Trend is expected to continue
            signals.append({
                "type": "trend_continuation",
                "direction": recent_trend,
                "strength": "medium",
                "description": f"{recent_trend.title()} trend expected to continue",
                "confidence": "medium"
            })

        # Signal 2: Trend reversal signal
        elif recent_trend != "stable" and forecast_trend == "stable":
            # Trend expected to stabilize
            signals.append({
                "type": "trend_stabilization",
                "prior_direction": recent_trend,
                "strength": "low",
                "description": f"{recent_trend.title()} trend expected to stabilize",
                "confidence": "medium"
            })

        elif recent_trend != forecast_trend and forecast_trend != "stable":
            # Trend expected to reverse
            signals.append({
                "type": "trend_reversal",
                "from_direction": recent_trend,
                "to_direction": forecast_trend,
                "strength": "high",
                "description": f"Trend expected to reverse from {recent_trend} to {forecast_trend}",
                "confidence": "medium"
            })

        # Signal 3: Significant price movement expected
        abs_forecast_change = abs(forecast_change)
        if abs_forecast_change > 10.0:  # More than 10% change expected
            direction = "up" if forecast_change > 0 else "down"
            signals.append({
                "type": "significant_price_movement",
                "direction": direction,
                "magnitude": abs_forecast_change,
                "strength": "high",
                "description": f"Significant price {direction} movement expected "
                           f"({abs_forecast_change:.1f}% over forecast horizon)",
                "confidence": "medium"
            })

        # Signal 4: High volatility warning
        volatility = trend_analysis.get("volatility", 0.0)
        if volatility > 15.0:  # High volatility
            signals.append({
                "type": "high_volatility_warning",
                "volatility": volatility,
                "strength": "medium",
                "description": f"High market volatility detected ({volatility:.1f}%)",
                "confidence": "high"
            })

        # Signal 5: Low data availability warning
        data_points = trend_analysis.get("data_points", 0)
        if data_points < 10:
            signals.append({
                "type": "low_data_availability",
                "data_points": data_points,
                "strength": "medium",
                "description": f"Limited historical data available ({data_points} points)",
                "confidence": "high"
            })

        # If no specific signals generated, add a neutral signal
        if not signals:
            signals.append({
                "type": "neutral_market",
                "strength": "low",
                "description": "Market appears stable with no strong signals detected",
                "confidence": "low"
            })

        return signals
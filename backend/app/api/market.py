"""
Market Forecast API endpoints.
Exposes functionality for retrieving market data, generating forecasts,
and deriving market intelligence signals.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from ..core import dependencies
from ..core.config import settings
from ..core.logging import logger
from ..database import connection
from ..intelligence import market_intelligence
from ..schemas import market as schemas
from ..services import market_service
from ..forecasting import forecast_service

# Create router
router = APIRouter(
    prefix="/api/market",
    tags=["market"],
    responses={404: {"description": "Not found"}},
)


# Dependency injection
def get_db_session() -> Session:
    """Dependency to get database session."""
    with connection.SessionLocal() as session:
        try:
            yield session
        finally:
            session.close()


def get_market_service(db: Session = Depends(get_db_session)) -> market_service.MarketService:
    """Dependency to get market service."""
    return market_service.MarketService(db)


def get_forecast_service(db: Session = Depends(get_db_session)) -> forecast_service.ForecastService:
    """Dependency to get forecast service."""
    return forecast_service.ForecastService(db)


def get_market_intelligence_service(
    db: Session = Depends(get_db_session)
) -> market_intelligence.MarketIntelligence:
    """Dependency to get market intelligence service."""
    return market_intelligence.MarketIntelligence(db)


@router.get(
    "/current",
    response_model=schemas.MarketObservationResponse,
    summary="Get latest market price for a commodity",
    description="Retrieve the most recent market price observation for a specified commodity and location."
)
async def get_current_price(
    commodity: str = Query(..., description="Commodity name (e.g., 'Paddy(Common)')", example="Paddy(Common)"),
    state: Optional[str] = Query(None, description="State name (e.g., 'Andhra Pradesh')", example="Andhra Pradesh"),
    district: Optional[str] = Query(None, description="District name (e.g., 'Prakasam')", example="Prakasam"),
    market: Optional[str] = Query(None, description="Market name (e.g., 'Maddipadu APMC')", example="Maddipadu APMC"),
    market_svc: market_service.MarketService = Depends(get_market_service)
):
    """
    Get the latest market price for a commodity.

    Returns the most recent observation for the specified commodity
    and optional location filters.
    """
    logger.info(
        f"Fetching current price for commodity={commodity}, "
        f"state={state}, district={district}, market={market}"
    )

    observation = market_svc.get_latest_price(
        commodity=commodity,
        state=state,
        district=district,
        market=market
    )

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data found for commodity '{commodity}' "
                   f"with specified location filters"
        )

    return observation


@router.get(
    "/history",
    response_model=List[schemas.MarketObservationResponse],
    summary="Get historical market prices",
    description="Retrieve historical market price observations for a commodity."
)
async def get_historical_prices(
    commodity: str = Query(..., description="Commodity name", example="Paddy(Common)"),
    state: Optional[str] = Query(None, description="State name filter"),
    district: Optional[str] = Query(None, description="District name filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    market_svc: market_service.MarketService = Depends(get_market_service)
):
    """
    Get historical market prices for a commodity.

    Returns a list of market observations for the specified commodity
    and optional date/location filters.
    """
    logger.info(
        f"Fetching historical prices for commodity={commodity}, "
        f"state={state}, district={district}, market={market}, "
        f"start_date={start_date}, end_date={end_date}, limit={limit}"
    )

    observations = market_svc.get_historical_prices(
        commodity=commodity,
        start_date=start_date,
        end_date=end_date,
        state=state,
        district=district,
        market=market,
        limit=limit
    )

    return observations


@router.get(
    "/forecast",
    response_model=schemas.MarketForecastResponse,
    summary="Generate market price forecast",
    description="Generate future price forecasts for a commodity using time-series models."
)
async def get_market_forecast(
    commodity: str = Query(..., description="Commodity name to forecast", example="Paddy(Common)"),
    state: Optional[str] = Query(None, description="State name filter"),
    district: Optional[str] = Query(None, description="District name filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    horizon: int = Query(7, description="Forecast horizon in days", ge=1, le=30, example=7),
    model: Optional[str] = Query(
        None,
        description="Forecasting model to use",
        regex="^(naive|moving_average|ets|arima)$",
        example="ets"
    ),
    use_cache: bool = Query(True, description="Use cached forecast if available"),
    forecast_svc: forecast_service.ForecastService = Depends(get_forecast_service)
):
    """
    Generate market price forecast for a commodity.

    Uses historical data to train a forecasting model and generate
    future price predictions.
    """
    logger.info(
        f"Generating forecast for commodity={commodity}, "
        f"state={state}, district={district}, market={market}, "
        f"horizon={horizon}, model={model}, use_cache={use_cache}"
    )

    try:
        # Default to ETS model if none specified
        model_type = model or "ets"

        forecast_result = await forecast_svc.generate_forecast(
            commodity=commodity,
            horizon_days=horizon,
            state=state,
            district=district,
            market=market,
            model_type=model_type,
            use_cache=use_cache
        )

        # Get current price for the response
        market_svc = market_service.MarketService(forecast_svc.db)
        current_obs = market_svc.get_latest_price(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )

        current_price = current_obs["modal_price"] if current_obs else 0.0

        # Build response
        response = schemas.MarketForecastResponse(
            commodity=forecast_result.commodity,
            market=forecast_result.market,
            state=forecast_result.state,
            current_price=current_price,
            forecast_horizon_days=forecast_result.horizon_days,
            forecast=[
                schemas.ForecastPointResponse(
                    date=fp.date,
                    predicted_price=fp.predicted_price,
                    confidence_lower=fp.confidence_lower,
                    confidence_upper=fp.confidence_upper
                )
                for fp in forecast_result.forecast
            ],
            trend=forecast_result.trend,
            model=forecast_result.model_name,
            metrics=forecast_result.metrics
        )

        return response

    except ValueError as e:
        logger.warning(f"Validation error in forecast generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating market forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating forecast"
        )


@router.get(
    "/trend",
    response_model=schemas.MarketTrendResponse,
    summary="Get market trend analysis",
    description="Analyze recent market trends for a commodity."
)
async def get_market_trend(
    commodity: str = Query(..., description="Commodity name to analyze", example="Paddy(Common)"),
    state: Optional[str] = Query(None, description="State name filter"),
    district: Optional[str] = Query(None, description="District name filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    lookback_days: int = Query(30, description="Lookback period in days", ge=7, le=90, example=30),
    intel_svc: market_intelligence.MarketIntelligence = Depends(get_market_intelligence_service)
):
    """
    Get market trend analysis for a commodity.

    Analyzes recent price movements to determine trend direction,
    strength, and volatility.
    """
    logger.info(
        f"Analyzing market trend for commodity={commodity}, "
        f"state={state}, district={district}, market={market}, "
        f"lookback_days={lookback_days}"
    )

    try:
        trend_analysis = intel_svc.analyze_market_trend(
            commodity=commodity,
            state=state,
            district=district,
            market=market,
            lookback_days=lookback_days
        )

        # Get latest price for completeness
        market_svc = market_service.MarketService(intel_svc.db)
        latest_price_data = market_svc.get_latest_price(
            commodity=commodity,
            state=state,
            district=district,
            market=market
        )

        response = schemas.MarketTrendResponse(
            commodity=commodity,
            market=market,
            state=state,
            trend=trend_analysis["trend"],
            recent_change_percent=trend_analysis["recent_change_percent"],
            forecast_change_percent=0.0,  # Will be filled by forecast analysis if needed
            volatility=trend_analysis["volatility"],
            signal_strength=trend_analysis["signal_strength"],
            data_points=trend_analysis["data_points"],
            analysis_period_days=trend_analysis["analysis_period_days"],
            latest_price=latest_price_data["modal_price"] if latest_price_data else 0.0,
            latest_date=date.fromisoformat(latest_price_data["observation_date"]) if latest_price_data and latest_price_data.get("observation_date") else date.today()
        )

        return response

    except Exception as e:
        logger.error(f"Error analyzing market trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while analyzing market trend"
        )


@router.get(
    "/signals",
    response_model=schemas.MarketSignalsResponse,
    summary="Get comprehensive market signals",
    description="Get combined market data, trend analysis, forecast, and actionable signals."
)
async def get_market_signals(
    commodity: str = Query(..., description="Commodity name to analyze", example="Paddy(Common)"),
    state: Optional[str] = Query(None, description="State name filter"),
    district: Optional[str] = Query(None, description="District name filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    forecast_horizon: int = Query(7, description="Forecast horizon in days", ge=1, le=30, example=7),
    intel_svc: market_intelligence.MarketIntelligence = Depends(get_market_intelligence_service)
):
    """
    Get comprehensive market signals for a commodity.

    Combines current market data, trend analysis, forecast outlook,
    and actionable trading signals.
    """
    logger.info(
        f"Generating market signals for commodity={commodity}, "
        f"state={state}, district={district}, market={market}, "
        f"forecast_horizon={forecast_horizon}"
    )

    try:
        signals_data = await intel_svc.get_market_signals(
            commodity=commodity,
            state=state,
            district=district,
            market=market,
            forecast_horizon=forecast_horizon
        )

        # Convert to response format
        response = schemas.MarketSignalsResponse(
            commodity=signals_data["commodity"],
            market=signals_data["market"],
            state=signals_data["state"],
            district=signals_data["district"],
            timestamp=signals_data["timestamp"],
            latest_price=schemas.MarketObservationResponse(**signals_data["latest_price"]) if signals_data["latest_price"] else None,
            trend_analysis=schemas.MarketTrendResponse(
                commodity=signals_data["commodity"],
                market=signals_data["market"],
                state=signals_data["state"],
                trend=signals_data["trend_analysis"]["trend"],
                recent_change_percent=signals_data["trend_analysis"]["recent_change_percent"],
                forecast_change_percent=signals_data["forecast_analysis"].get(
                    "forecast_change_percent", 0.0
                ),
                volatility=signals_data["trend_analysis"]["volatility"],
                signal_strength=signals_data["trend_analysis"]["signal_strength"],
                data_points=signals_data["trend_analysis"]["data_points"],
                analysis_period_days=signals_data["trend_analysis"]["analysis_period_days"],
                latest_price=signals_data["latest_price"]["modal_price"] if signals_data["latest_price"] else 0.0,
                latest_date=date.fromisoformat(signals_data["latest_price"]["observation_date"]) if signals_data["latest_price"] and signals_data["latest_price"].get("observation_date") else date.today()
            ),
            forecast_analysis=schemas.MarketForecastResponse(**signals_data["forecast_analysis"]),
            actionable_signals=signals_data["actionable_signals"],
            forecast_horizon_days=signals_data["forecast_horizon_days"]
        )

        return response

    except Exception as e:
        logger.error(f"Error generating market signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating market signals"
        )


@router.post(
    "/refresh",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refresh market data from external API",
    description="Trigger a refresh of market data from the external government API."
)
async def refresh_market_data(
    commodity: Optional[str] = Query(None, description="Commodity to filter (optional)"),
    state: Optional[str] = Query(None, description="State to filter (optional)"),
    market: Optional[str] = Query(None, description="Market to filter (optional)"),
    limit: int = Query(1000, description="Maximum records to fetch", ge=1, le=5000),
    market_svc: market_service.MarketService = Depends(get_market_service)
):
    """
    Refresh market data from external API.

    Fetches latest data from government sources and stores it in the database.
    """
    logger.info(
        f"Refreshing market data for commodity={commodity}, "
        f"state={state}, market={market}, limit={limit}"
    )

    try:
        # This would be run asynchronously in a real application
        # For now, we'll run it synchronously but return 202 Accepted
        stored_count = await market_svc.fetch_and_store_latest_data(
            commodity=commodity,
            state=state,
            market=market,
            limit=limit
        )

        return {
            "message": f"Market data refresh completed",
            "records_stored": stored_count,
            "status": "accepted"
        }

    except Exception as e:
        logger.error(f"Error refreshing market data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while refreshing market data"
        )


# Health check endpoint for the market module
@router.get(
    "/health",
    summary="Health check for market module",
    description="Check if the market forecast service is operational."
)
async def market_health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "module": "market_forecast",
        "timestamp": date.today().isoformat(),
        "version": "1.0.0"
    }
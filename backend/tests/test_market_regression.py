"""
Comprehensive regression test suite for Market Intelligence module.
Validates all requirements from Phase 21:
1. current commodity success
2. current commodity not found
3. current commodity + state
4. wrong state no fallback
5. commodity mapping (spacing / aliases)
6. forecast ETS
7. forecast moving_average
8. forecast naive
9. forecast ARIMA
10. forecast cache isolation
11. insufficient historical data
12. trend filtering
13. signal filtering
14. refresh behavior
"""

import asyncio
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import models
from app.forecasting.forecast_service import ForecastService
from app.services.market_service import MarketService, MarketAPIClient
from app.services.market_commodity_canonicalizer import (
    canonicalize_commodity,
    get_commodity_display_name,
    get_supported_commodities_catalogue,
)

test_client = TestClient(app)


# 1. Current commodity success
def test_current_commodity_success():
    resp = test_client.get("/api/market/current", params={"commodity": "Paddy(Common)"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity"] == "Paddy(Common)"
    assert data["modal_price"] > 0
    assert data["state"] is not None


# 2. Current commodity not found
def test_current_commodity_not_found():
    resp = test_client.get("/api/market/current", params={"commodity": "NonExistentCrop123"})
    assert resp.status_code == 404
    assert "No market data found" in resp.json()["detail"]


# 3. Current commodity + state
def test_current_commodity_with_state():
    resp = test_client.get(
        "/api/market/current",
        params={"commodity": "Paddy(Common)", "state": "West Bengal"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity"] == "Paddy(Common)"
    assert data["state"] == "West Bengal"
    assert data["modal_price"] == 2441.0
    assert data["market"] == "Khatra APMC"


# 4. Wrong state no fallback (e.g. Maize in West Bengal must NOT silently return Maharashtra)
def test_wrong_state_no_fallback():
    # Maize has records in Maharashtra, but 0 in West Bengal
    resp = test_client.get(
        "/api/market/current",
        params={"commodity": "Maize", "state": "West Bengal"}
    )
    assert resp.status_code == 404
    assert "No market data found for commodity 'Maize'" in resp.json()["detail"]
    assert "West Bengal" not in resp.text or "filters" in resp.json()["detail"]


# 5. Commodity mapping (canonical normalization)
def test_commodity_canonical_mapping():
    # Spaced variation: 'Paddy (Common)' must map to 'Paddy(Common)'
    r1 = test_client.get(
        "/api/market/current",
        params={"commodity": "Paddy (Common)", "state": "West Bengal"}
    )
    r2 = test_client.get(
        "/api/market/current",
        params={"commodity": "Paddy(Common)", "state": "West Bengal"}
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["modal_price"] == r2.json()["modal_price"] == 2441.0
    assert r1.json()["commodity"] == "Paddy(Common)"

    # Direct canonicalizer unit tests
    assert canonicalize_commodity("Paddy (Common)") == "Paddy(Common)"
    assert canonicalize_commodity("paddy") == "Paddy(Common)"
    assert canonicalize_commodity("rice") == "Paddy(Common)"
    assert canonicalize_commodity("corn") == "Maize"
    assert canonicalize_commodity("wheat") == "Wheat"
    assert get_commodity_display_name("Paddy(Common)") == "Paddy (Common)"


# 6-9. Forecast model evaluation on simulated adequate history
def test_forecast_models_with_sufficient_history():
    """Verify that all 4 models (ETS, moving_average, naive, arima) fit and predict."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    # Create 35 distinct days of observations to meet MIN_HISTORICAL_DAYS_REQUIRED (30)
    today = date.today()
    for i in range(35):
        obs_date = today - timedelta(days=35 - i)
        db.add(models.MarketObservation(
            state="West Bengal",
            district="Bankura",
            market="Khatra APMC",
            commodity="Paddy(Common)",
            variety="FAQ",
            grade="FAQ",
            min_price=2400.0 + (i * 2),
            max_price=2450.0 + (i * 2),
            modal_price=2425.0 + (i * 2),
            observation_date=obs_date,
        ))
    db.commit()

    service = ForecastService(db)

    # 6. ETS
    ets_result = asyncio.run(service.generate_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="ets",
        use_cache=False
    ))
    assert len(ets_result.forecast) == 7
    assert ets_result.model_name == "ETS_add_none_no"

    # 7. Moving Average
    ma_result = asyncio.run(service.generate_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="moving_average",
        use_cache=False
    ))
    assert len(ma_result.forecast) == 7
    assert ma_result.model_name == "MovingAverage_7"

    # 8. Naive
    naive_result = asyncio.run(service.generate_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="naive",
        use_cache=False
    ))
    assert len(naive_result.forecast) == 7
    assert naive_result.model_name == "Naive"

    # 9. ARIMA
    arima_result = asyncio.run(service.generate_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="arima",
        use_cache=False
    ))
    assert len(arima_result.forecast) == 7
    assert arima_result.model_name == "ARIMA_111_none"

    db.close()


# 10. Forecast cache isolation (commodity, model, location, horizon)
def test_forecast_cache_isolation():
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    service = ForecastService(db)
    today = date.today()

    # Pre-populate a cached 7-day ETS forecast for Paddy in West Bengal
    for day in range(1, 8):
        db.add(models.ForecastResult(
            commodity="Paddy(Common)",
            state="West Bengal",
            district=None,
            market=None,
            forecast_date=today,
            target_date=today + timedelta(days=day),
            horizon_days=day,
            predicted_modal_price=2500.0 + day,
            model_name="ETS_add_none_no"
        ))
    db.commit()

    # Hit: Exact match
    cached_hit = service._get_cached_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="ets",
        forecast_date=today
    )
    assert cached_hit is not None
    assert len(cached_hit.forecast) == 7
    assert cached_hit.model_name == "ETS_add_none_no"

    # Miss: Different model (Moving Average must NOT return ETS cache)
    cached_wrong_model = service._get_cached_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="West Bengal",
        model_type="moving_average",
        forecast_date=today
    )
    assert cached_wrong_model is None

    # Miss: Different state (Maharashtra must NOT return West Bengal cache)
    cached_wrong_state = service._get_cached_forecast(
        commodity="Paddy(Common)",
        horizon_days=7,
        state="Maharashtra",
        model_type="ets",
        forecast_date=today
    )
    assert cached_wrong_state is None

    # Miss: Different commodity (Maize must NOT return Paddy cache)
    cached_wrong_crop = service._get_cached_forecast(
        commodity="Maize",
        horizon_days=7,
        state="West Bengal",
        model_type="ets",
        forecast_date=today
    )
    assert cached_wrong_crop is None

    # Miss: Different horizon (14-day must NOT accept a 7-day cache)
    cached_wrong_horizon = service._get_cached_forecast(
        commodity="Paddy(Common)",
        horizon_days=14,
        state="West Bengal",
        model_type="ets",
        forecast_date=today
    )
    assert cached_wrong_horizon is None

    db.close()


# 11. Insufficient historical data handled cleanly
def test_insufficient_historical_data_returns_controlled_error():
    # In West Bengal, Paddy(Common) only has 7 records across 2 unique dates (requires 30)
    resp = test_client.get(
        "/api/market/forecast",
        params={
            "commodity": "Paddy(Common)",
            "state": "West Bengal",
            "model": "ets",
            "use_cache": False
        }
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "Insufficient historical data for forecasting" in detail
    assert "Need at least 30" in detail



# 12. Trend filtering
def test_trend_filtering_respects_commodity_and_location():
    # Paddy in WB has 7 points
    wb_trend = test_client.get(
        "/api/market/trend",
        params={"commodity": "Paddy(Common)", "state": "West Bengal"}
    )
    assert wb_trend.status_code == 200
    assert wb_trend.json()["commodity"] == "Paddy(Common)"
    assert wb_trend.json()["state"] == "West Bengal"
    assert wb_trend.json()["data_points"] == 7

    # Maize in WB has 0 points
    maize_wb = test_client.get(
        "/api/market/trend",
        params={"commodity": "Maize", "state": "West Bengal"}
    )
    assert maize_wb.status_code == 200
    assert maize_wb.json()["commodity"] == "Maize"
    assert maize_wb.json()["data_points"] == 0
    assert maize_wb.json()["trend"] == "insufficient_data"


# 13. Signal filtering
def test_signal_filtering_respects_commodity_and_location():
    wb_signals = test_client.get(
        "/api/market/signals",
        params={"commodity": "Paddy(Common)", "state": "West Bengal"}
    )
    assert wb_signals.status_code == 200
    wb_data = wb_signals.json()
    assert wb_data["commodity"] == "Paddy(Common)"
    assert wb_data["state"] == "West Bengal"
    assert wb_data["latest_price"] is not None
    assert wb_data["latest_price"]["commodity"] == "Paddy(Common)"
    assert wb_data["latest_price"]["state"] == "West Bengal"

    # Maize signals must not show Paddy data
    maize_signals = test_client.get(
        "/api/market/signals",
        params={"commodity": "Maize", "state": "West Bengal"}
    )
    assert maize_signals.status_code == 200
    maize_data = maize_signals.json()
    assert maize_data["commodity"] == "Maize"
    assert maize_data["latest_price"] is None


# 14. Refresh endpoint behavior
def test_refresh_endpoint_handles_parameters():
    with patch.object(MarketService, "fetch_and_store_latest_data", return_value=0) as mock_fetch:
        resp = test_client.post(
            "/api/market/refresh",
            params={"commodity": "Paddy (Common)", "state": "West Bengal", "limit": 10}
        )
        assert resp.status_code == 202
        assert resp.json()["status"] == "accepted"
        mock_fetch.assert_called_once()
        # Verify canonical commodity was passed to fetch
        _, kwargs = mock_fetch.call_args
        assert kwargs["commodity"] == "Paddy(Common)"
        assert kwargs["state"] == "West Bengal"


# 15. Commodities catalogue endpoint
def test_commodities_catalogue_endpoint():
    resp = test_client.get("/api/market/commodities", params={"state": "West Bengal"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "West Bengal"
    assert data["total"] > 0
    
    # Check that Paddy(Common) is marked available in West Bengal
    paddy_item = next((c for c in data["commodities"] if c["canonical_name"] == "Paddy(Common)"), None)
    assert paddy_item is not None
    assert paddy_item["is_available"] is True
    assert paddy_item["observation_count"] == 7

    # Check that Masur Dal is marked available in West Bengal
    masur_item = next((c for c in data["commodities"] if c["canonical_name"] == "Masur Dal"), None)
    assert masur_item is not None
    assert masur_item["is_available"] is True

    # Check that Maize is marked unavailable in West Bengal
    maize_item = next((c for c in data["commodities"] if c["canonical_name"] == "Maize"), None)
    assert maize_item is not None
    assert maize_item["is_available"] is False
    assert maize_item["observation_count"] == 0
    assert maize_item["total_nationwide"] == 4


# 16. Current price with granular district and market filters
def test_current_price_district_and_market_filters():
    # Masur Dal in Nadia, Chakdah APMC
    resp = test_client.get(
        "/api/market/current",
        params={
            "commodity": "Masur Dal",
            "state": "West Bengal",
            "district": "Nadia",
            "market": "Chakdah APMC",
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity"] == "Masur Dal"
    assert data["state"] == "West Bengal"
    assert data["district"] == "Nadia"
    assert data["market"] == "Chakdah APMC"
    assert data["modal_price"] == 11800.0

    # Non-existent market in Nadia returns 404
    resp_bad = test_client.get(
        "/api/market/current",
        params={
            "commodity": "Masur Dal",
            "state": "West Bengal",
            "district": "Nadia",
            "market": "FakeMarket99",
        }
    )
    assert resp_bad.status_code == 404


# 17. India-wide fallback when regional state has no data
def test_india_wide_fallback_for_regional_nodata():
    # Brinjal in West Bengal returns 404
    resp_wb = test_client.get(
        "/api/market/current",
        params={"commodity": "Brinjal", "state": "West Bengal"}
    )
    assert resp_wb.status_code == 404

    # India-wide fallback (regional state filter cleared) returns nationwide observation
    resp_nationwide = test_client.get(
        "/api/market/current",
        params={"commodity": "Brinjal"}
    )
    assert resp_nationwide.status_code == 200
    data = resp_nationwide.json()
    assert data["commodity"] == "Brinjal"
    assert data["state"] != "West Bengal"  # Must not claim to be West Bengal
    assert data["modal_price"] > 0


# 18. Cross-commodity and cross-state contamination protection
def test_cross_commodity_and_state_contamination_protection():
    # Requesting Masur Dal + West Bengal must NEVER return Paddy or Maharashtra
    resp = test_client.get(
        "/api/market/current",
        params={"commodity": "Masur Dal", "state": "West Bengal"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity"] == "Masur Dal"
    assert data["state"] == "West Bengal"
    assert "Paddy" not in data["commodity"]
    assert data["state"] != "Maharashtra"

    # Requesting an unavailable commodity in West Bengal must return 404, NOT another crop
    resp_cotton_wb = test_client.get(
        "/api/market/current",
        params={"commodity": "Cotton", "state": "West Bengal"}
    )
    assert resp_cotton_wb.status_code == 404


# 19. Historical data queries and ordering
def test_historical_prices_ordering_and_filtering():
    # Paddy in West Bengal has multiple dates
    resp = test_client.get(
        "/api/market/history",
        params={"commodity": "Paddy(Common)", "state": "West Bengal"}
    )
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 2
    # Verify records are sorted by date
    dates = [r["observation_date"] for r in records]
    assert dates == sorted(dates)

    # Date range filtering
    start = dates[0]
    resp_filtered = test_client.get(
        "/api/market/history",
        params={
            "commodity": "Paddy(Common)",
            "state": "West Bengal",
            "start_date": start,
            "end_date": start,
        }
    )
    assert resp_filtered.status_code == 200
    for r in resp_filtered.json():
        assert r["observation_date"] == start


# 20. Refresh idempotency and historical date preservation
def test_refresh_idempotency_and_preservation():
    from app.database.repository import MarketObservationRepository
    from app.database import models

    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    repo = MarketObservationRepository(db)

    record_day1 = {
        "state": "West Bengal",
        "district": "Nadia",
        "market": "Chakdah APMC",
        "commodity": "Masur Dal",
        "variety": "FAQ",
        "grade": "FAQ",
        "min_price": 11000.0,
        "max_price": 12000.0,
        "modal_price": 11800.0,
        "observation_date": date(2026, 9, 17),
        "source": "data.gov.in",
    }
    obs1 = repo.create_observation(record_day1)
    assert obs1.id is not None

    # Re-inserting the same observation should update, not create duplicate
    record_day1_updated = dict(record_day1, modal_price=11850.0)
    obs1_updated = repo.create_observation(record_day1_updated)
    assert obs1_updated.id == obs1.id
    assert obs1_updated.modal_price == 11850.0
    assert repo.count_observations("Masur Dal") == 1

    # Inserting a second date must preserve the first date and add the second
    record_day2 = dict(record_day1, observation_date=date(2026, 9, 18), modal_price=11900.0)
    obs2 = repo.create_observation(record_day2)
    assert obs2.id != obs1.id
    assert repo.count_observations("Masur Dal") == 2

    # Verify both dates exist in query
    all_obs = repo.get_observations_for_commodity("Masur Dal")
    assert len(all_obs) == 2
    dates = {o.observation_date for o in all_obs}
    assert dates == {date(2026, 9, 17), date(2026, 9, 18)}

    db.close()


# 21. Rejection across all 4 models when insufficient historical data (< 30 days)
@pytest.mark.parametrize("model_name", ["ets", "moving_average", "naive", "arima"])
def test_all_models_reject_insufficient_historical_data(model_name):
    resp = test_client.get(
        "/api/market/forecast",
        params={
            "commodity": "Masur Dal",
            "state": "West Bengal",
            "model": model_name,
            "use_cache": False,
        }
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "Insufficient historical data" in detail
    assert "Need at least 30" in detail


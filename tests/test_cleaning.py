"""
test_cleaning.py — Task 3.8

Each test checks one cleaning rule on a tiny hand-made table.
Run from the repo root:   pytest
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cleaning as c  # noqa: E402


def bike_rows(values, site="1", start="2025-01-01"):
    dates = pd.date_range(start, periods=len(values), freq="D")
    return pd.DataFrame({"site_id": site, "date": dates, "bikes_total": values,
                         "bikes_in": values, "bikes_out": 0.0, "source_file": "f.csv"})


def test_filter_cities_keeps_only_heidelberg_and_mannheim():
    df = pd.DataFrame({"domain_name": ["Stadt Heidelberg", "Stadt Mannheim", "Stadt Freiburg im Breisgau"]})
    out, _ = c.filter_cities.raw(df)
    assert len(out) == 2


def test_one_row_per_site_and_day_keeps_latest_file():
    df = pd.concat([bike_rows([10.0]).assign(source_file="a.csv"),
                    bike_rows([20.0]).assign(source_file="b.csv")])
    out, _ = c.deduplicate_site_day.raw(df)
    assert len(out) == 1 and out["bikes_total"].iloc[0] == 20


def test_negative_counts_become_null():
    out, _ = c.invalid_counts_to_null.raw(bike_rows([5.0, -3.0]))
    assert out["bikes_total"].isna().sum() == 1


def test_three_zero_days_are_an_outage_but_one_zero_day_is_kept():
    out, _ = c.flag_outages.raw(bike_rows([50.0, 0.0, 0.0, 0.0, 40.0, 0.0, 30.0]))
    assert out["is_outage"].sum() == 3
    assert out["is_zero"].sum() == 1
    assert out["bikes_total"].isna().sum() == 3      # outage set to NULL, not 0


def test_missing_days_are_added_as_null_not_zero():
    df = bike_rows([10.0, 12.0, 14.0]).drop(index=1)  # day 2 missing
    for col in ["site_name", "city", "counter_serial", "is_outage", "is_zero", "is_outlier"]:
        df[col] = False if col.startswith("is_") else "x"
    out, _ = c.complete_calendar.raw(df)
    assert len(out) == 3
    assert out["is_missing"].sum() == 1
    assert pd.isna(out.loc[out["is_missing"], "bikes_total"]).all()


def test_weather_prefers_historical_over_recent():
    w = pd.DataFrame({"MESS_DATUM": ["20250501", "20250501"], "TMK": ["10.0", "11.0"],
                      "source_priority": [0, 1]})   # 0 = historical
    out, _ = c.combine_weather_sources.raw(w)
    assert len(out) == 1 and out["TMK"].iloc[0] == "10.0"


def test_weather_minus_999_becomes_null():
    w = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
                      "TMK": ["3.2", "-999"], "RSK": ["0.0", "2.5"]})
    out, _ = c.clean_weather_values.raw(w)
    assert out["temp_mean_c"].isna().sum() == 1
    assert (out["temp_mean_c"] != -999).all()
    assert out["is_rainy"].tolist() == [False, True]


def test_holidays_and_weekends():
    df = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-04", "2025-01-07"])})
    out = c.add_calendar_features(df)
    assert out["is_holiday"].tolist() == [True, False, False]     # New Year
    assert out["is_weekend"].tolist() == [False, True, False]     # Saturday


def test_weekly_total_is_null_when_no_valid_day():
    m = pd.DataFrame({"site_id": "1", "site_name": "x", "city": "Heidelberg",
                      "date": pd.date_range("2025-01-06", periods=14, freq="D"),
                      "bikes_total": [np.nan] * 7 + [10.0] * 7, "temp_mean_c": 5.0, "precip_mm": 0.0})
    out = c.aggregate_weekly(m)
    assert pd.isna(out["bikes_total"].iloc[0]) and out["valid_days"].iloc[0] == 0   # unknown, not 0
    assert out["bikes_total"].iloc[1] == 70


def test_pipeline_output_on_real_data_if_present():
    """Runs on the downloaded data: key is unique and no -999 is left."""
    if not list(c.RAW_BIKE.glob("fahrradzaehler_tageswerten_*.csv")):
        return
    tables, _ = c.run_pipeline(2025, write=False)
    counts, weather = tables["daily_counts"], tables["weather_daily"]
    assert not counts.duplicated(["site_id", "date"]).any()
    assert not (weather.select_dtypes("number") == -999).any().any()
    assert (counts["bikes_total"].dropna() >= 0).all()
    assert tables["model_table"]["city"].notna().all()

def test_outlier_is_flagged_but_value_kept():
    out, _ = c.flag_outliers.raw(bike_rows([100.0] * 20 + [5000.0]))
    assert out["is_outlier"].sum() == 1
    assert out["bikes_total"].max() == 5000          # flag only, value kept


def test_outlier_threshold_is_per_site():
    big = bike_rows([3000.0] * 20, site="big")
    small = bike_rows([100.0] * 19 + [3000.0], site="small")
    out, _ = c.flag_outliers.raw(pd.concat([big, small], ignore_index=True))
    assert out.loc[out["site_id"] == "big", "is_outlier"].sum() == 0    # normal for the big site
    assert out.loc[out["site_id"] == "small", "is_outlier"].sum() == 1  # extreme for the small site


def test_text_na_becomes_null_and_date_is_berlin_day():
    raw = pd.DataFrame({
        "counter_site_id": ["1"], "counter_site": ["x"], "domain_name": ["Stadt Mannheim"],
        "channels_in": ["na"], "channels_out": ["na"], "channels_all": ["5846"],
        "latitude": ["49.5"], "longitude": ["8.4"],
        "iso_timestamp": ["2025-06-01T00:00:00+02:00"],      # = 31 May 22:00 UTC
    })
    out, _ = c.standardise_types.raw(raw)
    assert out["bikes_in"].isna().all()                       # "na" -> NULL
    assert out["bikes_total"].iloc[0] == 5846                 # text -> number
    assert out["date"].iloc[0] == pd.Timestamp("2025-06-01")  # Berlin day, not the UTC day
    assert out["city"].iloc[0] == "Mannheim"                  # "Stadt " removed


def test_join_does_not_change_row_count():
    counts = bike_rows([1.0, 2.0, 3.0])
    sites = pd.DataFrame({"site_id": ["1"], "site_name": ["x"], "city": ["Heidelberg"]})
    weather = pd.DataFrame({"date": counts["date"], "temp_mean_c": [1.0, 2.0, 3.0]})
    out, _ = c.build_model_table.raw(counts, sites, weather)
    assert len(out) == len(counts)


def test_duplicate_site_key_stops_the_join():
    counts = bike_rows([1.0])
    sites = pd.DataFrame({"site_id": ["1", "1"], "site_name": ["x", "y"], "city": ["Heidelberg"] * 2})
    weather = pd.DataFrame({"date": counts["date"], "temp_mean_c": [1.0]})
    with pytest.raises(pd.errors.MergeError):
        c.build_model_table.raw(counts, sites, weather)

if not list(c.RAW_BIKE.glob("fahrradzaehler_tageswerten_*.csv")):
        pytest.skip("raw data not downloaded")
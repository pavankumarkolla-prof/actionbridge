"""Tests for the SCANIA Component X loader."""

from pathlib import Path

import pytest

from actionbridge.data import scania
from actionbridge.orchestration import ActionChannel, Action
from actionbridge.pipeline import Pipeline


SAMPLE_CSV = Path(__file__).parent.parent / "data" / "samples" / "scania_sample.csv"


def test_sample_csv_exists():
    assert SAMPLE_CSV.exists(), f"sample CSV missing at {SAMPLE_CSV}"


def test_load_csv_returns_records():
    records = scania.load_csv(SAMPLE_CSV)
    assert len(records) > 0
    # First record is a healthy truck_001 reading
    first = records[0]
    assert first.telemetry.asset_id == "truck_001"
    assert first.telemetry.timestamp == 3600
    assert not first.is_failure


def test_load_csv_picks_up_failure_labels():
    records = scania.load_csv(SAMPLE_CSV)
    n_failures = sum(1 for r in records if r.is_failure)
    # The sample includes 2 failure events (truck_001 and truck_003)
    assert n_failures == 2


def test_load_csv_extracts_features():
    records = scania.load_csv(SAMPLE_CSV)
    r = records[0]
    assert r.telemetry.feature_names == (
        "feature_engine_temp",
        "feature_oil_pressure",
        "feature_vibration",
        "feature_load",
        "feature_rpm_norm",
    )
    assert len(r.telemetry.features) == 5
    # Feature lookup by name works
    assert r.telemetry.get("feature_engine_temp") == 0.32


def test_load_csv_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        scania.load_csv("/nonexistent/path.csv")


def test_to_asset_specs_dedupes_components():
    records = scania.load_csv(SAMPLE_CSV)
    specs = scania.to_asset_specs(records)
    assert set(specs.keys()) == {"truck_001", "truck_002", "truck_003"}
    assert all(s.sector == "discrete_manufacturing" for s in specs.values())


def test_evaluate_routing_against_failures():
    """End-to-end: load real-format sample, run pipeline, score routing."""
    records = scania.load_csv(SAMPLE_CSV)
    specs = scania.to_asset_specs(records)
    pipeline = Pipeline(assets=specs, theta_pro=0.55, theta_re=0.30)
    actions = pipeline.run([r.telemetry for r in records])
    metrics = scania.evaluate_routing(records, actions)
    assert metrics["n_failures"] == 2
    assert metrics["n_proactive_actions"] >= 0
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0


def test_evaluate_routing_handles_empty_actions():
    metrics = scania.evaluate_routing(records=[], actions=[])
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["n_failures"] == 0

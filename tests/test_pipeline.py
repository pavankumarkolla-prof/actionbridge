"""End-to-end tests for the four-stage pipeline (Eq. 2)."""

from actionbridge.pipeline import Pipeline, ingest, intelligence
from actionbridge.telemetry import Telemetry, AssetSpec
from actionbridge.orchestration import ActionChannel


def _telemetry(asset_id, t, value):
    return Telemetry(asset_id=asset_id, timestamp=t, features=(value,))


def test_ingest_dedupes_duplicate_timestamps():
    stream = [
        _telemetry("a1", 1, 0.1),
        _telemetry("a1", 1, 0.9),  # later one wins
        _telemetry("a1", 2, 0.5),
    ]
    out = ingest(stream)
    assert len(out) == 2
    assert out[0].features == (0.9,)


def test_ingest_sorts_by_asset_then_time():
    stream = [
        _telemetry("b", 2, 0.5),
        _telemetry("a", 1, 0.2),
        _telemetry("a", 2, 0.6),
    ]
    out = ingest(stream)
    assert [(t.asset_id, t.timestamp) for t in out] == [("a", 1), ("a", 2), ("b", 2)]


def test_intelligence_produces_score_per_telemetry():
    assets = {
        "a1": AssetSpec(asset_id="a1", criticality=0.5, sector="general_manufacturing"),
    }
    out = intelligence([_telemetry("a1", 1, 0.7), _telemetry("a1", 2, 0.3)], assets)
    assert len(out) == 2
    assert all(0 <= score <= 1 for _, _, score in out)


def test_pipeline_routes_high_signal_to_proactive():
    assets = {
        "press_03": AssetSpec(
            asset_id="press_03",
            downtime_cost=5000.0,
            criticality=0.9,
            sector="discrete_manufacturing",
        ),
    }
    pipeline = Pipeline(assets=assets, theta_pro=0.55, theta_re=0.30)
    actions = pipeline.run([_telemetry("press_03", 100, 0.95)])
    assert len(actions) == 1
    assert actions[0].channel == ActionChannel.PROACTIVE


def test_pipeline_skips_unregistered_assets():
    assets = {"known": AssetSpec(asset_id="known")}
    pipeline = Pipeline(assets=assets)
    actions = pipeline.run([_telemetry("unknown", 1, 0.9)])
    assert actions == []


def test_pipeline_action_emitter_called():
    assets = {"a1": AssetSpec(asset_id="a1")}
    received: list = []
    pipeline = Pipeline(
        assets=assets, theta_pro=0.55, theta_re=0.30,
        action_emitter=received.append,
    )
    pipeline.run([_telemetry("a1", 1, 0.9)])
    assert len(received) == 1

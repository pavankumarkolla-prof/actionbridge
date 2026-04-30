"""Four-stage pipeline composition — Eq. 2.

A = Phi_act ( Phi_orch ( Phi_int ( Phi_ing (D) ) ) )

The package ships minimal reference implementations of Phi_ing (ingestion:
schema enforcement + per-asset deduplication) and Phi_int (intelligence:
a pluggable failure-probability scorer with a default heuristic baseline).
Phi_orch comes from `orchestration.orchestrate`. Phi_act is a pluggable
"emit to CRM" hook (default: collect into a list — replace in production
with a real Salesforce / Dynamics / ServiceNow REST adapter).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from actionbridge.telemetry import Telemetry, AssetSpec
from actionbridge.scs import scs, SCSWeights
from actionbridge.orchestration import orchestrate, Action


class FailureProbabilityModel(Protocol):
    """Phi_int's ML core. Production deployments inject a trained model."""

    def predict(self, telemetry: Telemetry) -> float: ...

    def remaining_useful_life(self, telemetry: Telemetry) -> float: ...


def _heuristic_p_fail(telemetry: Telemetry) -> float:
    """Default scorer: max-feature normalisation, clipped to [0, 1].

    Useful as a baseline for unit tests and the H100-style demo. Replace
    with a real PdM model (LSTM, XGBoost, transformer-based RUL) in
    production.
    """
    if not telemetry.features:
        return 0.0
    return max(0.0, min(1.0, max(telemetry.features)))


def _heuristic_rul(telemetry: Telemetry) -> float:
    """Default RUL: 168 - 168 * max-feature, in hours."""
    if not telemetry.features:
        return 168.0
    return max(0.0, 168.0 - 168.0 * max(telemetry.features))


@dataclass
class _DefaultModel:
    def predict(self, telemetry: Telemetry) -> float:
        return _heuristic_p_fail(telemetry)

    def remaining_useful_life(self, telemetry: Telemetry) -> float:
        return _heuristic_rul(telemetry)


def ingest(stream: Iterable[Telemetry]) -> list[Telemetry]:
    """Phi_ing — normalisation + deduplication + schema enforcement.

    Default: drop duplicate (asset_id, timestamp) pairs (last writer wins).
    """
    seen: dict[tuple[str, int], Telemetry] = {}
    for t in stream:
        seen[(t.asset_id, t.timestamp)] = t
    return sorted(seen.values(), key=lambda t: (t.asset_id, t.timestamp))


def intelligence(
    telemetry: list[Telemetry],
    assets: dict[str, AssetSpec],
    model: FailureProbabilityModel | None = None,
    weights_override: SCSWeights | None = None,
) -> list[tuple[str, int, float]]:
    """Phi_int — produce the signal set S = {(asset_id, t, SCS)}."""
    model = model or _DefaultModel()
    out: list[tuple[str, int, float]] = []
    for t in telemetry:
        spec = assets.get(t.asset_id)
        if spec is None:
            continue
        p_fail = model.predict(t)
        rul = model.remaining_useful_life(t)
        score = scs(
            p_fail=p_fail,
            downtime_severity=spec.criticality,
            rul_hours=rul,
            weights=weights_override,
            sector=spec.sector,
        )
        out.append((t.asset_id, t.timestamp, score))
    return out


@dataclass
class Pipeline:
    """The full ActionBridge pipeline (Eq. 2)."""

    assets: dict[str, AssetSpec]
    theta_pro: float = 0.65
    theta_re: float = 0.40
    model: FailureProbabilityModel | None = None
    weights_override: SCSWeights | None = None
    action_emitter: Callable[[Action], None] | None = None

    def run(self, raw_stream: Iterable[Telemetry]) -> list[Action]:
        ingested = ingest(raw_stream)
        signals = intelligence(
            ingested, self.assets,
            model=self.model,
            weights_override=self.weights_override,
        )
        actions = orchestrate(signals, self.theta_pro, self.theta_re)
        if self.action_emitter:
            for a in actions:
                self.action_emitter(a)
        return actions

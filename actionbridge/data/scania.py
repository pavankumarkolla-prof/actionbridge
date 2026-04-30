"""SCANIA Component X loader.

The SCANIA Component X dataset (Scientific Data, 2024; arXiv:2401.15199)
is 23 months of real operational data from anonymised truck components,
with run-to-failure labels. We use it to validate the Signal Criticality
Score scoring + Algorithm 1 routing on real industrial telemetry rather
than synthetic data.

The dataset's canonical CSV schema (after the authors' standardisation)
is approximately:

    component_id,timestamp,feature_001,feature_002,...,feature_F,
    is_failure,rul_hours

This loader reads that schema and emits ActionBridge Telemetry +
AssetSpec records. For users who haven't downloaded the full dataset
(several GB), data/samples/scania_sample.csv ships a small synthetic
slice that exercises the same code path.

Download: https://researchdata.scania.com  (CC BY 4.0)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from actionbridge.telemetry import Telemetry, AssetSpec


@dataclass
class ScaniaRecord:
    """One row from the SCANIA CSV: telemetry + ground-truth labels.

    Tests can compare the SCS-driven action against `is_failure` /
    `rul_hours` to compute precision, recall, and lead-time metrics.
    """
    telemetry: Telemetry
    is_failure: bool
    rul_hours: float | None


def _detect_feature_columns(header: list[str]) -> list[str]:
    """Identify feature columns (excluding ID, timestamp, labels)."""
    excluded = {
        "component_id", "asset_id", "id",
        "timestamp", "time", "t",
        "is_failure", "failure", "label",
        "rul_hours", "rul",
    }
    return [c for c in header if c.lower() not in excluded]


def load_csv(path: str | Path) -> list[ScaniaRecord]:
    """Load a SCANIA-format CSV, return one ScaniaRecord per row.

    Args:
        path: path to the CSV file. Schema must include component_id,
              timestamp, feature columns, and at minimum is_failure.

    Returns:
        list of ScaniaRecord, in file order (sorting is the caller's job).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"SCANIA CSV not found at {p}")

    records: list[ScaniaRecord] = []
    with p.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return records
        feature_cols = _detect_feature_columns(reader.fieldnames)
        for row in reader:
            features = tuple(float(row[c]) for c in feature_cols)
            telemetry = Telemetry(
                asset_id=row.get("component_id", row.get("asset_id", "")),
                timestamp=int(float(row.get("timestamp", row.get("time", 0)))),
                features=features,
                feature_names=tuple(feature_cols),
            )
            is_failure_raw = row.get("is_failure", row.get("failure", "0"))
            is_failure = str(is_failure_raw).strip() in {"1", "True", "true"}
            rul_raw = row.get("rul_hours", row.get("rul", ""))
            rul = float(rul_raw) if rul_raw not in (None, "") else None
            records.append(ScaniaRecord(
                telemetry=telemetry, is_failure=is_failure, rul_hours=rul,
            ))
    return records


def to_asset_specs(
    records: list[ScaniaRecord],
    downtime_cost_per_hour: float = 250.0,
    sector: str = "discrete_manufacturing",
) -> dict[str, AssetSpec]:
    """Build an AssetSpec dict for the unique components in the dataset.

    SCANIA Component X is anonymised, so we apply uniform downtime-cost
    assumptions across components. Production users would override these
    on a per-component basis from their own fleet management system.
    """
    specs: dict[str, AssetSpec] = {}
    for r in records:
        aid = r.telemetry.asset_id
        if aid not in specs:
            specs[aid] = AssetSpec(
                asset_id=aid,
                downtime_cost=downtime_cost_per_hour,
                criticality=0.7,
                sector=sector,
            )
    return specs


def evaluate_routing(
    records: list[ScaniaRecord],
    actions,
    proactive_window_hours: float = 72.0,
) -> dict[str, float]:
    """Score the SCS-driven routing against SCANIA's failure labels.

    Computes:
        precision  — fraction of PROACTIVE actions whose component
                     subsequently failed within proactive_window_hours
        recall     — fraction of actual failures that received a PROACTIVE
                     or REACTIVE action ahead of the failure timestamp
        lead_time_h — median hours of warning provided by PROACTIVE actions

    Args:
        records: ScaniaRecord ground truth, in time order per component.
        actions: list[Action] returned from a Pipeline.run() call.
        proactive_window_hours: how far ahead PROACTIVE must fire to count
                                as correct.

    Returns:
        dict with precision, recall, lead_time_hours, n_actions, n_failures.
    """
    from actionbridge.orchestration import ActionChannel

    failures_by_asset: dict[str, list[int]] = {}
    for r in records:
        if r.is_failure:
            failures_by_asset.setdefault(r.telemetry.asset_id, []).append(r.telemetry.timestamp)

    proactive_actions = [a for a in actions if a.channel == ActionChannel.PROACTIVE]
    reactive_actions = [a for a in actions if a.channel == ActionChannel.REACTIVE]

    proactive_correct = 0
    lead_times: list[float] = []
    for a in proactive_actions:
        future_failures = [
            t for t in failures_by_asset.get(a.asset_id, [])
            if 0 < t - a.timestamp <= proactive_window_hours * 3600
        ]
        if future_failures:
            proactive_correct += 1
            lead = (min(future_failures) - a.timestamp) / 3600.0
            lead_times.append(lead)

    n_failures = sum(len(v) for v in failures_by_asset.values())
    covered_failures = 0
    for asset_id, times in failures_by_asset.items():
        for t in times:
            if any(
                a.asset_id == asset_id and a.timestamp <= t
                for a in (proactive_actions + reactive_actions)
            ):
                covered_failures += 1

    precision = proactive_correct / len(proactive_actions) if proactive_actions else 0.0
    recall = covered_failures / n_failures if n_failures else 0.0
    median_lead = sorted(lead_times)[len(lead_times) // 2] if lead_times else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "lead_time_hours_median": median_lead,
        "n_proactive_actions": len(proactive_actions),
        "n_reactive_actions": len(reactive_actions),
        "n_failures": n_failures,
    }

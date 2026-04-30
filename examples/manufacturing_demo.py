"""ActionBridge end-to-end demo on a small manufacturing fleet.

Models a 5-asset shop floor with rising vibration on one critical press.
Shows the pipeline routing signals to PROACTIVE / REACTIVE / DEFER channels
and computes a Delta-CTS reduction ratio against a "no-PdM" baseline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from actionbridge import (
    AssetSpec,
    CostToServe,
    Pipeline,
    Telemetry,
    delta_cts,
)
from actionbridge.orchestration import ActionChannel


def build_fleet() -> dict[str, AssetSpec]:
    return {
        "press_01": AssetSpec(asset_id="press_01", downtime_cost=1500, criticality=0.6, sector="discrete_manufacturing"),
        "press_02": AssetSpec(asset_id="press_02", downtime_cost=1500, criticality=0.6, sector="discrete_manufacturing"),
        "press_03": AssetSpec(asset_id="press_03", downtime_cost=5000, criticality=0.95, sector="discrete_manufacturing"),
        "cnc_01":   AssetSpec(asset_id="cnc_01",   downtime_cost=800,  criticality=0.4, sector="high_mix_low_volume"),
        "reactor":  AssetSpec(asset_id="reactor",  downtime_cost=12000, criticality=0.98, sector="process_manufacturing"),
    }


def synthetic_telemetry() -> list[Telemetry]:
    """5 assets x 4 timesteps. press_03 vibration ramps; reactor temperature spikes."""
    stream = []
    # Healthy assets: low feature values
    for asset in ("press_01", "press_02", "cnc_01"):
        for t in range(100, 104):
            stream.append(Telemetry(asset_id=asset, timestamp=t, features=(0.20 + 0.01 * (t - 100),)))
    # press_03: rising vibration -> high SCS expected
    for i, t in enumerate(range(100, 104)):
        stream.append(Telemetry(asset_id="press_03", timestamp=t, features=(0.55 + 0.10 * i,)))
    # reactor: sudden temperature event at t=103
    stream.append(Telemetry(asset_id="reactor", timestamp=100, features=(0.30,)))
    stream.append(Telemetry(asset_id="reactor", timestamp=101, features=(0.32,)))
    stream.append(Telemetry(asset_id="reactor", timestamp=102, features=(0.35,)))
    stream.append(Telemetry(asset_id="reactor", timestamp=103, features=(0.92,)))
    return stream


def main() -> None:
    print("ActionBridge — Manufacturing Demo")
    print("=" * 50)

    fleet = build_fleet()
    pipeline = Pipeline(assets=fleet, theta_pro=0.55, theta_re=0.30)
    actions = pipeline.run(synthetic_telemetry())

    counts = {c: 0 for c in ActionChannel}
    for a in actions:
        counts[a.channel] += 1

    print(f"\nFleet: {len(fleet)} assets, {len(actions)} actions emitted")
    for c in ActionChannel:
        print(f"  {c.value:10s}: {counts[c]}")

    print("\nTop 5 actions by SCS:")
    for a in actions[:5]:
        print(f"  {a.asset_id:10s}  t={a.timestamp}  SCS={a.scs:.3f}  -> {a.channel.value}")

    # Delta-CTS: pre = "no PdM", post = "ActionBridge deployed".
    pre = [
        CostToServe(asset_id="press_01", maintenance=8000, downtime=2200, warranty=900, service=600, inventory=400),
        CostToServe(asset_id="press_02", maintenance=8000, downtime=2200, warranty=900, service=600, inventory=400),
        CostToServe(asset_id="press_03", maintenance=12000, downtime=8000, warranty=2200, service=1500, inventory=900),
        CostToServe(asset_id="cnc_01",   maintenance=5000, downtime=1100, warranty=400, service=300, inventory=200),
        CostToServe(asset_id="reactor",  maintenance=18000, downtime=22000, warranty=4000, service=2800, inventory=1400),
    ]
    post = [
        CostToServe(asset_id="press_01", maintenance=6500, downtime=1800, warranty=750, service=500, inventory=370),
        CostToServe(asset_id="press_02", maintenance=6500, downtime=1800, warranty=750, service=500, inventory=370),
        CostToServe(asset_id="press_03", maintenance=8500, downtime=4200, warranty=1500, service=900, inventory=820),
        CostToServe(asset_id="cnc_01",   maintenance=4400, downtime=900, warranty=350, service=240, inventory=180),
        CostToServe(asset_id="reactor",  maintenance=13000, downtime=12500, warranty=2700, service=2000, inventory=1300),
    ]
    delta = delta_cts(pre, post)
    print(f"\nDelta-CTS (fleet aggregate, illustrative): {delta:.3f}")
    print(f"  Pre  total: ${sum(c.total() for c in pre):>10,.0f}")
    print(f"  Post total: ${sum(c.total() for c in post):>10,.0f}")
    print(f"  Reduction:  ${sum(c.total() for c in pre) - sum(c.total() for c in post):>10,.0f} ({delta * 100:.1f}%)")


if __name__ == "__main__":
    main()

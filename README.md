# ActionBridge

> Reference implementation for *ActionBridge: A Signal-to-Action Reference
> Architecture Integrating IoT Telemetry, Cloud ML, and CRM for Cost-to-Serve
> Reduction and U.S. Manufacturing Reshoring.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Status: Research](https://img.shields.io/badge/status-research-lightgrey.svg)](#status)

U.S. manufacturers reshoring decisions hinge less on labor costs than on
the *non-labor* portion of cost-to-serve: warranty, downtime, customer-
service overhead, and inventory carry. ActionBridge is a four-stage
reference architecture (Ingestion → Intelligence → Orchestration → Action)
that maps IIoT telemetry, cloud-hosted ML, and CRM workflow automation to
quantifiable reductions in those cost components.

This repository is the reference implementation accompanying the paper.

## Paper

- **Title:** ActionBridge: A Signal-to-Action Reference Architecture
  Integrating IoT Telemetry, Cloud ML, and CRM for Cost-to-Serve Reduction
  and U.S. Manufacturing Reshoring
- **Author:** Pavan Kumar Kolla
- **PDF:** *(arXiv link to be added after submission)*

## What this implements

| Concept (paper) | Module |
|---|---|
| Telemetry stream $\mathcal{D} = \{d_{i,t}\}$, asset metadata | [`actionbridge/telemetry.py`](actionbridge/telemetry.py) |
| Pipeline composition $\mathcal{A} = \Phi_{\mathrm{act}} \circ \Phi_{\mathrm{orch}} \circ \Phi_{\mathrm{int}} \circ \Phi_{\mathrm{ing}}$ (Eq. 2) | [`actionbridge/pipeline.py`](actionbridge/pipeline.py) |
| Cost-to-Serve decomposition (Eq. 5) and Delta-CTS reduction ratio (Eq. 6) | [`actionbridge/cts.py`](actionbridge/cts.py) |
| Signal Criticality Score, SCS (Eq. 7) with sector-calibrated weights | [`actionbridge/scs.py`](actionbridge/scs.py) |
| Orchestration routing — Algorithm 1 | [`actionbridge/orchestration.py`](actionbridge/orchestration.py) |

## Install

```bash
git clone https://github.com/pavankumarkolla-prof/actionbridge.git
cd actionbridge
pip install -e .
```

ActionBridge has zero hard dependencies — `pytest` for tests is optional.

## Quick start

```python
from actionbridge import Pipeline, AssetSpec, Telemetry

fleet = {
    "press_03": AssetSpec(
        asset_id="press_03",
        downtime_cost=5000,
        criticality=0.95,
        sector="discrete_manufacturing",
    ),
}
pipeline = Pipeline(assets=fleet, theta_pro=0.65, theta_re=0.40)
actions = pipeline.run([
    Telemetry(asset_id="press_03", timestamp=100, features=(0.92,)),
])
print(actions[0].channel)  # ActionChannel.PROACTIVE
```

## Reproducing the manufacturing demo

The paper's Section V scenario walk-through is provided as a runnable example:

```bash
python examples/manufacturing_demo.py
```

It builds a 5-asset fleet, replays a synthetic telemetry stream culminating
in a critical-press fault and a reactor temperature spike, and reports
both the action routing and a Delta-CTS reduction figure.

## Calibrating SCS weights

The paper defines the Signal Criticality Score as

$$\mathrm{SCS}(d_{i,t}) = \alpha \cdot \hat{p}^{\mathrm{fail}}_{i,t} + \beta \cdot \phi(C^{\mathrm{down}}_{i}) + \gamma \cdot \psi(\mathrm{RUL}_{i,t}), \quad \alpha+\beta+\gamma = 1.$$

The package ships sector-specific defaults in
[`actionbridge/scs.py`](actionbridge/scs.py):

| Sector | $\alpha$ | $\beta$ | $\gamma$ | Rationale |
|---|---|---|---|---|
| `discrete_manufacturing`  | 0.55 | 0.25 | 0.20 | failure-driven |
| `process_manufacturing`   | 0.30 | 0.55 | 0.15 | downtime-cost-driven |
| `high_mix_low_volume`     | 0.30 | 0.20 | 0.50 | RUL-urgency-driven |
| `general_manufacturing`   | 0.40 | 0.35 | 0.25 | balanced default |

These defaults are *examples*, not gospel. Operators should re-calibrate
on pilot data; pass an explicit `SCSWeights(alpha=..., beta=..., gamma=...)`
override.

## Tests

```bash
pip install pytest
pytest
```

Covers SCS weighting & decay, CTS decomposition arithmetic, orchestration
routing thresholds, and end-to-end pipeline behaviour.

## Repository layout

```
actionbridge/
├── actionbridge/
│   ├── __init__.py        # Public API
│   ├── telemetry.py       # Telemetry, AssetSpec
│   ├── cts.py             # Cost-to-Serve (Eq. 5) + Delta-CTS (Eq. 6)
│   ├── scs.py             # Signal Criticality Score (Eq. 7)
│   ├── orchestration.py   # Algorithm 1 (proactive/reactive/defer routing)
│   └── pipeline.py        # Phi_ing -> Phi_int -> Phi_orch (Eq. 2)
├── examples/
│   └── manufacturing_demo.py
├── tests/
│   ├── test_scs.py
│   ├── test_cts.py
│   ├── test_orchestration.py
│   └── test_pipeline.py
├── setup.py
├── README.md
└── LICENSE
```

## Status

Research prototype. The math matches the paper and tests pass on the
reference fleet, but the framework has not been validated against
production manufacturing telemetry — that is explicit future work
(see paper's Limitations section). Bug reports and validation studies
welcome.

## Citation

```bibtex
@article{kolla2026actionbridge,
  title  = {{ActionBridge}: A Signal-to-Action Reference Architecture Integrating IoT Telemetry, Cloud ML, and CRM for Cost-to-Serve Reduction and U.S. Manufacturing Reshoring},
  author = {Kolla, Pavan Kumar},
  year   = {2026},
  note   = {Preprint; arXiv link to be added}
}
```

## License

MIT — see [LICENSE](LICENSE).

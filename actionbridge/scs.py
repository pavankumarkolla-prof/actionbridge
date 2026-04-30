"""Signal Criticality Score (SCS) — Eq. 7 of the paper.

SCS(d_{i,t}) = alpha * p_fail + beta * phi(C^down_i) + gamma * psi(RUL_{i,t})

where alpha + beta + gamma = 1, all weights in [0, 1]. The transform psi is
monotonically decreasing in remaining useful life; default psi(r) = exp(-lambda * r)
with deployment-tuneable lambda.

Calibration note: the paper deliberately leaves alpha, beta, gamma to be
calibrated per industry sector. This module ships sector-specific defaults
(SECTOR_WEIGHTS) derived from the rationale in the paper:
- Discrete manufacturing leans on failure probability (high alpha)
- Process manufacturing leans on downtime cost (high beta) because lost
  batch throughput dominates the cost equation
- High-mix low-volume leans on RUL urgency (high gamma) because spare
  parts have long lead times
These defaults are *examples*, not gospel — operators should re-calibrate
on their own pilot data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SCSWeights:
    """alpha, beta, gamma — must sum to 1.

    alpha: weight on ML-estimated failure probability
    beta:  weight on normalized downtime-cost severity
    gamma: weight on RUL-urgency transform
    """
    alpha: float
    beta: float
    gamma: float

    def __post_init__(self) -> None:
        for name in ("alpha", "beta", "gamma"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1], got {value}")
        s = self.alpha + self.beta + self.gamma
        if abs(s - 1.0) > 1e-6:
            raise ValueError(f"weights must sum to 1, got {s}")


SECTOR_WEIGHTS: dict[str, SCSWeights] = {
    "discrete_manufacturing": SCSWeights(alpha=0.55, beta=0.25, gamma=0.20),
    "process_manufacturing":  SCSWeights(alpha=0.30, beta=0.55, gamma=0.15),
    "high_mix_low_volume":    SCSWeights(alpha=0.30, beta=0.20, gamma=0.50),
    "general_manufacturing":  SCSWeights(alpha=0.40, beta=0.35, gamma=0.25),
}


def psi_exponential_decay(rul_hours: float, lam: float = 0.01) -> float:
    """psi(RUL) = exp(-lambda * RUL) — bounded to [0, 1].

    Default lambda = 0.01 corresponds to ~half decay over 70 hours, which
    matches the paper's default failure-probability horizon tau = 72h.
    """
    if rul_hours < 0:
        raise ValueError(f"RUL must be >= 0, got {rul_hours}")
    if lam <= 0:
        raise ValueError(f"lambda must be > 0, got {lam}")
    return math.exp(-lam * rul_hours)


def scs(
    p_fail: float,
    downtime_severity: float,
    rul_hours: float,
    weights: SCSWeights | None = None,
    sector: str = "general_manufacturing",
    lam: float = 0.01,
) -> float:
    """Signal Criticality Score (Eq. 7).

    Args:
        p_fail:            ML-estimated failure probability in [0, 1] within
                           the default horizon tau = 72h.
        downtime_severity: phi(C^down_i) in [0, 1] — normalized severity.
        rul_hours:         estimated remaining useful life in hours.
        weights:           override the per-sector default SCSWeights.
        sector:            sector key into SECTOR_WEIGHTS (used if weights=None).
        lam:               decay constant for psi (default 0.01).

    Returns:
        SCS in [0, 1].
    """
    if not 0.0 <= p_fail <= 1.0:
        raise ValueError(f"p_fail must be in [0,1], got {p_fail}")
    if not 0.0 <= downtime_severity <= 1.0:
        raise ValueError(f"downtime_severity must be in [0,1], got {downtime_severity}")

    w = weights or SECTOR_WEIGHTS.get(sector, SECTOR_WEIGHTS["general_manufacturing"])
    psi_value = psi_exponential_decay(rul_hours, lam=lam)
    return w.alpha * p_fail + w.beta * downtime_severity + w.gamma * psi_value

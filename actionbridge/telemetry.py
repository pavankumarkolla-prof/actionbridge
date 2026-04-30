"""Telemetry: discrete-time sensor observations from monitored assets.

Implements the formal model from Section III-A of the paper:
    D = { d_{i,t} | i in {1..N}, t in Z+ }
where each d_{i,t} in R^F is a vector of F sensor features.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Telemetry:
    """A single telemetry observation d_{i,t}.

    Attributes:
        asset_id:  i — the monitored asset identifier
        timestamp: t — discrete time step (seconds since epoch typical)
        features:  d_{i,t} — vector in R^F (sensor readings, in any units)
        feature_names: optional names for the F dimensions, in order
    """
    asset_id: str
    timestamp: int
    features: tuple[float, ...]
    feature_names: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.feature_names and len(self.feature_names) != len(self.features):
            raise ValueError(
                f"feature_names length {len(self.feature_names)} != "
                f"features length {len(self.features)}"
            )
        if self.timestamp < 0:
            raise ValueError(f"timestamp must be >= 0, got {self.timestamp}")

    def get(self, name: str) -> float:
        if not self.feature_names:
            raise KeyError("feature_names not provided; use .features tuple instead")
        idx = self.feature_names.index(name)
        return self.features[idx]


@dataclass
class AssetSpec:
    """Static metadata for an asset i, used by CTS and SCS.

    Attributes:
        asset_id:        i
        downtime_cost:   C^down_i — production-downtime cost per hour
        criticality:     phi(C^down_i) in [0, 1] — normalized severity index
        sector:          industry sector (used to look up SCS weights)
    """
    asset_id: str
    downtime_cost: float = 0.0
    criticality: float = 0.5
    sector: str = "general_manufacturing"

    def __post_init__(self) -> None:
        if not 0.0 <= self.criticality <= 1.0:
            raise ValueError(f"criticality must be in [0,1], got {self.criticality}")
        if self.downtime_cost < 0:
            raise ValueError(f"downtime_cost must be >= 0, got {self.downtime_cost}")

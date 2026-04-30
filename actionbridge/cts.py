"""Cost-to-Serve decomposition (Eq. 5) and Delta-CTS reduction ratio (Eq. 6).

CTS_i = C^maint_i + C^down_i + C^wty_i + C^svc_i + C^inv_i

Each component is reducible by a distinct ActionBridge stage:
- C^maint_i, C^down_i      -- reduced by Phi_int (predictive maintenance)
- C^svc_i,   C^wty_i       -- reduced by Phi_orch (case routing + proactive alerts)
- C^inv_i                  -- reduced by Phi_act (demand-signal propagation to ERP)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostToServe:
    """Per-asset cost-to-serve over a planning horizon T.

    All values are in the same currency unit (e.g., USD over T hours/days).
    """
    asset_id: str
    maintenance: float = 0.0  # C^maint_i — scheduled + reactive maintenance
    downtime: float = 0.0     # C^down_i — production-downtime (lost throughput)
    warranty: float = 0.0     # C^wty_i  — warranty claims
    service: float = 0.0      # C^svc_i  — case handling, dispatch, escalations
    inventory: float = 0.0    # C^inv_i  — excess spares + buffer carry

    def __post_init__(self) -> None:
        for name in ("maintenance", "downtime", "warranty", "service", "inventory"):
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} must be >= 0, got {value}")

    def total(self) -> float:
        """CTS_i — Eq. 5."""
        return (
            self.maintenance
            + self.downtime
            + self.warranty
            + self.service
            + self.inventory
        )


def delta_cts(pre: list[CostToServe], post: list[CostToServe]) -> float:
    """Fleet-level cost-to-serve reduction ratio — Eq. 6.

    Delta-CTS = 1 - sum(CTS^post_i) / sum(CTS^pre_i)

    A positive value means CTS dropped after ActionBridge deployment.
    Returns 0.0 for an empty pre/post fleet.
    """
    if len(pre) != len(post):
        raise ValueError(
            f"pre/post fleet sizes differ: {len(pre)} vs {len(post)}"
        )
    pre_total = sum(c.total() for c in pre)
    post_total = sum(c.total() for c in post)
    if pre_total == 0:
        return 0.0
    return 1.0 - (post_total / pre_total)

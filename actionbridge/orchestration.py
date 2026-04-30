"""Orchestration operator Phi_orch — Algorithm 1 of the paper.

Routes each ranked (d_{i,t}, SCS) signal to one of three action channels:
  - PROACTIVE: open CRM case before failure              (SCS >= theta_pro)
  - REACTIVE:  open CRM case on fault event              (theta_re <= SCS < theta_pro)
  - DEFER:     log for trend analysis, no immediate case (SCS < theta_re)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionChannel(Enum):
    PROACTIVE = "proactive"
    REACTIVE = "reactive"
    DEFER = "defer"


@dataclass(frozen=True)
class Action:
    asset_id: str
    timestamp: int
    scs: float
    channel: ActionChannel


def orchestrate(
    signals: list[tuple[str, int, float]],
    theta_pro: float,
    theta_re: float,
) -> list[Action]:
    """Algorithm 1 — route each signal to an action channel.

    Args:
        signals:   sequence of (asset_id, timestamp, SCS) triples.
        theta_pro: threshold for PROACTIVE routing.
        theta_re:  threshold for REACTIVE routing; must satisfy theta_pro >= theta_re.

    Returns:
        Actions ordered by SCS descending. Each input signal produces exactly
        one Action.
    """
    if theta_pro < theta_re:
        raise ValueError(
            f"theta_pro must be >= theta_re, got "
            f"theta_pro={theta_pro}, theta_re={theta_re}"
        )

    ranked = sorted(signals, key=lambda s: s[2], reverse=True)
    actions: list[Action] = []
    for asset_id, t, score in ranked:
        if score >= theta_pro:
            channel = ActionChannel.PROACTIVE
        elif score >= theta_re:
            channel = ActionChannel.REACTIVE
        else:
            channel = ActionChannel.DEFER
        actions.append(Action(asset_id=asset_id, timestamp=t, scs=score, channel=channel))
    return actions

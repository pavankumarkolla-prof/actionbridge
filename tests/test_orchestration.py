"""Tests for Algorithm 1 — orchestration routing."""

import pytest

from actionbridge.orchestration import orchestrate, ActionChannel


def test_proactive_routing_above_high_threshold():
    actions = orchestrate(
        signals=[("a1", 1, 0.8)],
        theta_pro=0.65, theta_re=0.40,
    )
    assert actions[0].channel == ActionChannel.PROACTIVE


def test_reactive_routing_in_middle_band():
    actions = orchestrate(
        signals=[("a1", 1, 0.50)],
        theta_pro=0.65, theta_re=0.40,
    )
    assert actions[0].channel == ActionChannel.REACTIVE


def test_defer_routing_below_low_threshold():
    actions = orchestrate(
        signals=[("a1", 1, 0.10)],
        theta_pro=0.65, theta_re=0.40,
    )
    assert actions[0].channel == ActionChannel.DEFER


def test_actions_ordered_by_scs_descending():
    actions = orchestrate(
        signals=[("a1", 1, 0.30), ("a2", 1, 0.80), ("a3", 1, 0.50)],
        theta_pro=0.65, theta_re=0.40,
    )
    scores = [a.scs for a in actions]
    assert scores == sorted(scores, reverse=True)


def test_threshold_validation():
    with pytest.raises(ValueError):
        orchestrate(signals=[("a1", 1, 0.5)], theta_pro=0.4, theta_re=0.65)


def test_each_signal_yields_one_action():
    signals = [("a1", 1, 0.7), ("a2", 1, 0.3), ("a3", 1, 0.5)]
    actions = orchestrate(signals, theta_pro=0.65, theta_re=0.40)
    assert len(actions) == 3

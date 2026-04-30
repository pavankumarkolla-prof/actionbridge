"""Tests for Signal Criticality Score (Eq. 7)."""

import math

import pytest

from actionbridge.scs import (
    SCSWeights,
    SECTOR_WEIGHTS,
    psi_exponential_decay,
    scs,
)


def test_weights_must_sum_to_one():
    SCSWeights(alpha=0.3, beta=0.3, gamma=0.4)  # ok
    with pytest.raises(ValueError):
        SCSWeights(alpha=0.5, beta=0.5, gamma=0.5)
    with pytest.raises(ValueError):
        SCSWeights(alpha=-0.1, beta=0.6, gamma=0.5)


def test_psi_decreasing_in_rul():
    short = psi_exponential_decay(10, lam=0.05)
    long = psi_exponential_decay(100, lam=0.05)
    assert short > long


def test_psi_at_zero_is_one():
    assert psi_exponential_decay(0) == 1.0


def test_psi_rejects_negative_inputs():
    with pytest.raises(ValueError):
        psi_exponential_decay(-1)
    with pytest.raises(ValueError):
        psi_exponential_decay(10, lam=0)


def test_scs_in_unit_interval():
    score = scs(p_fail=0.7, downtime_severity=0.5, rul_hours=24)
    assert 0.0 <= score <= 1.0


def test_scs_weighted_combination():
    # Force a known weighting; psi(0) = 1, exp(-0*0.01)=1
    w = SCSWeights(alpha=1.0, beta=0.0, gamma=0.0)
    assert math.isclose(scs(0.7, 0.5, 0, weights=w), 0.7, rel_tol=1e-9)
    w = SCSWeights(alpha=0.0, beta=1.0, gamma=0.0)
    assert math.isclose(scs(0.7, 0.5, 0, weights=w), 0.5, rel_tol=1e-9)
    w = SCSWeights(alpha=0.0, beta=0.0, gamma=1.0)
    assert math.isclose(scs(0.7, 0.5, 0, weights=w), 1.0, rel_tol=1e-9)


def test_scs_rejects_out_of_range_inputs():
    with pytest.raises(ValueError):
        scs(p_fail=1.5, downtime_severity=0.5, rul_hours=10)
    with pytest.raises(ValueError):
        scs(p_fail=0.7, downtime_severity=-0.1, rul_hours=10)


def test_sector_defaults_published():
    """Published sector defaults — ensures we don't silently change them."""
    discrete = SECTOR_WEIGHTS["discrete_manufacturing"]
    process = SECTOR_WEIGHTS["process_manufacturing"]
    hmlv = SECTOR_WEIGHTS["high_mix_low_volume"]
    # Discrete: high alpha (failure-driven)
    assert discrete.alpha > discrete.beta and discrete.alpha > discrete.gamma
    # Process: high beta (downtime-cost-driven)
    assert process.beta > process.alpha and process.beta > process.gamma
    # HMLV: high gamma (RUL-urgency-driven)
    assert hmlv.gamma > hmlv.alpha and hmlv.gamma > hmlv.beta


def test_higher_p_fail_gives_higher_score_in_discrete_sector():
    a = scs(0.20, 0.5, 50, sector="discrete_manufacturing")
    b = scs(0.90, 0.5, 50, sector="discrete_manufacturing")
    assert b > a

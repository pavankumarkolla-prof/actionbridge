"""Tests for cost-to-serve decomposition (Eq. 5) and Delta-CTS (Eq. 6)."""

import pytest

from actionbridge.cts import CostToServe, delta_cts


def test_cts_total_sums_components():
    c = CostToServe(
        asset_id="a1",
        maintenance=100, downtime=200, warranty=50, service=30, inventory=20,
    )
    assert c.total() == 400


def test_cts_rejects_negative_components():
    with pytest.raises(ValueError):
        CostToServe(asset_id="a1", maintenance=-1)


def test_delta_cts_zero_for_no_change():
    pre = [CostToServe(asset_id="a1", downtime=100)]
    post = [CostToServe(asset_id="a1", downtime=100)]
    assert delta_cts(pre, post) == 0.0


def test_delta_cts_positive_for_reduction():
    pre = [CostToServe(asset_id="a1", downtime=200)]
    post = [CostToServe(asset_id="a1", downtime=100)]
    assert delta_cts(pre, post) == 0.5


def test_delta_cts_negative_for_increase():
    pre = [CostToServe(asset_id="a1", downtime=100)]
    post = [CostToServe(asset_id="a1", downtime=150)]
    assert delta_cts(pre, post) == -0.5


def test_delta_cts_rejects_mismatched_fleet_sizes():
    with pytest.raises(ValueError):
        delta_cts([CostToServe(asset_id="a1")], [])


def test_delta_cts_zero_pre_returns_zero():
    pre = [CostToServe(asset_id="a1")]
    post = [CostToServe(asset_id="a1")]
    assert delta_cts(pre, post) == 0.0

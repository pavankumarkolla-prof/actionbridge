"""Tests for the NIST MEP, SEC 10-K, and Census ASM data modules."""

import pytest

from actionbridge.data import nist_mep, sec_10k, asm


# ---------- NIST MEP ----------

def test_mep_published_aggregates_present():
    assert 2024 in nist_mep.PUBLISHED_AGGREGATES
    fy24 = nist_mep.PUBLISHED_AGGREGATES[2024]
    assert fy24.fiscal_year == 2024
    assert fy24.n_clients_served > 0
    assert fy24.cost_savings_usd > 0


def test_mep_per_client_savings_in_realistic_range():
    """MEP per-client cost savings should be in the $40K-$300K range."""
    savings = nist_mep.per_client_savings(2024)
    assert 40_000 <= savings <= 300_000, f"unexpected: {savings}"


def test_mep_latest_returns_most_recent_year():
    latest = nist_mep.latest()
    assert latest.fiscal_year == max(nist_mep.PUBLISHED_AGGREGATES)


def test_mep_unknown_year_raises():
    with pytest.raises(KeyError):
        nist_mep.per_client_savings(1990)


# ---------- SEC 10-K ----------

def test_10k_filings_loaded():
    tickers = {f.ticker for f in sec_10k.PUBLISHED_FILINGS}
    assert {"CAT", "DE", "WHR"}.issubset(tickers)


def test_warranty_intensity_positive():
    cat = sec_10k.by_ticker("CAT")
    intensity = sec_10k.warranty_intensity(cat)
    assert 0.0 < intensity < 0.10  # 0% to 10% of revenue


def test_warranty_intensity_higher_for_heavy_equipment():
    """Heavy equipment manufacturers should report higher warranty intensity
    than white goods, reflecting longer warranty obligations."""
    cat = sec_10k.warranty_intensity(sec_10k.by_ticker("CAT"))
    whr = sec_10k.warranty_intensity(sec_10k.by_ticker("WHR"))
    assert cat > whr


def test_total_non_labor_cts_positive():
    cat = sec_10k.by_ticker("CAT")
    total = sec_10k.total_non_labor_cost_to_serve(cat)
    assert total > 0
    # Sanity: total should be sum of components
    assert total == cat.warranty_reserves_musd + cat.sga_musd + cat.inventory_carrying_musd


def test_unknown_ticker_raises():
    with pytest.raises(KeyError):
        sec_10k.by_ticker("NONEXISTENT")


# ---------- Census ASM ----------

def test_asm_published_sectors_loaded():
    assert "333" in asm.PUBLISHED_SECTORS
    assert "3361" in asm.PUBLISHED_SECTORS


def test_asm_cost_shares_sum_close_to_one():
    """All sector cost shares should sum to <= 1.0 (residual 'other' allowed)."""
    for code, sector in asm.PUBLISHED_SECTORS.items():
        total = (
            sector.share_materials
            + sector.share_labor
            + sector.share_capital
            + sector.share_warranty_service
            + sector.share_inventory_carry
        )
        assert 0.5 <= total <= 1.05, f"{code}: shares sum to {total}"


def test_asm_estimate_cts_components_positive():
    estimate = asm.estimate_cts_components(revenue_musd=1000.0, naics_code="333")
    for key in ("maintenance", "downtime", "warranty", "service", "inventory"):
        assert estimate[key] > 0


def test_asm_estimate_scales_with_revenue():
    a = asm.estimate_cts_components(revenue_musd=100.0, naics_code="333")
    b = asm.estimate_cts_components(revenue_musd=1000.0, naics_code="333")
    assert b["warranty"] == pytest.approx(a["warranty"] * 10)


def test_asm_unknown_naics_raises():
    with pytest.raises(KeyError):
        asm.estimate_cts_components(revenue_musd=100.0, naics_code="9999")

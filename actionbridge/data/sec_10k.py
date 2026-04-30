"""Cost-of-Serve components extracted from public 10-K filings.

U.S. publicly traded manufacturers report their warranty reserves,
restructuring costs, and selling/general/administrative breakdowns
in annual 10-K filings filed with the SEC. These are public domain.

This module bundles a small set of headline figures from recent
filings of three large U.S. manufacturers chosen for sector diversity
(heavy equipment, agricultural equipment, white goods). The figures
are aggregated annual numbers in millions of USD as filed.

ActionBridge's Validation section uses these as real, third-party-
verifiable anchors for the cost-component magnitudes the Cost-to-Serve
decomposition (Eq. 5) operates on. Reviewers can reproduce by pulling
the cited filings from sec.gov/edgar.

Source: https://www.sec.gov/edgar — full-text 10-K filings, FY2023-2024.

Note: numbers are filing-as-reported and approximate when the filing
reports a range; consult the original filing for exact figures and
the latest restatements.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenKExtract:
    """Cost components from one 10-K filing, all values in $M USD."""
    company: str
    ticker: str
    fiscal_year: int
    revenue_musd: float
    cost_of_goods_sold_musd: float
    warranty_reserves_musd: float
    rd_musd: float
    sga_musd: float
    inventory_carrying_musd: float
    cik_filing_url: str  # link to filing index on edgar


PUBLISHED_FILINGS: list[TenKExtract] = [
    # Caterpillar Inc. — heavy-equipment manufacturer
    TenKExtract(
        company="Caterpillar Inc.",
        ticker="CAT",
        fiscal_year=2024,
        revenue_musd=64_809.0,
        cost_of_goods_sold_musd=43_128.0,
        warranty_reserves_musd=1_650.0,
        rd_musd=2_098.0,
        sga_musd=6_423.0,
        inventory_carrying_musd=15_400.0,
        cik_filing_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000018230&type=10-K",
    ),
    # Deere & Company — agricultural and construction equipment
    TenKExtract(
        company="Deere & Company",
        ticker="DE",
        fiscal_year=2024,
        revenue_musd=51_716.0,
        cost_of_goods_sold_musd=37_241.0,
        warranty_reserves_musd=1_080.0,
        rd_musd=2_220.0,
        sga_musd=4_590.0,
        inventory_carrying_musd=8_900.0,
        cik_filing_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000315189&type=10-K",
    ),
    # Whirlpool Corporation — white goods manufacturer
    TenKExtract(
        company="Whirlpool Corporation",
        ticker="WHR",
        fiscal_year=2024,
        revenue_musd=16_605.0,
        cost_of_goods_sold_musd=14_184.0,
        warranty_reserves_musd=290.0,
        rd_musd=580.0,
        sga_musd=1_540.0,
        inventory_carrying_musd=2_180.0,
        cik_filing_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000106640&type=10-K",
    ),
]


def warranty_intensity(extract: TenKExtract) -> float:
    """Warranty reserves as a fraction of revenue.

    A simple intensity ratio used in the Validation section to compare
    sectors: heavy equipment runs ~2.5%, white goods ~1.7%, etc. Falls
    out cleanly from publicly reported figures.
    """
    if extract.revenue_musd <= 0:
        return 0.0
    return extract.warranty_reserves_musd / extract.revenue_musd


def total_non_labor_cost_to_serve(extract: TenKExtract) -> float:
    """Approximate non-labor CTS components from the filing (in $M USD).

    Sums warranty reserves, SG&A, and inventory carry — three of the
    five components in ActionBridge's Cost-to-Serve decomposition (Eq. 5)
    that are observable from public filings. The other two (maintenance,
    downtime) are not reported separately in 10-Ks and require the
    NIST MEP / ASM datasets.
    """
    return (
        extract.warranty_reserves_musd
        + extract.sga_musd
        + extract.inventory_carrying_musd
    )


def by_ticker(ticker: str) -> TenKExtract:
    matches = [f for f in PUBLISHED_FILINGS if f.ticker == ticker]
    if not matches:
        raise KeyError(f"No 10-K extract for ticker {ticker!r}")
    return matches[0]

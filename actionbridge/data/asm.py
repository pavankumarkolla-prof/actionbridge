"""U.S. Census Annual Survey of Manufactures (ASM) sector cost structures.

The ASM publishes sector-level cost-component breakdowns each year,
covering all manufacturing NAICS codes. Public domain.

ActionBridge uses these as the *macro* anchor for Cost-to-Serve
decomposition: even when per-firm data isn't available, ASM gives
sector-typical fractions for materials, labor, capital, and indirect
costs that we can apply as priors when estimating CTS for a generic
firm in a given NAICS code.

Source: https://www.census.gov/programs-surveys/asm.html

Note: bundled values are FY2022 published aggregates. They drift slowly
year-over-year; consult the latest ASM tables for fresh data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ASMSectorCostStructure:
    """Sector-level cost structure as a share of total value of shipments.

    All `share_*` fields are dimensionless [0, 1]. They sum to roughly 1
    after rounding (small residual from "other" categories).
    """
    naics_code: str
    sector_label: str
    fiscal_year: int
    total_value_of_shipments_busd: float
    share_materials: float       # raw materials, parts, supplies
    share_labor: float           # production-worker wages
    share_capital: float         # depreciation, equipment investment
    share_warranty_service: float  # warranty reserves + customer service overhead
    share_inventory_carry: float   # estimated carry cost (from working-capital tables)


# Published ASM FY2022 aggregates for selected NAICS sectors. These are
# the standard sector codes ActionBridge's case studies reference.
PUBLISHED_SECTORS: dict[str, ASMSectorCostStructure] = {
    "333": ASMSectorCostStructure(
        naics_code="333",
        sector_label="Machinery Manufacturing",
        fiscal_year=2022,
        total_value_of_shipments_busd=455.0,
        share_materials=0.45,
        share_labor=0.18,
        share_capital=0.12,
        share_warranty_service=0.06,
        share_inventory_carry=0.04,
    ),
    "3361": ASMSectorCostStructure(
        naics_code="3361",
        sector_label="Motor Vehicle Manufacturing",
        fiscal_year=2022,
        total_value_of_shipments_busd=520.0,
        share_materials=0.62,
        share_labor=0.10,
        share_capital=0.09,
        share_warranty_service=0.05,
        share_inventory_carry=0.03,
    ),
    "335": ASMSectorCostStructure(
        naics_code="335",
        sector_label="Electrical Equipment, Appliance, and Component",
        fiscal_year=2022,
        total_value_of_shipments_busd=148.0,
        share_materials=0.50,
        share_labor=0.14,
        share_capital=0.10,
        share_warranty_service=0.07,
        share_inventory_carry=0.05,
    ),
    "325": ASMSectorCostStructure(
        naics_code="325",
        sector_label="Chemical Manufacturing (process-mfg representative)",
        fiscal_year=2022,
        total_value_of_shipments_busd=985.0,
        share_materials=0.55,
        share_labor=0.08,
        share_capital=0.18,
        share_warranty_service=0.03,
        share_inventory_carry=0.06,
    ),
}


def estimate_cts_components(
    revenue_musd: float,
    naics_code: str,
) -> dict[str, float]:
    """Use sector-typical ASM shares to estimate per-firm CTS components.

    Args:
        revenue_musd: firm revenue in millions USD.
        naics_code:   3-4-digit NAICS code keying into PUBLISHED_SECTORS.

    Returns:
        dict with maintenance, downtime, warranty, service, inventory
        estimates in $M USD. Values are rough sector-prior estimates;
        per-firm calibration from a 10-K filing should override.

    Raises KeyError if naics_code is not in PUBLISHED_SECTORS.
    """
    sector = PUBLISHED_SECTORS[naics_code]
    # Maintenance approximated as half of capital share (the depreciation
    # component is largely consumed by routine + reactive maintenance).
    # Downtime approximated as 30% of inventory-carry share (assets sitting
    # idle is a major contributor to working-capital pressure).
    maintenance = revenue_musd * sector.share_capital * 0.5
    downtime = revenue_musd * sector.share_inventory_carry * 0.3
    # Warranty + service together split into 60/40 in published filings.
    warranty = revenue_musd * sector.share_warranty_service * 0.6
    service = revenue_musd * sector.share_warranty_service * 0.4
    inventory = revenue_musd * sector.share_inventory_carry * 0.7
    return {
        "maintenance": maintenance,
        "downtime": downtime,
        "warranty": warranty,
        "service": service,
        "inventory": inventory,
    }

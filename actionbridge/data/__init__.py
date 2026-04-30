"""Public-dataset loaders for ActionBridge validation.

Each module here provides a thin loader for a public manufacturing /
predictive-maintenance / cost-of-serve dataset, returning ActionBridge's
canonical types (Telemetry, AssetSpec, CostToServe). This is the empirical
substrate for the paper's Validation section: instead of synthetic
scenario analysis, every figure can be reproduced against a public
dataset reviewers can independently verify.

Datasets currently wired in:

  scania       SCANIA Component X (real truck operational data, 23 months,
               with failure labels). CC BY 4.0.
               Source: https://researchdata.scania.com / arXiv:2401.15199

  nist_mep     U.S. NIST Manufacturing Extension Partnership (MEP) annual
               client-impact aggregates. Public domain.
               Source: https://www.nist.gov/mep/mep-national-network/
                       impacts-state-and-national-economy

  sec_10k      Cost-component extracts from public 10-K filings of major
               U.S. manufacturers (Caterpillar, Deere, Whirlpool). Public
               domain (SEC EDGAR).
               Source: https://www.sec.gov/edgar

  asm          U.S. Census Annual Survey of Manufactures sector-level cost
               structures. Public domain.
               Source: https://www.census.gov/programs-surveys/asm.html

For each loader, ActionBridge ships a small synthetic-or-anonymised sample
in data/samples/ so the test suite and quick-start demo run without
requiring any download. Real users point loaders at full-sized files
they download themselves.
"""

from actionbridge.data import scania, nist_mep, sec_10k, asm

__all__ = ["scania", "nist_mep", "sec_10k", "asm"]

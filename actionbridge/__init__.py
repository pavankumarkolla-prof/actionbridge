"""ActionBridge — Signal-to-Action reference implementation.

Reference implementation for the paper:
    ActionBridge: A Signal-to-Action Reference Architecture Integrating
    IoT Telemetry, Cloud ML, and CRM for Cost-to-Serve Reduction and
    U.S. Manufacturing Reshoring.

Core components:
    Telemetry         -- discrete-time sensor observation d_{i,t} \\in R^F
    pipeline          -- four-stage transformation Phi_act . Phi_orch . Phi_int . Phi_ing
    cts               -- cost-to-serve decomposition (Eq. 5) + Delta-CTS (Eq. 6)
    scs               -- Signal Criticality Score (Eq. 7)
    orchestration     -- routing algorithm (Algorithm 1)
"""

from actionbridge.telemetry import Telemetry, AssetSpec
from actionbridge.cts import CostToServe, delta_cts
from actionbridge.scs import scs, SCSWeights
from actionbridge.orchestration import orchestrate, Action, ActionChannel
from actionbridge.pipeline import Pipeline, ingest, intelligence

__version__ = "0.1.0"
__author__ = "Pavan Kumar Kolla"

__all__ = [
    "Telemetry",
    "AssetSpec",
    "CostToServe",
    "delta_cts",
    "scs",
    "SCSWeights",
    "orchestrate",
    "Action",
    "ActionChannel",
    "Pipeline",
    "ingest",
    "intelligence",
]

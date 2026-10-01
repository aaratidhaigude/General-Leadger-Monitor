"""
UC8: Predictive Vendor Health & Insolvency Monitor
===================================================
Calculates Vendor Health Index (VHI) to prevent advance deposit losses to bankrupt suppliers.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class VendorHealthResult:
    vendor_health_index: float # 0-100 (100 = healthy, < 40 = high risk)
    insolvency_risk_level: str  # HIGH | MEDIUM | LOW
    score: float                # 0-100 (higher = higher risk score)
    credit_rating: str
    litigation_count: int
    reason: str
    advance_payment_block: bool

def evaluate_vendor_health(
    vendor: str,
    vendor_code: str,
    amount_inr: float,
    is_advance_requested: bool = False
) -> VendorHealthResult:
    v_lower = vendor.lower()
    
    # Simulate OSINT & Credit API ratings based on vendor profile
    if "wipro" in v_lower or "tata" in v_lower or "infosys" in v_lower or "hcl" in v_lower:
        vhi = 92.0
        risk_level = "LOW"
        score = 5.0
        rating = "AAA"
        litigation = 0
        reason = f"Vendor '{vendor}' has strong financial solvency (VHI: 92/100, Rating: AAA)."
        block_adv = False
    elif "distributor" in v_lower or "logistics" in v_lower or "transport" in v_lower or "enterprises" in v_lower:
        vhi = 62.0
        risk_level = "MEDIUM"
        score = 45.0
        rating = "BBB"
        litigation = 2
        reason = f"Vendor '{vendor}' shows moderate liquidity stretch (VHI: 62/100, Rating: BBB, 2 active litigations)."
        block_adv = False
    elif "shell" in v_lower or "troubled" in v_lower or "failing" in v_lower or "insolvent" in v_lower:
        vhi = 25.0
        risk_level = "HIGH"
        score = 90.0
        rating = "CCC"
        litigation = 7
        reason = f"ALERT: Vendor '{vendor}' shows severe bankruptcy signals (VHI: 25/100, Rating: CCC, 7 legal stays)."
        block_adv = True
    else:
        vhi = 80.0
        risk_level = "LOW"
        score = 15.0
        rating = "A+"
        litigation = 0
        reason = f"Vendor '{vendor}' solvent with stable payment history (VHI: 80/100)."
        block_adv = False

    return VendorHealthResult(
        vendor_health_index=vhi,
        insolvency_risk_level=risk_level,
        score=score,
        credit_rating=rating,
        litigation_count=litigation,
        reason=reason,
        advance_payment_block=block_adv
    )

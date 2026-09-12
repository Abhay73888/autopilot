r"""
backend/app/schemas/billing.py — Subscriptions, Credits, and Ledger Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlanTier(BaseModel):
    id: str
    name: str
    monthlyPriceUsd: float
    annualPriceUsd: float
    monthlyCredits: int
    features: List[str]


class CreditBalanceResponse(BaseModel):
    balance: int
    lifetimePurchased: int
    lifetimeUsed: int
    rawCostUsdMonthToDate: float = 0.0


class UsageLedgerItem(BaseModel):
    id: str
    operationType: str
    provider: str
    unitsConsumed: float
    rawCostUsd: float
    creditsDebited: int
    createdAt: str


class CheckoutRequest(BaseModel):
    planId: str
    interval: str = "month"  # month | year
    successUrl: str
    cancelUrl: str

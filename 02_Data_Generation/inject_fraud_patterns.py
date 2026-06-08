"""Shared helpers for deterministic SAP procurement fraud data generation.

The generator scripts in this phase create synthetic but SAP-like source data for
portfolio analytics. Fraud flags are intentionally included only as ground-truth
validation fields; later SQL and notebook analyses should detect patterns from
transaction attributes, not from these flags.
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "03_Data"

SEED = 20260608
ANALYSIS_YEAR = 2025
SPLIT_PURCHASE_THRESHOLD = 500_000
NEW_VENDOR_REFERENCE_DATE = date(2025, 12, 31)

PAYMENT_TERMS = ("Net30", "Net45", "Net60")
VENDOR_CATEGORIES = ("FOOD", "LINN", "MAIN", "SERV")
MATERIAL_GROUPS = {
    "FOOD": ["FRESH_PRODUCE", "SEAFOOD", "BEVERAGE", "DRY_GOODS"],
    "LINN": ["LINEN", "HOUSEKEEPING", "LAUNDRY"],
    "MAIN": ["HVAC", "ELECTRICAL", "PLUMBING", "KITCHEN_EQP"],
    "SERV": ["SPA_SERVICES", "IT_SUPPORT", "SECURITY", "EVENTS"],
}
DEPARTMENTS = ("Procurement", "Finance", "F&B", "Housekeeping", "Maintenance", "Operations")


def rng(offset: int = 0) -> random.Random:
    """Return a deterministic random generator for a script or operation."""
    return random.Random(SEED + offset)


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    ensure_data_dir()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def iso(value: date | datetime | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()


def random_date(randomizer: random.Random, start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=randomizer.randint(0, days))


def add_business_days(start: date, days: int) -> date:
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def jpy_amount(randomizer: random.Random, minimum: int, maximum: int, step: int = 1_000) -> int:
    raw = randomizer.randint(minimum // step, maximum // step) * step
    return int(raw)


def choose_approver(employees: Sequence[Dict[str, str]], amount: int, randomizer: random.Random) -> Dict[str, str]:
    """Choose an active employee whose approval limit can cover the PO amount."""
    eligible = [
        employee
        for employee in employees
        if employee["is_active"] == "True" and int(employee["approval_limit"]) >= amount
    ]
    if not eligible:
        eligible = [employee for employee in employees if employee["is_active"] == "True"]
    return randomizer.choice(eligible)


def choose_low_limit_approver(employees: Sequence[Dict[str, str]], amount: int, randomizer: random.Random) -> Dict[str, str]:
    """Choose an active employee whose approval limit is below the PO amount."""
    candidates = [
        employee
        for employee in employees
        if employee["is_active"] == "True" and int(employee["approval_limit"]) < amount
    ]
    return randomizer.choice(candidates)


def payment_days_for_terms(payment_terms: str) -> int:
    return {"Net30": 30, "Net45": 45, "Net60": 60}[payment_terms]


def vendor_by_id(vendors: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {vendor["vendor_id"]: vendor for vendor in vendors}

"""Generate SAP-like purchase orders and employee approval master data.

Outputs:
- 03_Data/employees.csv
- 03_Data/purchase_orders.csv

SAP context: purchase order header/item data resembles EKKO/EKPO, while the
employee file represents a simplified approval-authority master used by MM
release strategy and workflow controls.
"""

from __future__ import annotations

from datetime import date, timedelta

from generate_vendors import generate_vendors
from inject_fraud_patterns import (
    ANALYSIS_YEAR,
    DATA_DIR,
    DEPARTMENTS,
    MATERIAL_GROUPS,
    SPLIT_PURCHASE_THRESHOLD,
    add_business_days,
    choose_approver,
    choose_low_limit_approver,
    iso,
    jpy_amount,
    random_date,
    read_csv,
    rng,
    vendor_by_id,
    write_csv,
)

EMPLOYEE_FIELDNAMES = [
    "employee_id",
    "employee_name",
    "department",
    "approval_limit",
    "approval_level",
    "is_active",
]

PO_FIELDNAMES = [
    "po_number",
    "vendor_id",
    "po_date",
    "total_amount",
    "line_item_count",
    "approved_by",
    "approval_date",
    "approval_level",
    "approval_threshold_limit",
    "material_group",
    "plant",
    "is_split_purchase",
    "is_approval_bypass",
]

EMPLOYEE_NAMES = [
    "Aiko Tanaka", "Ren Sato", "Yuna Suzuki", "Kaito Yamamoto", "Mei Watanabe",
    "Sora Ito", "Hana Kobayashi", "Daichi Kato", "Rina Yoshida", "Takumi Yamada",
    "Nana Sasaki", "Haruki Yamaguchi", "Mio Matsumoto", "Ryo Inoue", "Akari Kimura",
    "Yuto Shimizu", "Emi Hayashi", "Hinata Mori", "Naoki Abe", "Kokoro Ikeda",
    "Toma Hashimoto", "Miku Yamashita", "Shun Ishikawa", "Ayaka Nakajima", "Kei Maeda",
    "Noa Fujita", "Itsuki Ogawa", "Sara Goto", "Ryusei Okada", "Yuka Hasegawa",
]

APPROVAL_PROFILE = {
    "L1": 300_000,
    "L2": 800_000,
    "L3": 2_000_000,
}


def generate_employees() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    levels = ["L1"] * 14 + ["L2"] * 10 + ["L3"] * 6
    for index, (name, level) in enumerate(zip(EMPLOYEE_NAMES, levels), start=1):
        rows.append(
            {
                "employee_id": f"EMP{index:03d}",
                "employee_name": name,
                "department": DEPARTMENTS[(index - 1) % len(DEPARTMENTS)],
                "approval_limit": APPROVAL_PROFILE[level],
                "approval_level": level,
                "is_active": "False" if index in {12, 27} else "True",
            }
        )
    return rows


def _load_or_generate_vendors() -> list[dict[str, str]]:
    vendor_path = DATA_DIR / "vendors.csv"
    if vendor_path.exists():
        return read_csv(vendor_path)
    vendors = generate_vendors()
    write_csv(vendor_path, vendors, [
        "vendor_id", "vendor_name", "bank_account_number", "registration_date", "payment_terms",
        "vendor_category", "contact_person", "is_active", "is_ghost_vendor", "similar_to_vendor",
    ])
    return read_csv(vendor_path)


def _po_row(po_number: int, vendor_id: str, po_dt: date, amount: int, employees: list[dict[str, str]], vendors: dict[str, dict[str, str]], randomizer, *, split: bool = False, bypass: bool = False, missing_approval: bool = False) -> dict[str, object]:
    vendor_category = vendors[vendor_id]["vendor_category"]
    material_group = randomizer.choice(MATERIAL_GROUPS[vendor_category])
    if missing_approval:
        approved_by = ""
        approval_level = ""
        threshold = 0
        approval_date = ""
    elif bypass:
        approver = choose_low_limit_approver(employees, amount, randomizer)
        approved_by = approver["employee_id"]
        approval_level = approver["approval_level"]
        threshold = int(approver["approval_limit"])
        approval_date = iso(add_business_days(po_dt, randomizer.randint(0, 3)))
    else:
        approver = choose_approver(employees, amount, randomizer)
        approved_by = approver["employee_id"]
        approval_level = approver["approval_level"]
        threshold = int(approver["approval_limit"])
        approval_date = iso(add_business_days(po_dt, randomizer.randint(0, 3)))

    return {
        "po_number": str(po_number),
        "vendor_id": vendor_id,
        "po_date": iso(po_dt),
        "total_amount": amount,
        "line_item_count": randomizer.randint(1, 8),
        "approved_by": approved_by,
        "approval_date": approval_date,
        "approval_level": approval_level,
        "approval_threshold_limit": threshold,
        "material_group": material_group,
        "plant": "JP01",
        "is_split_purchase": "True" if split else "False",
        "is_approval_bypass": "True" if bypass or missing_approval else "False",
    }


def generate_purchase_orders() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    randomizer = rng(20)
    vendors = _load_or_generate_vendors()
    employees = generate_employees()
    vendor_lookup = vendor_by_id(vendors)
    active_legitimate_vendor_ids = [v["vendor_id"] for v in vendors if v["is_active"] == "True" and v["is_ghost_vendor"] == "False"]
    ghost_vendor_ids = [v["vendor_id"] for v in vendors if v["is_ghost_vendor"] == "True"]

    rows: list[dict[str, object]] = []
    po_number = 4_500_000_001
    start = date(ANALYSIS_YEAR, 1, 1)
    end = date(ANALYSIS_YEAR, 12, 31)

    # 20 split-purchase POs: 10 vendor/day clusters of two POs each.
    for _cluster in range(10):
        vendor_id = randomizer.choice(active_legitimate_vendor_ids)
        po_dt = random_date(randomizer, start, end)
        for _ in range(2):
            amount = jpy_amount(randomizer, 255_000, 495_000)
            rows.append(_po_row(po_number, vendor_id, po_dt, amount, employees, vendor_lookup, randomizer, split=True))
            po_number += 1

    # 15 approval bypasses: 8 missing approval and 7 insufficient approver limit.
    for index in range(15):
        vendor_id = randomizer.choice(active_legitimate_vendor_ids)
        po_dt = random_date(randomizer, start, end)
        amount = jpy_amount(randomizer, 650_000, 1_250_000)
        rows.append(
            _po_row(
                po_number,
                vendor_id,
                po_dt,
                amount,
                employees,
                vendor_lookup,
                randomizer,
                bypass=index >= 8,
                missing_approval=index < 8,
            )
        )
        po_number += 1

    # 10 POs issued to ghost vendors.
    for _ in range(10):
        vendor_id = randomizer.choice(ghost_vendor_ids)
        po_dt = random_date(randomizer, date(ANALYSIS_YEAR, 10, 1), end)
        amount = jpy_amount(randomizer, 180_000, 1_350_000)
        rows.append(_po_row(po_number, vendor_id, po_dt, amount, employees, vendor_lookup, randomizer))
        po_number += 1

    # Normal purchase orders to reach 500 total records.
    while len(rows) < 500:
        vendor_id = randomizer.choice(active_legitimate_vendor_ids)
        po_dt = random_date(randomizer, start, end)
        amount = jpy_amount(randomizer, 35_000, 1_700_000)
        # Avoid accidentally generating same-day split clusters just below threshold.
        if 240_000 <= amount < SPLIT_PURCHASE_THRESHOLD and randomizer.random() < 0.55:
            amount = jpy_amount(randomizer, 55_000, 220_000)
        rows.append(_po_row(po_number, vendor_id, po_dt, amount, employees, vendor_lookup, randomizer))
        po_number += 1

    rows.sort(key=lambda row: (row["po_date"], row["po_number"]))
    return rows, employees


if __name__ == "__main__":
    purchase_orders, employees = generate_purchase_orders()
    write_csv(DATA_DIR / "employees.csv", employees, EMPLOYEE_FIELDNAMES)
    write_csv(DATA_DIR / "purchase_orders.csv", purchase_orders, PO_FIELDNAMES)
    print(f"Generated {len(employees)} employees at {DATA_DIR / 'employees.csv'}")
    print(f"Generated {len(purchase_orders)} purchase orders at {DATA_DIR / 'purchase_orders.csv'}")

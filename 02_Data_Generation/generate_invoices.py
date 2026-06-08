"""Generate SAP-like vendor invoices linked to purchase orders.

Output: 03_Data/invoices.csv
SAP context: invoice header/item data resembles RBKP/RSEG created through MIRO.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from generate_purchase_orders import generate_purchase_orders
from inject_fraud_patterns import (
    DATA_DIR,
    add_business_days,
    iso,
    jpy_amount,
    payment_days_for_terms,
    read_csv,
    rng,
    vendor_by_id,
    write_csv,
)

FIELDNAMES = [
    "invoice_id",
    "po_number",
    "vendor_id",
    "invoice_date",
    "invoice_amount",
    "invoice_number",
    "posting_date",
    "payment_date",
    "payment_status",
    "three_way_match_status",
    "is_duplicate",
    "is_maverick_spend",
]


def _parse(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _load_or_generate_purchase_orders() -> list[dict[str, str]]:
    po_path = DATA_DIR / "purchase_orders.csv"
    employee_path = DATA_DIR / "employees.csv"
    if po_path.exists() and employee_path.exists():
        return read_csv(po_path)
    purchase_orders, employees = generate_purchase_orders()
    write_csv(employee_path, employees, [
        "employee_id", "employee_name", "department", "approval_limit", "approval_level", "is_active",
    ])
    write_csv(po_path, purchase_orders, [
        "po_number", "vendor_id", "po_date", "total_amount", "line_item_count", "approved_by",
        "approval_date", "approval_level", "approval_threshold_limit", "material_group", "plant",
        "is_split_purchase", "is_approval_bypass",
    ])
    return read_csv(po_path)


def _invoice_row(invoice_id: int, po: dict[str, str] | None, vendor_id: str, invoice_dt: date, amount: int, randomizer, vendors: dict[str, dict[str, str]], *, invoice_number: str | None = None, over_po: bool = False, no_po: bool = False, duplicate: bool = False) -> dict[str, object]:
    posting_date = add_business_days(invoice_dt, randomizer.randint(0, 4))
    terms = vendors[vendor_id]["payment_terms"]
    due_date = add_business_days(posting_date, payment_days_for_terms(terms))
    payment_status = randomizer.choices(["Paid", "Open", "Blocked"], weights=[0.78, 0.17, 0.05], k=1)[0]
    payment_date = "" if payment_status in {"Open", "Blocked"} else iso(due_date + timedelta(days=randomizer.randint(-3, 5)))

    if no_po:
        match_status = "No PO"
    elif over_po:
        match_status = "Price Variance"
    else:
        match_status = randomizer.choices(["Matched", "Quantity Variance", "Price Variance"], weights=[0.88, 0.08, 0.04], k=1)[0]

    return {
        "invoice_id": f"INV{invoice_id:06d}",
        "po_number": "" if po is None else po["po_number"],
        "vendor_id": vendor_id,
        "invoice_date": iso(invoice_dt),
        "invoice_amount": amount,
        "invoice_number": invoice_number or f"{vendor_id}-{invoice_dt.strftime('%Y%m')}-{randomizer.randint(1000, 9999)}",
        "posting_date": iso(posting_date),
        "payment_date": payment_date,
        "payment_status": payment_status,
        "three_way_match_status": match_status,
        "is_duplicate": "True" if duplicate else "False",
        "is_maverick_spend": "True" if no_po or over_po else "False",
    }


def generate_invoices() -> list[dict[str, object]]:
    randomizer = rng(30)
    purchase_orders = _load_or_generate_purchase_orders()
    vendors = vendor_by_id(read_csv(DATA_DIR / "vendors.csv"))
    rows: list[dict[str, object]] = []
    invoice_id = 1

    # 500 routine linked invoices: one for each PO.
    for po in purchase_orders:
        po_amount = int(po["total_amount"])
        po_date = _parse(po["po_date"])
        invoice_dt = add_business_days(po_date, randomizer.randint(3, 25))
        amount = max(10_000, int(po_amount * randomizer.uniform(0.82, 1.00) // 1_000 * 1_000))
        rows.append(_invoice_row(invoice_id, po, po["vendor_id"], invoice_dt, amount, randomizer, vendors))
        invoice_id += 1

    # 20 invoices slightly over PO amount to simulate tolerance/three-way match weakness.
    sampled_pos = randomizer.sample(purchase_orders, 20)
    for po in sampled_pos:
        po_amount = int(po["total_amount"])
        po_date = _parse(po["po_date"])
        invoice_dt = add_business_days(po_date, randomizer.randint(8, 35))
        amount = int(po_amount * randomizer.uniform(1.03, 1.12) // 1_000 * 1_000)
        rows.append(_invoice_row(invoice_id, po, po["vendor_id"], invoice_dt, amount, randomizer, vendors, over_po=True))
        invoice_id += 1

    # 15 no-PO invoices, representing maverick spend/non-PO vendor invoices.
    vendor_ids = list(vendors.keys())
    for _ in range(15):
        vendor_id = randomizer.choice(vendor_ids)
        invoice_dt = date(2025, randomizer.randint(1, 12), randomizer.randint(1, 25))
        amount = jpy_amount(randomizer, 75_000, 950_000)
        rows.append(_invoice_row(invoice_id, None, vendor_id, invoice_dt, amount, randomizer, vendors, no_po=True))
        invoice_id += 1

    # 35 additional routine invoices for repeat vendor history and realistic volume.
    for po in randomizer.sample(purchase_orders, 35):
        po_amount = int(po["total_amount"])
        po_date = _parse(po["po_date"])
        invoice_dt = add_business_days(po_date, randomizer.randint(12, 45))
        amount = max(10_000, int(po_amount * randomizer.uniform(0.25, 0.65) // 1_000 * 1_000))
        rows.append(_invoice_row(invoice_id, po, po["vendor_id"], invoice_dt, amount, randomizer, vendors))
        invoice_id += 1

    # 30 duplicate invoices: same vendor and amount posted within 30 days of source.
    duplicate_sources = randomizer.sample([row for row in rows if row["po_number"]], 30)
    for source in duplicate_sources:
        source_date = _parse(str(source["posting_date"]))
        duplicate_dt = source_date + timedelta(days=randomizer.randint(1, 20))
        rows.append(
            _invoice_row(
                invoice_id,
                {"po_number": str(source["po_number"])},
                str(source["vendor_id"]),
                duplicate_dt,
                int(source["invoice_amount"]),
                randomizer,
                vendors,
                invoice_number=f"{source['invoice_number']}-DUP",
                duplicate=True,
            )
        )
        invoice_id += 1

    rows.sort(key=lambda row: (row["posting_date"], row["invoice_id"]))
    return rows


if __name__ == "__main__":
    invoices = generate_invoices()
    write_csv(DATA_DIR / "invoices.csv", invoices, FIELDNAMES)
    print(f"Generated {len(invoices)} invoices at {DATA_DIR / 'invoices.csv'}")

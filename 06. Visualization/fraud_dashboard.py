"""Build a dependency-light SAP procurement fraud dashboard.

The script uses Python's standard library so the visualization phase can run in
restricted environments.  The generated HTML uses Plotly from a CDN for the
browser-side charts, while all fraud calculations are performed locally.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

APPROVAL_THRESHOLD_JPY = 500_000
DUPLICATE_AMOUNT_TOLERANCE = 0.05
DUPLICATE_WINDOW_DAYS = 30
NEW_VENDOR_DAYS = 90
HIGH_PAYMENT_JPY = 1_000_000
Z_SCORE_THRESHOLD = 2.5

FRAUD_COLORS = {
    "Duplicate Invoices": "#dc2626",
    "Split Purchases": "#ea580c",
    "Abnormal Vendors": "#ca8a04",
    "Approval Bypasses": "#2563eb",
}


@dataclass(frozen=True)
class DashboardPaths:
    project_root: Path
    data_dir: Path
    output_dir: Path


def resolve_paths(project_root: Path | None = None) -> DashboardPaths:
    root = Path(project_root or Path.cwd()).resolve()
    if not (root / "03_Data").exists():
        root = root.parent.resolve()
    output_dir = root / "06. Visualization" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return DashboardPaths(root, root / "03_Data", output_dir)


def parse_date(value: str) -> datetime | None:
    return datetime.strptime(value, "%Y-%m-%d") if value else None


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def yen(value: float | int) -> str:
    return f"¥{float(value):,.0f}"


def read_csv(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key, value in list(row.items()):
            if key.endswith("date") and value:
                row[key] = parse_date(value)
            elif key in {"total_amount", "invoice_amount", "approval_limit", "approval_threshold_limit", "line_item_count"} and value:
                row[key] = float(value)
            elif key.startswith("is_"):
                row[key] = parse_bool(value)
    return rows


def load_source_data(paths: DashboardPaths) -> dict[str, list[dict[str, object]]]:
    return {
        "vendors": read_csv(paths.data_dir / "vendors.csv"),
        "employees": read_csv(paths.data_dir / "employees.csv"),
        "purchase_orders": read_csv(paths.data_dir / "purchase_orders.csv"),
        "invoices": read_csv(paths.data_dir / "invoices.csv"),
    }


def detect_duplicate_invoices(data: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    vendors = {row["vendor_id"]: row for row in data["vendors"]}
    invoices = sorted(data["invoices"], key=lambda row: (row["vendor_id"], row["posting_date"], row["invoice_id"]))
    suspects: list[dict[str, object]] = []
    for index, original in enumerate(invoices):
        for suspect in invoices[index + 1 :]:
            if suspect["vendor_id"] != original["vendor_id"]:
                if suspect["vendor_id"] > original["vendor_id"]:
                    break
                continue
            posting_gap = abs((suspect["posting_date"] - original["posting_date"]).days)
            if posting_gap > DUPLICATE_WINDOW_DAYS:
                continue
            max_amount = max(original["invoice_amount"], suspect["invoice_amount"])
            amount_difference_pct = abs(suspect["invoice_amount"] - original["invoice_amount"]) / max_amount
            if amount_difference_pct <= DUPLICATE_AMOUNT_TOLERANCE:
                vendor = vendors.get(original["vendor_id"], {})
                suspects.append(
                    {
                        "fraud_category": "Duplicate Invoices",
                        "risk_level": "High",
                        "vendor_id": original["vendor_id"],
                        "vendor_name": vendor.get("vendor_name", "Unknown vendor"),
                        "invoice_id_original": original["invoice_id"],
                        "invoice_id_suspect": suspect["invoice_id"],
                        "posting_gap_days": posting_gap,
                        "amount_difference_pct": round(amount_difference_pct, 4),
                        "exposure_jpy": min(original["invoice_amount"], suspect["invoice_amount"]),
                        "event_month": suspect["posting_date"].strftime("%Y-%m"),
                    }
                )
    return sorted(suspects, key=lambda row: row["exposure_jpy"], reverse=True)


def detect_split_purchases(data: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    vendors = {row["vendor_id"]: row for row in data["vendors"]}
    clusters: dict[tuple[str, str], list[dict[str, object]]] = {}
    for po in data["purchase_orders"]:
        if po["total_amount"] < APPROVAL_THRESHOLD_JPY:
            clusters.setdefault((po["vendor_id"], po["po_date"].strftime("%Y-%m-%d")), []).append(po)
    suspects = []
    for (vendor_id, po_date), orders in clusters.items():
        exposure = sum(order["total_amount"] for order in orders)
        if len(orders) >= 2 and exposure > APPROVAL_THRESHOLD_JPY:
            suspects.append(
                {
                    "fraud_category": "Split Purchases",
                    "risk_level": "High",
                    "vendor_id": vendor_id,
                    "vendor_name": vendors.get(vendor_id, {}).get("vendor_name", "Unknown vendor"),
                    "po_date": po_date,
                    "suspect_count": len(orders),
                    "po_numbers": ", ".join(str(order["po_number"]) for order in orders),
                    "material_groups": ", ".join(sorted({str(order["material_group"]) for order in orders})),
                    "exposure_jpy": exposure,
                    "event_month": po_date[:7],
                }
            )
    return sorted(suspects, key=lambda row: row["exposure_jpy"], reverse=True)


def detect_abnormal_vendors(data: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    vendors = {row["vendor_id"]: row for row in data["vendors"]}
    invoices_by_vendor: dict[str, list[dict[str, object]]] = {}
    for invoice in data["invoices"]:
        invoices_by_vendor.setdefault(invoice["vendor_id"], []).append(invoice)

    duplicate_bank_accounts = {
        vendor["bank_account_number"]
        for vendor in data["vendors"]
        if sum(1 for item in data["vendors"] if item["bank_account_number"] == vendor["bank_account_number"]) > 1
    }
    averages = [mean(invoice["invoice_amount"] for invoice in invoices) for invoices in invoices_by_vendor.values()]
    average_mean = mean(averages) if averages else 0
    average_std = pstdev(averages) if len(averages) > 1 else 0

    suspects = []
    for vendor_id, invoices in invoices_by_vendor.items():
        vendor = vendors.get(vendor_id, {})
        amounts = [invoice["invoice_amount"] for invoice in invoices]
        first_posting = min(invoice["posting_date"] for invoice in invoices)
        age_days = (first_posting - vendor.get("registration_date", first_posting)).days
        average_invoice = mean(amounts)
        z_score = ((average_invoice - average_mean) / average_std) if average_std else 0
        reasons = []
        if 0 <= age_days <= NEW_VENDOR_DAYS and sum(amounts) >= HIGH_PAYMENT_JPY:
            reasons.append("New vendor with high payment")
        if abs(z_score) >= Z_SCORE_THRESHOLD:
            reasons.append("Abnormally high average invoice")
        if vendor.get("bank_account_number") in duplicate_bank_accounts:
            reasons.append("Duplicate bank account")
        if len(invoices) == 1 and max(amounts) >= HIGH_PAYMENT_JPY:
            reasons.append("Single high-value invoice")
        if reasons:
            suspects.append(
                {
                    "fraud_category": "Abnormal Vendors",
                    "risk_level": "Critical" if "Duplicate bank account" in reasons else "Medium",
                    "vendor_id": vendor_id,
                    "vendor_name": vendor.get("vendor_name", "Unknown vendor"),
                    "bank_account_number": vendor.get("bank_account_number", ""),
                    "invoice_count": len(invoices),
                    "average_invoice_jpy": round(average_invoice, 2),
                    "max_invoice_jpy": max(amounts),
                    "vendor_age_at_first_invoice_days": age_days,
                    "invoice_z_score": round(z_score, 2),
                    "risk_reason": "; ".join(reasons),
                    "exposure_jpy": sum(amounts),
                    "event_month": first_posting.strftime("%Y-%m"),
                }
            )
    return sorted(suspects, key=lambda row: row["exposure_jpy"], reverse=True)


def detect_approval_bypasses(data: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    vendors = {row["vendor_id"]: row for row in data["vendors"]}
    employees = {row["employee_id"]: row for row in data["employees"]}
    suspects = []
    for po in data["purchase_orders"]:
        approver = employees.get(po["approved_by"])
        approval_limit = approver.get("approval_limit", 0) if approver else 0
        missing_approver = approver is None
        inactive_approver = bool(approver) and not parse_bool(approver.get("is_active", True))
        limit_exception = po["total_amount"] > approval_limit
        if missing_approver or inactive_approver or limit_exception:
            reason = "Amount exceeds approver limit"
            if missing_approver:
                reason = "Approver missing from employee master"
            elif inactive_approver:
                reason = "Inactive approver used"
            suspects.append(
                {
                    "fraud_category": "Approval Bypasses",
                    "risk_level": "Medium",
                    "vendor_id": po["vendor_id"],
                    "vendor_name": vendors.get(po["vendor_id"], {}).get("vendor_name", "Unknown vendor"),
                    "po_number": po["po_number"],
                    "po_date": po["po_date"].strftime("%Y-%m-%d"),
                    "approved_by": po["approved_by"],
                    "approver_name": approver.get("employee_name", "Missing approver") if approver else "Missing approver",
                    "total_amount": po["total_amount"],
                    "employee_approval_limit": approval_limit,
                    "risk_reason": reason,
                    "exposure_jpy": max(po["total_amount"] - approval_limit, 0),
                    "event_month": po["po_date"].strftime("%Y-%m"),
                }
            )
    return sorted(suspects, key=lambda row: row["exposure_jpy"], reverse=True)


def build_exception_tables(data: dict[str, list[dict[str, object]]]) -> dict[str, list[dict[str, object]]]:
    return {
        "duplicate_invoices": detect_duplicate_invoices(data),
        "split_purchases": detect_split_purchases(data),
        "abnormal_vendors": detect_abnormal_vendors(data),
        "approval_bypasses": detect_approval_bypasses(data),
    }


def build_summary(exceptions: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    category_map = {
        "Duplicate Invoices": exceptions["duplicate_invoices"],
        "Split Purchases": exceptions["split_purchases"],
        "Abnormal Vendors": exceptions["abnormal_vendors"],
        "Approval Bypasses": exceptions["approval_bypasses"],
    }
    summary = []
    for category, rows in category_map.items():
        exposure = sum(row["exposure_jpy"] for row in rows)
        risk_level = rows[0]["risk_level"] if rows else "Low"
        summary.append(
            {
                "fraud_category": category,
                "suspects_found": len(rows),
                "financial_exposure_jpy": exposure,
                "financial_exposure_formatted": yen(exposure),
                "risk_level": risk_level,
            }
        )
    return summary


def build_control_recommendations(summary: list[dict[str, object]]) -> list[dict[str, object]]:
    recommendations = {
        "Duplicate Invoices": "Activate strict MIRO duplicate checks in OMRDC and monitor same-vendor near-match invoices before payment runs.",
        "Split Purchases": "Add cumulative same-day vendor spend checks to MM release strategy and route threshold-adjacent POs to a second approver.",
        "Abnormal Vendors": "Enforce dual control over vendor master creation, bank account changes, and new-vendor payment review during the first 90 days.",
        "Approval Bypasses": "Configure hard workflow stops when PO value exceeds employee authorization limits and review inactive approver assignments.",
    }
    controls = []
    for row in sorted(summary, key=lambda item: item["financial_exposure_jpy"], reverse=True):
        controls.append(
            {
                "fraud_category": row["fraud_category"],
                "risk_level": row["risk_level"],
                "financial_exposure_jpy": row["financial_exposure_jpy"],
                "recommended_sap_control": recommendations[row["fraud_category"]],
            }
        )
    return controls


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            clean_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    clean_row[key] = value.strftime("%Y-%m-%d")
                elif isinstance(value, float) and value.is_integer():
                    clean_row[key] = int(value)
                else:
                    clean_row[key] = value
            writer.writerow(clean_row)


def build_chart_payload(summary: list[dict[str, object]], exceptions: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    monthly: dict[tuple[str, str], dict[str, object]] = {}
    vendor_exposure: dict[str, float] = {}
    for category_rows in exceptions.values():
        for row in category_rows:
            key = (str(row.get("event_month", "Unknown")), str(row["fraud_category"]))
            monthly.setdefault(key, {"month": key[0], "fraud_category": key[1], "exposure_jpy": 0, "suspects": 0})
            monthly[key]["exposure_jpy"] += row["exposure_jpy"]
            monthly[key]["suspects"] += 1
            vendor_exposure[str(row["vendor_name"])] = vendor_exposure.get(str(row["vendor_name"]), 0) + row["exposure_jpy"]
    top_vendors = [
        {"vendor_name": vendor, "exposure_jpy": exposure}
        for vendor, exposure in sorted(vendor_exposure.items(), key=lambda item: item[1], reverse=True)[:10]
    ]
    return {"summary": summary, "monthly": list(monthly.values()), "top_vendors": top_vendors, "colors": FRAUD_COLORS}


def write_html(path: Path, summary: list[dict[str, object]], exceptions: dict[str, list[dict[str, object]]], controls: list[dict[str, object]]) -> None:
    payload = build_chart_payload(summary, exceptions)
    total_exposure = sum(row["financial_exposure_jpy"] for row in summary)
    total_suspects = sum(row["suspects_found"] for row in summary)
    summary_rows = "".join(
        f"<tr><td>{row['fraud_category']}</td><td>{row['suspects_found']}</td><td>{row['financial_exposure_formatted']}</td><td>{row['risk_level']}</td></tr>"
        for row in summary
    )
    control_rows = "".join(
        f"<tr><td>{row['fraud_category']}</td><td>{row['risk_level']}</td><td>{yen(row['financial_exposure_jpy'])}</td><td>{row['recommended_sap_control']}</td></tr>"
        for row in controls
    )
    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>SAP Procurement Fraud Detection Dashboard</title>
  <script src=\"https://cdn.plot.ly/plotly-2.32.0.min.js\"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    header {{ background: #0f172a; color: white; padding: 28px 40px; }}
    main {{ padding: 28px 40px; }}
    .cards {{ display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card, .chart, table {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 1px 2px rgba(15, 23, 42, .08); }}
    .card {{ padding: 20px; }} .metric {{ font-size: 34px; font-weight: 700; margin-top: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 18px; }}
    .chart {{ min-height: 420px; padding: 12px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 22px 0; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: left; vertical-align: top; }}
    th {{ background: #e2e8f0; }}
    @media (max-width: 900px) {{ .grid, .cards {{ grid-template-columns: 1fr; }} main, header {{ padding: 20px; }} }}
  </style>
</head>
<body>
<header>
  <h1>SAP Procurement Fraud Detection Dashboard</h1>
  <p>Executive visualization of duplicate invoice, split purchase, abnormal vendor, and approval bypass risks.</p>
</header>
<main>
  <section class=\"cards\">
    <div class=\"card\"><div>Total suspected exposure</div><div class=\"metric\">{yen(total_exposure)}</div></div>
    <div class=\"card\"><div>Total exceptions</div><div class=\"metric\">{total_suspects:,}</div></div>
  </section>
  <section class=\"grid\">
    <div id=\"exposure\" class=\"chart\"></div>
    <div id=\"mix\" class=\"chart\"></div>
    <div id=\"monthly\" class=\"chart\"></div>
    <div id=\"vendors\" class=\"chart\"></div>
  </section>
  <h2>Executive KPI Summary</h2>
  <table><thead><tr><th>Fraud category</th><th>Suspects found</th><th>Financial exposure</th><th>Risk level</th></tr></thead><tbody>{summary_rows}</tbody></table>
  <h2>SAP Control Recommendations</h2>
  <table><thead><tr><th>Fraud category</th><th>Risk</th><th>Exposure</th><th>Recommended SAP control</th></tr></thead><tbody>{control_rows}</tbody></table>
</main>
<script>
const payload = {json.dumps(payload)};
const categories = payload.summary.map(row => row.fraud_category);
const colors = categories.map(category => payload.colors[category]);
Plotly.newPlot('exposure', [{{type:'bar', x: categories, y: payload.summary.map(row => row.financial_exposure_jpy), marker:{{color: colors}}, text: payload.summary.map(row => row.financial_exposure_formatted), textposition:'auto'}}], {{title:'Exposure by Fraud Category', yaxis:{{title:'JPY'}}}}, {{responsive:true}});
Plotly.newPlot('mix', [{{type:'pie', labels: categories, values: payload.summary.map(row => row.suspects_found), marker:{{colors}}, hole:.45}}], {{title:'Exception Mix'}}, {{responsive:true}});
const traces = categories.map(category => {{
  const rows = payload.monthly.filter(row => row.fraud_category === category).sort((a,b) => a.month.localeCompare(b.month));
  return {{type:'scatter', mode:'lines+markers', name:category, x: rows.map(row => row.month), y: rows.map(row => row.exposure_jpy), line:{{color: payload.colors[category]}}}};
}});
Plotly.newPlot('monthly', traces, {{title:'Monthly Exposure Trend', yaxis:{{title:'JPY'}}}}, {{responsive:true}});
const vendors = [...payload.top_vendors].reverse();
Plotly.newPlot('vendors', [{{type:'bar', orientation:'h', y: vendors.map(row => row.vendor_name), x: vendors.map(row => row.exposure_jpy), marker:{{color:'#475569'}}}}], {{title:'Top 10 Vendors by Exposure', xaxis:{{title:'JPY'}}}}, {{responsive:true}});
</script>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")


def write_dashboard_outputs(paths: DashboardPaths, summary: list[dict[str, object]], exceptions: dict[str, list[dict[str, object]]], controls: list[dict[str, object]]) -> dict[str, Path]:
    outputs = {
        "summary": paths.output_dir / "fraud_dashboard_summary.csv",
        "controls": paths.output_dir / "sap_control_recommendations.csv",
        "html": paths.output_dir / "fraud_dashboard.html",
    }
    write_csv(outputs["summary"], summary)
    write_csv(outputs["controls"], controls)
    for name, rows in exceptions.items():
        outputs[name] = paths.output_dir / f"{name}.csv"
        write_csv(outputs[name], rows)
    write_html(outputs["html"], summary, exceptions, controls)
    return outputs


def build_dashboard(project_root: Path | None = None) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]], dict[str, Path]]:
    paths = resolve_paths(project_root)
    data = load_source_data(paths)
    exceptions = build_exception_tables(data)
    summary = build_summary(exceptions)
    controls = build_control_recommendations(summary)
    outputs = write_dashboard_outputs(paths, summary, exceptions, controls)
    return summary, exceptions, outputs


if __name__ == "__main__":
    dashboard_summary, _, dashboard_outputs = build_dashboard()
    print("SAP procurement fraud dashboard built successfully.")
    for row in dashboard_summary:
        print(
            f"{row['fraud_category']}: {row['suspects_found']} suspects, "
            f"{row['financial_exposure_formatted']} exposure, {row['risk_level']} risk"
        )
    print("\nOutputs:")
    for output_name, output_path in dashboard_outputs.items():
        print(f"- {output_name}: {output_path}")

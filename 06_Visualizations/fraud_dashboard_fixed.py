"""
Converted and fixed version of fraud_dashboard notebook as a Python script.
Fixes applied:
- Removed stray/invalid characters present in the original notebook cell source that caused a syntax error.
- Guarded divisions by zero when computing average values.
- Added safer CSV loading with existence checks and helpful error messages.
- Used .get(...) for potentially-missing dataframe columns so the script fails more gracefully.
- Wrapped heavy sections in `if __name__ == '__main__'` so it can be imported safely.
- Added basic logging/prints to indicate progress and saved outputs to same outputs directory.

Note: This is an executable script alternative to the notebook. If you prefer the notebook updated in-place, I can replace the .ipynb instead.
"""

from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sns.set_theme(style="whitegrid", palette="husl")
pd.options.display.float_format = "{:,.0f}".format
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "03_Data").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "03_Data"
ANALYSIS_DIR = PROJECT_ROOT / "05_Python_Analysis" / "outputs"
OUTPUT_DIR = PROJECT_ROOT / "06_Visualizations" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"✓ Project root: {PROJECT_ROOT}")
print(f"✓ Data directory: {DATA_DIR}")
print(f"✓ Analysis directory: {ANALYSIS_DIR}")
print(f"✓ Output directory: {OUTPUT_DIR}")


def safe_read_csv(path, parse_dates=None):
    if not path.exists():
        print(f"⚠️ File not found: {path} — continuing with empty DataFrame")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except Exception as e:
        print(f"⚠️ Error reading {path}: {e}")
        return pd.DataFrame()


if __name__ == '__main__':
    # Load raw data
    vendors = safe_read_csv(DATA_DIR / "vendors.csv", parse_dates=["registration_date"]) 
    invoices = safe_read_csv(DATA_DIR / "invoices.csv", parse_dates=["invoice_date", "posting_date", "payment_date"]) 
    purchase_orders = safe_read_csv(DATA_DIR / "purchase_orders.csv", parse_dates=["po_date", "approval_date"]) 

    # Load analysis outputs
    duplicate_suspects = safe_read_csv(ANALYSIS_DIR / "duplicate_invoice_suspects.csv")
    duplicate_vendor_summary = safe_read_csv(ANALYSIS_DIR / "duplicate_invoice_vendor_summary.csv")

    split_details = safe_read_csv(ANALYSIS_DIR / "split_purchase_details.csv")
    split_clusters = safe_read_csv(ANALYSIS_DIR / "split_purchase_clusters.csv")
    split_risk_scorecard = safe_read_csv(ANALYSIS_DIR / "split_purchase_risk_scorecard.csv")

    abnormal_vendor_scorecard = safe_read_csv(ANALYSIS_DIR / "abnormal_vendor_risk_scorecard.csv")
    ghost_vendor_candidates = safe_read_csv(ANALYSIS_DIR / "ghost_vendor_candidates.csv")

    approval_violations = safe_read_csv(ANALYSIS_DIR / "approval_bypass_violations.csv")
    approval_department_risk = safe_read_csv(ANALYSIS_DIR / "approval_bypass_department_risk.csv")
    approval_employee_ranking = safe_read_csv(ANALYSIS_DIR / "approval_bypass_employee_ranking.csv")

    print("\n✓ All analysis files attempted to load")
    print(f"  - Duplicate invoice suspects: {len(duplicate_suspects)}")
    print(f"  - Split purchase details: {len(split_details)}")
    print(f"  - Abnormal vendors: {len(abnormal_vendor_scorecard)}")
    print(f"  - Approval violations: {len(approval_violations)}")

    # Calculate aggregate metrics
    total_transactions_analyzed = len(invoices) + len(purchase_orders)

    fraud_suspects_count = (
        len(duplicate_suspects) +
        len(split_details) +
        len(ghost_vendor_candidates) +
        len(approval_violations)
    )

    # Use .get to avoid KeyError if column missing; sum() on empty returns 0
    total_financial_exposure_jpy = (
        duplicate_suspects.get("invoice_amount", pd.Series(dtype=float)).sum() +
        split_details.get("total_amount", pd.Series(dtype=float)).sum() +
        ghost_vendor_candidates.get("total_invoice_value_jpy", pd.Series(dtype=float)).sum() +
        approval_violations.get("total_amount", pd.Series(dtype=float)).sum()
    )

    fraud_rate_pct = (fraud_suspects_count / total_transactions_analyzed) * 100 if total_transactions_analyzed > 0 else 0

    summary_metrics = pd.DataFrame({
        "metric": [
            "Total Transactions Analyzed",
            "Total Fraud Suspects Found",
            "Total Financial Exposure (JPY)",
            "Fraud Rate (%)"
        ],
        "value": [
            f"{total_transactions_analyzed:,}",
            f"{fraud_suspects_count:,}",
            f"¥{total_financial_exposure_jpy:,.0f}",
            f"{fraud_rate_pct:.2f}%"
        ],
        "risk_level": ["Info", "🔴 Critical", "🔴 Critical", "🔴 Critical"]
    })

    print("\n" + "="*80)
    print("EXECUTIVE SUMMARY - FRAUD DETECTION OVERVIEW")
    print("="*80)
    print(summary_metrics.to_string(index=False))
    print("="*80)

    # FRAUD CATEGORY
    fraud_categories = pd.DataFrame({
        "fraud_type": [
            "Duplicate Invoices",
            "Split Purchases",
            "Abnormal Vendors",
            "Approval Bypasses"
        ],
        "count": [
            len(duplicate_suspects),
            len(split_details),
            len(ghost_vendor_candidates),
            len(approval_violations)
        ],
        "total_value_jpy": [
            duplicate_suspects.get("invoice_amount", pd.Series(dtype=float)).sum(),
            split_details.get("total_amount", pd.Series(dtype=float)).sum(),
            ghost_vendor_candidates.get("total_invoice_value_jpy", pd.Series(dtype=float)).sum(),
            approval_violations.get("total_amount", pd.Series(dtype=float)).sum()
        ],
        "risk_color": ["#ff6b6b", "#ff8c42", "#ffd93d", "#6bcf7f"]
    })

    # Avoid division by zero
    fraud_categories["avg_value_jpy"] = np.where(
        fraud_categories["count"] > 0,
        fraud_categories["total_value_jpy"] / fraud_categories["count"],
        0
    )

    print("\nFRAUD CATEGORY BREAKDOWN:")
    print(fraud_categories.to_string(index=False))

    # Small example: save fraud category table as CSV for review
    fraud_categories.to_csv(OUTPUT_DIR / "fraud_category_summary.csv", index=False)
    print("✓ Fraud category summary saved")

    # Vendor risk map preparation (safe access)
    if not abnormal_vendor_scorecard.empty:
        vendor_risk_map = abnormal_vendor_scorecard[[
            col for col in ["vendor_id", "vendor_name", "invoice_count", "total_invoice_value_jpy", "vendor_risk_score", "risk_category"] if col in abnormal_vendor_scorecard.columns
        ]].copy()
    else:
        vendor_risk_map = pd.DataFrame(columns=["vendor_id", "vendor_name", "invoice_count", "total_invoice_value_jpy", "vendor_risk_score", "risk_category"])

    vendor_risk_map["is_ghost_vendor"] = vendor_risk_map["vendor_id"].isin(
        ghost_vendor_candidates.get("vendor_id", pd.Series(dtype=object))
    ) if not vendor_risk_map.empty else pd.Series(dtype=bool)

    print("\nVENDOR RISK SUMMARY:")
    if not vendor_risk_map.empty:
        print(f"High Risk Vendors: {(vendor_risk_map['risk_category'] == 'High').sum()}")
        print(f"Medium Risk Vendors: {(vendor_risk_map['risk_category'] == 'Medium').sum()}")
        print(f"Low Risk Vendors: {(vendor_risk_map['risk_category'] == 'Low').sum()}")
        print(f"Ghost Vendors Identified: {vendor_risk_map['is_ghost_vendor'].sum()}")
    else:
        print("No vendor risk data available")

    # Recommendations (fixed stray characters and kept texts)
    recommendations = {
        "Duplicate Invoice Prevention": {
            "priority": "🔴 CRITICAL",
            "sap_transaction": "OMRDC",
            "action": "Activate duplicate invoice check",
            "details": [
                "Set check scope to Company Code level",
                "Set tolerance to 0% for exact amount match",
                "Set time window to 365 days",
                "Apply to all vendor account groups"
            ],
            "expected_impact": f"Prevent ¥{duplicate_suspects.get('invoice_amount', pd.Series(dtype=float)).sum():,.0f} in exposure",
            "affected_count": len(duplicate_suspects)
        },
        "Split Purchase Prevention": {
            "priority": "🔴 CRITICAL",
            "sap_transaction": "ME21N / Workflow Configuration",
            "action": "Implement cumulative vendor limits",
            "details": [
                "Reduce approval thresholds per PO",
                "Implement cumulative vendor spend limits",
                "Configure cross-PO daily vendor total monitoring",
                "Add exception report for same-day same-vendor POs"
            ],
            "expected_impact": f"Prevent ¥{split_details.get('total_amount', pd.Series(dtype=float)).sum():,.0f} in unauthorized spend",
            "affected_count": len(split_details)
        },
        "Vendor Master Hardening": {
            "priority": "🟠 HIGH",
            "sap_transaction": "XK01 / XK02 / OMSG",
            "action": "Strengthen vendor master governance",
            "details": [
                "Activate vendor master change document logging",
                "Implement dual control for new vendor creation",
                "Set mandatory bank account verification",
                "Auto-block vendors inactive 12+ months",
                "Flag new vendors for 90-day enhanced monitoring"
            ],
            "expected_impact": f"Prevent payments to {len(ghost_vendor_candidates)} identified ghost vendors",
            "affected_count": len(ghost_vendor_candidates)
        },
        "Approval Workflow Hardening": {
            "priority": "🟠 HIGH",
            "sap_transaction": "Workflow Builder / SWDD",
            "action": "Eliminate manual overrides for limit exceptions",
            "details": [
                "Remove manual override capability",
                "Implement hard stops for amounts above limit",
                "Add second approval for limit-adjacent POs",
                "Configure automated alerts for violations",
                "Regular review of employee authorization limits"
            ],
            "expected_impact": f"Prevent ¥{approval_violations.get('total_amount', pd.Series(dtype=float)).sum():,.0f} in unauthorized approvals",
            "affected_count": len(approval_violations)
        }
    }

    print("\n" + "="*100)
    print("SAP CONTROL RECOMMENDATIONS - PRIORITY SUMMARY")
    print("="*100)

    for control, details in recommendations.items():
        print(f"\n{control} {details['priority']}")
        print(f"SAP Transaction: {details['sap_transaction']}")
        print(f"Action: {details['action']}")
        print(f"Affected Records: {details['affected_count']}")
        print(f"Expected Impact: {details['expected_impact']}")

    # Save recommendations summary to file
    rec_summary = [{
        'control': k,
        'priority': v['priority'],
        'sap_transaction': v['sap_transaction'],
        'action': v['action'],
        'affected_count': v['affected_count']
    } for k, v in recommendations.items()]
    pd.DataFrame(rec_summary).to_csv(OUTPUT_DIR / 'recommendations_summary.csv', index=False)
    print('✓ Recommendations summary saved')

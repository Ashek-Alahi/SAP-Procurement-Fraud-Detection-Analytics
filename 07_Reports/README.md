# Phase 7 — Reports and Business Conclusions

This folder converts the dashboard outputs into portfolio-ready reporting for executives, Internal Audit, Procurement, Finance, and SAP control owners.

## Business Objective

Phase 7 answers the final project question: **what should management do with the fraud analytics results?**

The reports translate the exception CSV files from `06. Visualization/outputs/` into:

- Executive-level findings and business impact.
- Prioritized vendor and transaction investigation focus areas.
- SAP S/4HANA control recommendations.
- An audit-style action register that can be assigned to process owners.

## Files

| File | Purpose | Intended audience |
|---|---|---|
| `executive_findings_report.md` | Final narrative report summarizing project scope, key findings, financial exposure, top vendors, and investigation priorities. | Executives, recruiters, SAP consultants, audit managers |
| `sap_control_recommendations.md` | Detailed control remediation plan mapped to SAP process areas, transactions, and practical configuration/process improvements. | SAP functional consultants, process owners, internal controls teams |
| `audit_action_register.csv` | Structured action tracker with owners, priorities, target timing, evidence sources, and success measures. | Internal Audit, Finance, Procurement, SAP control owners |

## Source Evidence

The reports use the current Phase 6 dashboard outputs:

| Source file | Evidence used |
|---|---|
| `06. Visualization/outputs/fraud_dashboard_summary.csv` | Fraud category counts, risk levels, and financial exposure totals |
| `06. Visualization/outputs/duplicate_invoices.csv` | Duplicate invoice exception population and vendor-level investigation focus |
| `06. Visualization/outputs/split_purchases.csv` | Split purchase clusters, same-day vendor spend, and approval threshold circumvention evidence |
| `06. Visualization/outputs/abnormal_vendors.csv` | Vendor master, duplicate bank account, new-vendor, and high-payment risk indicators |
| `06. Visualization/outputs/approval_bypasses.csv` | Approval authority violations, missing approvers, inactive approvers, and value-at-risk |
| `06. Visualization/outputs/sap_control_recommendations.csv` | Dashboard-generated SAP control recommendation summary |

## Headline Results

| Fraud category | Exceptions | Exposure | Report priority |
|---|---:|---:|---|
| Duplicate invoices | 67 | ¥60,706,000 | 1 — highest direct cash leakage risk |
| Abnormal vendors | 10 | ¥52,934,000 | 2 — highest vendor master governance risk |
| Approval bypasses | 15 | ¥10,723,000 | 3 — workflow authorization weakness |
| Split purchases | 10 | ¥7,253,000 | 4 — approval threshold circumvention |
| **Total** | **102** | **¥131,616,000** | — |

## How to Use This Folder in a Portfolio Review

1. Start with `executive_findings_report.md` to understand the business case and management message.
2. Review `sap_control_recommendations.md` to see how the analytics results map to SAP controls.
3. Open `audit_action_register.csv` to show how findings can be operationalized into accountable remediation tasks.
4. Use the Phase 6 dashboard HTML and detailed exception CSVs as supporting evidence.

## Important Interpretation Note

The dataset is synthetic and designed for analytics demonstration. The report language intentionally uses terms such as **suspected exposure**, **exceptions**, and **requires investigation** because analytics identifies risk indicators, not legal proof of fraud. In a real SAP environment, each exception should be validated against invoice images, purchase requisitions, goods receipts, vendor master change logs, approval workflow logs, and payment run evidence before confirming fraud.

# Phase 6 — Visualization Dashboard

This folder converts the SQL and Python fraud-detection work into an executive dashboard suitable for a GitHub portfolio, audit review, or SAP control-improvement discussion.

## Business Objective

The dashboard answers four management questions:

| Management question | Dashboard metric | SAP control relevance |
|---|---|---|
| Which fraud category creates the largest suspected exposure? | Exposure by fraud category | Prioritizes SAP MM/FI control remediation |
| How many exceptions require investigation? | Total exception count and exception mix | Supports audit workpaper scoping |
| Which vendors should be reviewed first? | Top vendors by suspected exposure | Guides vendor master and payment-block review |
| Which SAP controls should be improved? | Control recommendation table | Converts analytics into process action |

## Files

| File | Purpose |
|---|---|
| `fraud_dashboard.py` | Reusable dashboard builder that loads `03_Data`, detects exceptions, creates Plotly visuals, and writes output artifacts. |
| `fraud_dashboard.ipynb` | Notebook version for explaining the business logic and displaying the interactive dashboard. |
| `outputs/fraud_dashboard.html` | Standalone interactive HTML dashboard generated from the current CSV data. |
| `outputs/fraud_dashboard_summary.csv` | Executive KPI table by fraud category. |
| `outputs/sap_control_recommendations.csv` | SAP control recommendations linked to dashboard risks. |
| `outputs/*_csv` | Detailed exception exports for audit follow-up. |

## How to Run

From the repository root:

```bash
pip install -r requirements.txt
python "06. Visualization/fraud_dashboard.py"
```

To run the notebook:

```bash
jupyter nbconvert --to notebook --execute "06. Visualization/fraud_dashboard.ipynb" --output executed_dashboard.ipynb
```

## Dashboard Design Notes

- The visualization intentionally separates **detection logic** (`fraud_dashboard.py`) from **presentation and explanation** (`fraud_dashboard.ipynb`) so the project is easier to maintain.
- Financial exposure is shown in JPY because the simulated SAP procurement data represents a Japanese hospitality company.
- Hidden fraud-label columns in the raw data are not used for the dashboard calculations. The dashboard uses business rules that mirror SAP procurement controls.
- The output CSV files make the dashboard auditable: each KPI can be traced back to detailed vendor, invoice, or PO exceptions.

## Recommended Portfolio Talking Points

1. **Business value:** The dashboard converts raw SAP-style tables into prioritized exceptions that audit, finance, and procurement teams can act on.
2. **SAP relevance:** Each chart links back to a control area: MIRO duplicate invoice checks, MM release strategy, vendor master governance, and workflow authorization limits.
3. **Analytics maturity:** The project progresses from simulated ERP data to SQL, Python detection, and an executive visualization layer.

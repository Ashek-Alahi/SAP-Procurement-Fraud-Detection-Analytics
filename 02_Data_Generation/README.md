# Phase 2 — Data Generation

This folder contains deterministic Python scripts that create the synthetic SAP procurement dataset used by later SQL, Python, visualization, and reporting phases.

## Scripts

| Script | Output | Purpose |
|---|---|---|
| `generate_vendors.py` | `03_Data/vendors.csv` | Creates 50 SAP-like vendor master records, including 5 ghost vendors similar to legitimate suppliers. |
| `generate_purchase_orders.py` | `03_Data/employees.csv`, `03_Data/purchase_orders.csv` | Creates 30 approvers and 500 purchase orders with split purchases, approval bypasses, and ghost-vendor POs. |
| `generate_invoices.py` | `03_Data/invoices.csv` | Creates 600 invoices with duplicate invoices, PO variances, and no-PO invoices. |
| `inject_fraud_patterns.py` | Shared helper module | Centralizes constants, deterministic random seeds, date helpers, CSV helpers, and fraud-injection utilities. |
| `data_dictionary.md` | Documentation | Documents every generated field with SAP-equivalent table/field context. |

## How to Regenerate the Phase 2 Data

Run from the repository root:

```bash
python 02_Data_Generation/generate_vendors.py
python 02_Data_Generation/generate_purchase_orders.py
python 02_Data_Generation/generate_invoices.py
```

The data generation process uses fixed random seeds for reproducibility.

## Generated Record Counts

| Dataset | Expected records |
|---|---:|
| Vendors | 50 |
| Employees | 30 |
| Purchase orders | 500 |
| Invoices | 600 |

## Injected Fraud Patterns

| Fraud pattern | Expected count |
|---|---:|
| Ghost vendors | 5 |
| Split-purchase POs | 20 |
| Approval bypass / missing approval POs | 15 |
| POs issued to ghost vendors | 10 |
| Duplicate invoices | 30 |
| Invoices slightly over PO amount | 20 |
| No-PO invoices | 15 |

Fraud flags are included for validation and should be treated as hidden labels in analysis deliverables.

# Phase 3 / Folder 04 — SQL Fraud Analysis

This folder contains the SQL analytics layer for the SAP Procurement Fraud Detection Analytics portfolio project. The queries are written in SQLite-compatible SQL so they can be run locally after loading the CSV files from `03_Data/` into tables named `vendors`, `employees`, `purchase_orders`, and `invoices`.

## SQL Files

| File | Fraud pattern | SAP context | Primary output |
|---|---|---|---|
| `duplicate_invoices.sql` | Same vendor, amount within 5%, invoices posted within 30 days | Extends MIRO-style duplicate invoice checks over RBKP/RSEG-like data | Suspected duplicate invoice pairs, vendor names, posting gap, and total value at risk |
| `split_purchases.sql` | Multiple same-day POs below ¥500,000 that exceed ¥500,000 in total | Detects SAP MM workflow/release strategy threshold circumvention | Vendors, split dates, PO numbers, individual amounts, combined total, and split counts |
| `abnormal_vendors.sql` | New high-payment vendors, abnormal invoice amount Z-scores, one-invoice high-value vendors, duplicate bank accounts, and inactivity/reactivation | Reviews LFA1/LFB1-like vendor master risks for ghost/shell vendor indicators | Vendor-level risk categories, related master-data details, and exposure roll-ups |
| `approval_bypass.sql` | PO amount exceeds approving employee authority limit, plus missing/inactive approvers | Tests SAP MM release strategy and workflow approval governance | PO number, amount, approver, approval limit, excess amount, and exception summary |

## How to Run in SQLite

```bash
sqlite3 /tmp/sap_procurement.db <<'SQL'
.headers on
.mode csv
.import 03_Data/vendors.csv vendors
.import 03_Data/employees.csv employees
.import 03_Data/purchase_orders.csv purchase_orders
.import 03_Data/invoices.csv invoices
.read 04_SQL_Analysis/duplicate_invoices.sql
.read 04_SQL_Analysis/split_purchases.sql
.read 04_SQL_Analysis/abnormal_vendors.sql
.read 04_SQL_Analysis/approval_bypass.sql
SQL
```

Each SQL file returns a detailed exception listing followed by an executive roll-up query for audit reporting.

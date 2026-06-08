# Phase 2 Data Dictionary — SAP Procurement Fraud Detection Analytics

This dictionary documents the synthetic procurement dataset generated for the Japanese hospitality company scenario. The data is SAP-like and is designed for analytics practice; it is not exported from a live SAP system.

## Dataset Summary

| File | Records | SAP Process Area | Purpose |
|---|---:|---|---|
| `03_Data/vendors.csv` | 50 | Vendor master data | Supplier identity, banking, payment terms, category, and ghost-vendor validation flags |
| `03_Data/employees.csv` | 30 | Workflow / approval authority master | Approver identity, department, level, and approval limit |
| `03_Data/purchase_orders.csv` | 500 | SAP MM purchasing | Purchase orders used to test split purchase, ghost vendor, and approval bypass logic |
| `03_Data/invoices.csv` | 600 | SAP MM invoice verification | Vendor invoices used to test duplicate invoice, PO variance, and no-PO spend logic |

> Fraud flags are included only as hidden validation labels for portfolio testing. Detection queries and notebooks should infer fraud patterns from transactional fields rather than relying on these flags.

---

## `vendors.csv` — Vendor Master Data

SAP context: vendor master records mimic vendor creation/maintenance through XK01/XK02 or Business Partner maintenance in SAP S/4HANA. Core SAP equivalents include LFA1 for general vendor master data, LFB1 for company-code payment data, and LFBK for bank details.

| Field name | Data type | SAP equivalent table.field | Description | Example value |
|---|---|---|---|---|
| `vendor_id` | String | LFA1-LIFNR | Synthetic vendor account number. | `VEND001` |
| `vendor_name` | String | LFA1-NAME1 | Vendor legal or trading name. Ghost vendors intentionally have names similar to legitimate vendors. | `Sakura Seafood Co.` |
| `bank_account_number` | String | LFBK-BANKN | Synthetic bank account identifier used for duplicate bank-account testing. | `JP1001-2007919` |
| `registration_date` | Date | LFA1-ERDAT | Date the vendor master record was created. | `2025-10-22` |
| `payment_terms` | String | LFB1-ZTERM | Payment terms used to estimate payment due dates. | `Net60` |
| `vendor_category` | String | LFA1-KTOKK / custom grouping | Procurement category for spend analysis. Values: `FOOD`, `LINN`, `MAIN`, `SERV`. | `FOOD` |
| `contact_person` | String | LFA1-ANRED / ADRC contact concept | Primary vendor contact for investigation context. | `Hina Nakamura` |
| `is_active` | Boolean string | LFA1-SPERR / LFB1-SPERR | Whether the vendor is active for purchasing/payment in the simulated scenario. | `True` |
| `is_ghost_vendor` | Boolean string | Hidden validation flag | Ground-truth fraud label for ghost vendors; not a standard SAP field. | `False` |
| `similar_to_vendor` | String | Hidden validation/link field | Legitimate vendor that a ghost vendor resembles. Blank for normal vendors. | `VEND001` |

---

## `employees.csv` — Employee Approval Master

SAP context: this file represents a simplified workflow and approval-authority master used to validate SAP MM release strategy behavior. It is conceptually related to release strategy configuration, workflow agent determination, and purchasing authorization governance.

| Field name | Data type | SAP equivalent table.field | Description | Example value |
|---|---|---|---|---|
| `employee_id` | String | USR21-BNAME / HR master reference | Synthetic employee or approver identifier. | `EMP001` |
| `employee_name` | String | ADRP-NAME_TEXT / HR master reference | Employee name used in approval reports. | `Aiko Tanaka` |
| `department` | String | HR org unit / cost center concept | Department responsible for the approver. | `Procurement` |
| `approval_limit` | Integer | Release strategy / workflow limit | Maximum PO amount the employee can approve in JPY. | `300000` |
| `approval_level` | String | Release code / workflow level concept | Approval authority tier. Values: `L1`, `L2`, `L3`. | `L1` |
| `is_active` | Boolean string | User/HR active status concept | Whether the employee is currently active for approval routing. | `True` |

---

## `purchase_orders.csv` — Purchase Order Data

SAP context: purchase orders mimic SAP MM header data from EKKO and selected item-level concepts from EKPO. The plant is fixed as `JP01` to represent the Japanese resort company scenario.

| Field name | Data type | SAP equivalent table.field | Description | Example value |
|---|---|---|---|---|
| `po_number` | String | EKKO-EBELN | Synthetic SAP purchase order number, starting from `4500000001`. | `4500000226` |
| `vendor_id` | String | EKKO-LIFNR | Vendor account number linked to `vendors.csv`. | `VEND019` |
| `po_date` | Date | EKKO-BEDAT | Purchase order document date. | `2025-01-01` |
| `total_amount` | Integer | EKKO-RLWRT / EKPO-NETWR | Total PO value in JPY. | `1314000` |
| `line_item_count` | Integer | EKPO-EBELP count | Number of simulated PO line items. | `8` |
| `approved_by` | String | Workflow agent / release user concept | Employee ID of the approver. Blank values simulate missing approval. | `EMP025` |
| `approval_date` | Date | Workflow approval timestamp concept | Date the PO was approved. Blank values simulate missing approval. | `2025-01-06` |
| `approval_level` | String | Release code / strategy concept | Approval level used on the PO. | `L3` |
| `approval_threshold_limit` | Integer | Workflow/release limit concept | Approval limit associated with the recorded approver. | `2000000` |
| `material_group` | String | EKPO-MATKL | Material or service group used for spend segmentation. | `KITCHEN_EQP` |
| `plant` | String | EKPO-WERKS | Plant or resort operating location. | `JP01` |
| `is_split_purchase` | Boolean string | Hidden validation flag | Ground-truth label for POs injected as split-purchase transactions. | `False` |
| `is_approval_bypass` | Boolean string | Hidden validation flag | Ground-truth label for POs with missing or insufficient approval. | `False` |

---

## `invoices.csv` — Vendor Invoice Data

SAP context: vendor invoices mimic invoice verification data from RBKP and RSEG. The data supports MIRO-style duplicate invoice analytics, three-way match variance review, and non-PO invoice monitoring.

| Field name | Data type | SAP equivalent table.field | Description | Example value |
|---|---|---|---|---|
| `invoice_id` | String | RBKP-BELNR | Synthetic invoice document identifier. | `INV000005` |
| `po_number` | String | RSEG-EBELN | Linked purchase order number. Blank for no-PO invoices. | `4500000029` |
| `vendor_id` | String | RBKP-LIFNR | Vendor account number linked to `vendors.csv`. | `VEND012` |
| `invoice_date` | Date | RBKP-BLDAT | Vendor invoice document date. | `2025-01-08` |
| `invoice_amount` | Integer | RBKP-RMWWR / RSEG-WRBTR | Invoice amount in JPY. | `595000` |
| `invoice_number` | String | RBKP-XBLNR | Vendor's external invoice reference number. | `VEND012-202501-2709` |
| `posting_date` | Date | RBKP-BUDAT | SAP posting date for the invoice. | `2025-01-13` |
| `payment_date` | Date | BSEG-AUGDT / payment clearing concept | Date paid or cleared. Blank if open or blocked. | `2025-03-01` |
| `payment_status` | String | Clearing/payment block concept | Invoice payment state. Values: `Paid`, `Open`, `Blocked`. | `Paid` |
| `three_way_match_status` | String | MIRO tolerance/check result concept | Matching outcome against PO/receipt expectations. | `Matched` |
| `is_duplicate` | Boolean string | Hidden validation flag | Ground-truth label for injected duplicate invoices. | `False` |
| `is_maverick_spend` | Boolean string | Hidden validation flag | Ground-truth label for no-PO invoices or invoices above PO amount. | `False` |

---

## Injected Fraud Pattern Counts

| Pattern | Injected records | Validation fields / detection basis |
|---|---:|---|
| Ghost vendors | 5 vendors | `vendors.is_ghost_vendor=True`; similar names and selected duplicate bank accounts |
| Split purchases | 20 POs | `purchase_orders.is_split_purchase=True`; same vendor/date, each below ¥500,000, combined above ¥500,000 |
| Approval bypass / missing approval | 15 POs | `purchase_orders.is_approval_bypass=True`; blank approvals or approver limit below PO amount |
| Purchase orders to ghost vendors | 10 POs | PO `vendor_id` links to ghost vendors |
| Duplicate invoices | 30 invoices | `invoices.is_duplicate=True`; same vendor and amount within 30 days of source invoice |
| Invoices slightly over PO amount | 20 invoices | `invoices.is_maverick_spend=True`; three-way match status `Price Variance` |
| No-PO invoices | 15 invoices | blank `po_number`; three-way match status `No PO` |

## Reproducibility

Run the scripts from the repository root in this order:

```bash
python 02_Data_Generation/generate_vendors.py
python 02_Data_Generation/generate_purchase_orders.py
python 02_Data_Generation/generate_invoices.py
```

The scripts use a fixed seed so regenerated CSV files are deterministic.

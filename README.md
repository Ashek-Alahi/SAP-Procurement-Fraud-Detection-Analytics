# SAP Procurement Fraud Detection Analytics

## 🔍 Detecting Procurement Fraud in SAP S/4HANA Using Data Analytics

![SAP](https://img.shields.io/badge/SAP-S%2F4HANA-blue) ![Python](https://img.shields.io/badge/Python-3.10%2B-green) ![SQL](https://img.shields.io/badge/SQL-SQLite-orange) ![License](https://img.shields.io/badge/License-MIT-yellow) ![Status](https://img.shields.io/badge/Status-In%20Progress-brightgreen)

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Business Problem](#business-problem)
- [Fraud Patterns Detected](#fraud-patterns-detected)
- [SAP Context](#sap-context)
- [Dataset Description](#dataset-description)
- [Project Structure](#project-structure)
- [Key Findings](#key-findings)
- [SAP Control Recommendations](#sap-control-recommendations)
- [Technologies Used](#technologies-used)
- [How to Run](#how-to-run)
- [Author](#author)

---

## Project Overview

This project analyzes simulated SAP S/4HANA procurement transaction data to detect fraudulent patterns using SQL queries, Python analytics, and statistical methods. The dataset replicates real SAP procurement tables including vendor master data, purchase orders, and vendor invoices for a Japanese hospitality company.

The project bridges three domains — SAP ERP systems, accounting controls, and data analytics — to demonstrate how enterprise transaction data can be used proactively to identify financial fraud before it causes significant business loss.

---

## Business Problem

Procurement fraud is one of the most costly forms of corporate fraud globally. According to the Association of Certified Fraud Examiners (ACFE), organizations lose an estimated 5% of annual revenue to fraud each year, with procurement schemes being among the most common. In SAP environments, procurement fraud typically exploits gaps in system configuration, approval workflow weaknesses, and inadequate monitoring of vendor master data.

Traditional audit approaches review transactions after the fact. This project demonstrates how analytical techniques applied directly to SAP procurement data can detect suspicious patterns in real time — enabling proactive fraud prevention rather than reactive investigation.

**Key questions this project answers:**

```
→ Are any vendors submitting duplicate invoices?
→ Is anyone splitting purchases to bypass approval limits?
→ Are there abnormal or ghost vendors receiving payments?
→ Are approval workflows being bypassed for high-value orders?
```

---

## Fraud Patterns Detected

### 1. 🔴 Duplicate Invoice Detection

**What it is:**
A duplicate invoice occurs when the same vendor submits the same invoice more than once — either intentionally to collect double payment or accidentally due to process failure. In SAP, the duplicate invoice check in transaction MIRO can be misconfigured or bypassed.

**Detection Logic:**
```
Same vendor ID
+ Same or near-identical invoice amount (within 5%)
+ Invoice posted within 30 days of original
= Suspected duplicate
```

**Financial Risk:** Direct double payment to vendor

---

### 2. 🟠 Split Purchase Detection

**What it is:**
Split purchasing occurs when a single large purchase is intentionally broken into multiple smaller transactions to stay below the approval authority threshold. This bypasses the SAP workflow approval controls configured in Materials Management (MM).

**Detection Logic:**
```
Same vendor ID
+ Multiple purchase orders on same day
+ Individual PO amounts below ¥500,000 threshold
+ Combined daily total above ¥500,000
= Suspected split purchase
```

**Financial Risk:** Unauthorized purchases above employee approval limit

---

### 3. 🟡 Abnormal Vendor Detection

**What it is:**
Abnormal vendor patterns indicate potential ghost vendors — fictitious companies created in the SAP vendor master to receive fraudulent payments. Ghost vendors often show unusual registration patterns, abnormally high transaction amounts relative to their history, or bank account details that match other vendors.

**Detection Logic:**
```
Vendor registered less than 90 days with payment above ¥1,000,000
OR vendor with Z-score above 2.5 for invoice amounts
OR vendor with duplicate bank account number
OR vendor inactive 6+ months then suddenly reactivated
= Abnormal vendor — requires investigation
```

**Financial Risk:** Payments to fictitious or unauthorized vendors

---

### 4. 🔵 Approval Bypass Detection

**What it is:**
An approval bypass occurs when a purchase order is approved by an employee whose authorization limit is below the PO value. In SAP, the approval workflow in MM should prevent this, but configuration gaps or manual overrides can allow unauthorized approvals to pass through.

**Detection Logic:**
```
Purchase order amount
> Approving employee authorization limit
= Approval bypass detected
```

**Financial Risk:** Unauthorized commitments exceeding employee authority

---

## SAP Context

This project directly maps each fraud pattern to real SAP S/4HANA tables, transactions, and configuration points — demonstrating both analytical capability and SAP system knowledge.

| Fraud Pattern | SAP Table | SAP Transaction | SAP Control Gap |
|---|---|---|---|
| Duplicate Invoice | RBKP / RSEG | MIRO | Duplicate check not activated in OMRDC |
| Split Purchase | EKKO / EKPO | ME21N | Approval threshold too high in workflow |
| Abnormal Vendor | LFA1 / LFB1 | XK01 / MK01 | Vendor master change monitoring inactive |
| Approval Bypass | EKKO / T024 | ME21N | Workflow tolerance limits misconfigured |

### SAP Data Model Used

```
LFA1 / LFB1     → Vendor Master (General + Company Code)
EKKO / EKPO     → Purchase Order Header + Line Items
RBKP / RSEG     → Invoice Header + Line Items
T024            → Purchasing Groups and Approval Limits
```

---

## Dataset Description

All data in this project is **simulated** and does not contain any real company information. The dataset is generated to realistically replicate SAP S/4HANA procurement transaction patterns for a Japanese hospitality company.

### Dataset Overview

| File | SAP Equivalent | Records | Description |
|---|---|---|---|
| `vendors.csv` | LFA1 / LFB1 | 50 vendors | Vendor master including 5 ghost vendors |
| `purchase_orders.csv` | EKKO / EKPO | 500 POs | POs including split purchases and bypasses |
| `invoices.csv` | RBKP / RSEG | 600 invoices | Invoices including duplicates and mavericks |
| `employees.csv` | HR Master | 30 employees | Approvers with authorization limits |

### Fraud Injection Summary

| Fraud Type | Records Injected | Financial Exposure |
|---|---|---|
| Duplicate Invoices | 30 | To be calculated |
| Split Purchases | 20 | To be calculated |
| Ghost Vendors | 5 | To be calculated |
| Approval Bypasses | 15 | To be calculated |

> Note: Fraud flags are hidden in raw data files. Detection notebooks identify them through analytical methods without using the flag columns directly — simulating real-world detection conditions.

---

## Project Structure

```
📁 SAP-Procurement-Fraud-Detection-Analytics
│
├── 📁 01_Project_Overview
│   ├── README.md
│   └── project_scope.md
│
├── 📁 02_Data_Generation
│   ├── generate_vendors.py
│   ├── generate_purchase_orders.py
│   ├── generate_invoices.py
│   ├── inject_fraud_patterns.py
│   └── data_dictionary.md
│
├── 📁 03_Data
│   ├── vendors.csv
│   ├── purchase_orders.csv
│   ├── invoices.csv
│   └── employees.csv
│
├── 📁 04_SQL_Analysis
│   ├── duplicate_invoices.sql
│   ├── split_purchases.sql
│   ├── abnormal_vendors.sql
│   └── approval_bypass.sql
│
├── 📁 05_Python_Analysis
│   ├── 01_duplicate_invoice_detection.ipynb
│   ├── 02_split_purchase_detection.ipynb
│   ├── 03_abnormal_vendor_detection.ipynb
│   └── 04_approval_bypass_detection.ipynb
│
├── 📁 06. Visualization
│   ├── README.md
│   ├── fraud_dashboard.py
│   ├── fraud_dashboard.ipynb
│   └── outputs/
│       ├── fraud_dashboard.html
│       ├── fraud_dashboard_summary.csv
│       ├── sap_control_recommendations.csv
│       └── detailed exception CSV files
│
├── 📁 07_Reports
│   ├── README.md
│   ├── executive_findings_report.md
│   ├── sap_control_recommendations.md
│   └── audit_action_register.csv
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Key Findings

The Phase 6 dashboard consolidates the four fraud analytics workstreams into an executive view for Finance, Internal Audit, Procurement, and SAP control owners.

### Summary Dashboard

| Fraud Category | Suspects Found | Financial Exposure (JPY) | Risk Level |
|---|---:|---:|---|
| Duplicate Invoices | 67 | ¥60,706,000 | 🔴 High |
| Split Purchases | 10 | ¥7,253,000 | 🟠 High |
| Abnormal Vendors | 10 | ¥52,934,000 | 🟡 Medium |
| Approval Bypasses | 15 | ¥10,723,000 | 🔵 Medium |
| **Total** | **102** | **¥131,616,000** | — |

The interactive HTML dashboard is available at `06. Visualization/outputs/fraud_dashboard.html`, with supporting summary and detailed exception CSV files in `06. Visualization/outputs/`.

The final Phase 7 reporting package is available in `07_Reports/`, including an executive findings report, SAP control remediation plan, and audit action register for remediation tracking.

---

## SAP Control Recommendations

Based on the fraud patterns detected, the following SAP S/4HANA configuration improvements are recommended:

### 1. Duplicate Invoice Prevention

**SAP Transaction:** OMRDC

```
Activate duplicate invoice check:
→ Set check scope to Company Code level
→ Set tolerance to 0% for exact amount match
→ Set time window to 365 days
→ Apply to all vendor account groups
```

---

### 2. Split Purchase Prevention

**SAP Transaction:** Workflow Configuration in MM

```
Reduce approval thresholds:
→ Review and lower per-PO approval limits
→ Implement cumulative vendor spend limits
→ Configure cross-PO daily vendor total monitoring
→ Add exception report for same-day same-vendor POs
```

---

### 3. Vendor Master Controls

**SAP Transaction:** XK01 / OMSG

```
Strengthen vendor master governance:
→ Activate vendor master change document logging
→ Implement dual control for new vendor creation
→ Set mandatory bank account verification process
→ Block vendors inactive for 12+ months automatically
→ Flag new vendors for enhanced monitoring first 90 days
```

---

### 4. Approval Workflow Hardening

**SAP Transaction:** Workflow Builder / SWDD

```
Tighten approval controls:
→ Remove manual override capability for limit exceptions
→ Implement hard stops for amounts above approver limit
→ Add second approval requirement for limit-adjacent POs
→ Configure automated alert for approval violations
→ Regular review of employee authorization limits
```

---

## Technologies Used

| Technology | Purpose | Version |
|---|---|---|
| Python | Data generation and analytics | 3.10+ |
| pandas | Data manipulation and analysis | Latest |
| numpy | Statistical calculations | Latest |
| matplotlib | Static visualizations | Latest |
| seaborn | Statistical visualizations | Latest |
| plotly | Interactive dashboard | Latest |
| SQLite | SQL query analysis | Built-in |
| Jupyter Notebook | Analysis notebooks | Latest |
| GitHub Codespaces | Development environment | — |
| GitHub Copilot / Codex | AI-assisted development | — |

---

## How to Run

### Option 1 — GitHub Codespaces (Recommended)

```
1. Click the green "Code" button on this repository
2. Select "Open with Codespaces"
3. Click "New Codespace"
4. Wait for environment to build
5. Open any notebook in 05_Python_Analysis
6. Run all cells
```

### Option 2 — Local Installation

```bash
# Clone the repository
git clone https://github.com/Ashek-Alahi/SAP-Procurement-Fraud-Detection-Analytics.git

# Navigate to project folder
cd SAP-Procurement-Fraud-Detection-Analytics

# Install required libraries
pip install -r requirements.txt

# Generate simulated data
python 02_Data_Generation/generate_vendors.py
python 02_Data_Generation/generate_purchase_orders.py
python 02_Data_Generation/generate_invoices.py
# Open Jupyter Notebook
jupyter notebook

# Navigate to 05_Python_Analysis and run notebooks in order
```

### Run Order

```
Step 1: Run vendor, purchase-order, and invoice generator scripts in 02_Data_Generation
Step 2: Run SQL queries in 04_SQL_Analysis
Step 3: Run notebooks in 05_Python_Analysis (01 to 04 in order)
Step 4: Run the Phase 6 dashboard script or notebook:
        python "06. Visualization/fraud_dashboard.py"
Step 5: Open 06. Visualization/outputs/fraud_dashboard.html and review the generated CSV exception files
```

---

## Author

**Ashek Alahi**

```
Background:
→ Accountant at Aomori Resort Co., Ltd., Japan
→ MSc in ERP Systems — SAP S/4HANA (KCGI, Kyoto)
→ BBA in Accounting (National University, Bangladesh)
→ SAP Modules: FI · CO · MM · SD

Research Interest:
→ Information Systems
→ Operational Analytics
→ ERP in Hospitality SMEs

Connect:
→ GitHub: github.com/Ashek-Alahi
→ LinkedIn: linkedin.com/in/alahi-ashek
→ Email: ashek.acc@gmail.com
→ Location: Aomori, Japan
```

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgements

This project was built using simulated data inspired by real SAP S/4HANA procurement data structures. All fraud patterns detected are based on common procurement fraud schemes documented in ACFE fraud examination literature and SAP internal control best practices.

---

*SAP Procurement Fraud Detection Analytics — Ashek Alahi — 2026*

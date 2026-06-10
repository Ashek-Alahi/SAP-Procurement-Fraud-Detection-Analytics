# Project Scope: SAP Procurement Fraud Detection Analytics

## 1. Business Problem

Procurement fraud is a high-impact business risk because it can occur inside normal purchasing, invoicing, vendor master, and approval processes. Organizations can lose a meaningful percentage of annual revenue to fraud, and procurement fraud is especially difficult to detect when fraudulent transactions resemble legitimate business activity.

SAP systems generate rich procurement transaction data that can be analyzed to identify fraudulent patterns before they cause significant financial loss. Vendor master records, purchase orders, invoices, approval records, posting dates, payment dates, and employee approval limits can all become audit evidence when analyzed together.

This project demonstrates how SAP procurement data can be used to detect fraud indicators, quantify financial exposure, and recommend SAP control improvements.

## 2. Project Objective

The objective of this project is to build an end-to-end procurement fraud detection analytics solution using simulated SAP-like data for a Japanese hospitality company.

The solution will:

- Generate realistic vendor, purchase order, invoice, and employee approval data.
- Inject known fraud patterns into the dataset for controlled testing.
- Use SQL to identify suspicious transactions and vendors.
- Use Python and Jupyter notebooks for deeper analysis, statistical detection, and visualization.
- Create an executive dashboard summarizing fraud exposure by category.
- Document SAP control recommendations that address the root causes behind each fraud pattern.

## 3. In Scope

This project focuses on the SAP procurement-to-payment process, including:

| Scope Area | Included Activities |
|---|---|
| Vendor master analytics | Vendor creation patterns, ghost vendor indicators, duplicate bank accounts, abnormal payment behavior |
| Purchase order analytics | PO amount analysis, split purchase detection, vendor/date clustering, approval threshold review |
| Invoice analytics | Duplicate invoice detection, invoice-to-PO matching, payment status review, maverick spend indicators |
| Approval analytics | Employee approval limits, approval level matching, missing approvals, over-limit approvals |
| SAP control recommendations | Configuration and process improvements linked to detected fraud patterns |

## 4. Out of Scope

The following items are not included in this portfolio version:

- Connection to a live SAP S/4HANA or ECC system.
- Use of real company, vendor, employee, invoice, bank, or payment data.
- Production deployment of a fraud monitoring tool.
- Legal determination of actual fraud.
- Machine learning model deployment beyond statistical anomaly indicators.
- Full SAP configuration implementation.

All data is simulated for education, portfolio development, and job application evidence.

## 5. Fraud Patterns to Detect

### 5.1 Duplicate Invoices

**Business risk:** A vendor may be paid twice for the same invoice, either because of accidental duplicate submission or intentional fraud.

**Detection logic:**

- Same `vendor_id`.
- Same or very similar `invoice_amount`.
- Invoice posting dates within 30 days.
- Duplicate or similar invoice references when available.

**SAP context:**

- Related SAP process: Logistics Invoice Verification.
- Related SAP transaction: MIRO.
- Related SAP tables: RBKP and RSEG.
- Control weakness: Duplicate invoice check may be inactive, too narrow, or bypassed.
- Control recommendation: Strengthen duplicate invoice validation and configure duplicate invoice checks consistently.

### 5.2 Split Purchases

**Business risk:** A user may divide one large purchase into several smaller purchase orders to avoid higher-level approval.

**Detection logic:**

- Same `vendor_id`.
- Same `po_date`.
- Multiple purchase orders on the same day.
- Each PO is below the ¥500,000 approval threshold.
- Combined same-day value exceeds ¥500,000.

**SAP context:**

- Related SAP process: Materials Management purchasing.
- Related SAP transactions: ME21N, ME22N, ME23N.
- Related SAP tables: EKKO and EKPO.
- Control weakness: Approval workflow evaluates each PO independently but does not monitor cumulative same-day vendor spend.
- Control recommendation: Add cumulative spend monitoring and exception reporting for same-vendor same-day PO clusters.

### 5.3 Abnormal Vendors

**Business risk:** Fraudulent employees may create ghost vendors or shell companies in the vendor master and route payments to those vendors.

**Detection logic:**

- Vendor registered less than 90 days ago with payments above ¥1,000,000.
- Vendor with one invoice but unusually high amount.
- Vendors sharing duplicate or highly similar bank account information.
- Vendors with little or no history followed by sudden large activity.
- Ghost vendors with names similar to legitimate vendors.

**SAP context:**

- Related SAP process: Vendor master governance.
- Related SAP transactions: XK01, XK02, MK01, BP.
- Related SAP tables: LFA1 and LFB1.
- Control weakness: Weak vendor onboarding, missing bank verification, insufficient duplicate vendor screening, or limited change monitoring.
- Control recommendation: Implement dual control for vendor creation, bank account verification, duplicate vendor checks, and periodic vendor master review.

### 5.4 Approval Bypasses

**Business risk:** Purchase orders may be approved by employees whose authorization limits are lower than the PO value.

**Detection logic:**

- Join purchase orders to employee approval master.
- Compare `total_amount` to `approval_limit`.
- Flag POs where the amount exceeds the approving employee's authority.
- Prioritize by excess amount and department.

**SAP context:**

- Related SAP process: Purchase order release strategy and approval workflow.
- Related SAP transactions: ME21N, ME28, workflow approval transactions.
- Related SAP tables/configuration concepts: EKKO, release strategy, workflow roles, approval limits.
- Control weakness: Workflow limits may be misconfigured, manual overrides may be allowed, or employee authorization data may be outdated.
- Control recommendation: Configure hard-stop approval controls, review release strategies, and maintain current approval authority master data.

## 6. Data Scope

The simulated dataset will represent 12 months of procurement activity for a Japanese hospitality or resort company.

| Dataset | Planned Record Count | SAP Equivalent | Key Purpose |
|---|---:|---|---|
| Vendor master | 50 vendors | LFA1 / LFB1 | Vendor identity, bank details, payment terms, category, ghost vendor indicator |
| Purchase orders | 500 POs | EKKO / EKPO | PO amount, vendor, date, approver, approval level, material group, plant |
| Vendor invoices | 600 invoices | RBKP / RSEG | Invoice amount, invoice date, PO matching, posting, payment, duplicate and maverick indicators |
| Employees | Approximately 30 employees | Employee/workflow authorization master | Approval limits, departments, approval levels, active status |

## 7. Fraud Injection Plan

Fraud indicators will be injected into the simulated data so the detection logic can be validated.

| Fraud Type | Planned Injected Pattern | Purpose |
|---|---|---|
| Ghost vendors | 5 vendors similar to legitimate vendors | Test abnormal vendor and master-data control detection |
| Split purchases | 20 split purchase patterns | Test cumulative vendor/day threshold analysis |
| Missing or bypassed approvals | 15 POs with missing or insufficient approvals | Test employee authorization matching |
| POs to ghost vendors | 10 POs to ghost vendors | Test vendor master risk linkage to transaction activity |
| Duplicate invoices | 30 duplicate invoice patterns | Test same-vendor, same-amount, time-window matching |
| Invoices above PO amount | 20 invoices slightly above PO value | Test three-way match and tolerance weakness |
| No-PO invoices | 15 invoices without matching POs | Test maverick spend and invoice control gaps |

## 8. Analytical Approach

The project will use both rule-based analytics and statistical indicators.

### SQL Analysis

SQL will be used to create clear, auditable detection queries:

- Duplicate invoice pair matching.
- Split purchase grouping by vendor and date.
- Abnormal vendor risk categorization.
- Approval bypass detection using joins between POs and employee limits.

### Python Analysis

Python notebooks will support deeper review:

- Descriptive statistics.
- Fuzzy duplicate detection.
- Z-score analysis for invoice amount outliers.
- Vendor risk scoring.
- Timeline and trend analysis.
- Visual ranking of highest-risk vendors, departments, and transaction clusters.

### Visualization

The executive dashboard will summarize:

- Total transactions analyzed.
- Suspected fraud count.
- Total JPY exposure.
- Fraud exposure by category.
- Monthly fraud pattern trends.
- Vendor risk map.
- Prioritized SAP control recommendations.

## 9. Key Deliverables

| Phase | Deliverable | Business Purpose |
|---|---|---|
| Phase 1 | Project overview and scope | Establish business case and SAP control context |
| Phase 2 | Generated SAP-like procurement data | Create realistic test data for analytics |
| Phase 3 | SQL detection queries | Demonstrate auditable fraud detection logic |
| Phase 4 | Python analysis notebooks | Demonstrate analytics, statistics, and visualization capability |
| Phase 5 | Executive fraud dashboard | Communicate risk exposure to management |
| Phase 6 | SAP control recommendations | Connect findings to ERP configuration and process fixes |
| Phase 7 | Final reports and remediation tracker | Create portfolio-ready executive, SAP control, and audit documentation |

## 10. Assumptions

- The company uses SAP procurement processes similar to standard S/4HANA or ECC procure-to-pay workflows.
- All generated data is synthetic and designed for portfolio demonstration.
- Fraud flags in generated data are used for validation only and are not used directly by detection queries or notebooks.
- The approval threshold for split purchase analysis is ¥500,000.
- New vendor risk is assessed using a 90-day registration window.
- Duplicate invoice risk is assessed using a 30-day posting window.
- Financial exposure is reported in Japanese yen.

## 11. Success Criteria

The project is successful if it produces:

1. A realistic simulated SAP procurement dataset.
2. SQL queries that detect all four target fraud patterns.
3. Python notebooks that explain and visualize each detection method.
4. A dashboard that communicates fraud exposure clearly to executives.
5. SAP control recommendations for each detected risk area.
6. Documentation that can be used as evidence in SAP consulting, finance transformation, internal audit, or analytics job applications.

## 12. Business Value

Early fraud detection can save organizations significant losses and strengthen internal controls. This project demonstrates how SAP transaction data can be converted into actionable control intelligence by combining:

- SAP procurement process knowledge.
- Accounting and internal control understanding.
- SQL and Python analytics.
- Executive-level communication.

The final outcome is a portfolio project that shows the ability to think like an ERP consultant: identify business risk, analyze transaction evidence, and recommend practical SAP control improvements.

## 13. Interview Evidence Statement

This project supports the following job interview statement:

> I built a procurement fraud detection analytics system using simulated SAP procurement data. The project identifies duplicate invoices, split purchases, abnormal vendor patterns, and approval bypasses. For each fraud pattern, I documented both the analytical detection method and the SAP control recommendation, showing that I understand the business process, the ERP control weakness, and the data analytics approach.

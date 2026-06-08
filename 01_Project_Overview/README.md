# 01 Project Overview

## Purpose of This Folder

This folder defines the business scope, SAP control context, analytics objectives, and success criteria for the **SAP Procurement Fraud Detection Analytics** portfolio project.

The goal of Phase 1 is to make the project understandable to three audiences:

1. **SAP consulting recruiters** who want to see SAP process and control knowledge.
2. **Internal audit and finance teams** who care about fraud risk, evidence, and control remediation.
3. **Data analytics reviewers** who want to see a clear analytical plan before code is written.

## Project Summary

This project analyzes simulated SAP procurement data for a Japanese hospitality company to detect four high-value fraud patterns:

| Fraud Pattern | Analytics Question | SAP Process Area | Primary Business Risk |
|---|---|---|---|
| Duplicate invoices | Did the same vendor submit the same or near-same invoice more than once? | Logistics Invoice Verification / MIRO | Duplicate payments and cash leakage |
| Split purchases | Were purchases intentionally divided to remain below approval thresholds? | Materials Management purchasing workflow | Unauthorized spend and approval circumvention |
| Abnormal vendors | Do vendor master and payment patterns indicate ghost vendors or shell companies? | Vendor master governance / XK01, BP | Payments to fictitious or unauthorized vendors |
| Approval bypasses | Did an employee approve a PO above their authority limit? | Release strategy / workflow approvals | Weak internal controls and unauthorized commitments |

## Repository Context

The repository is organized as a full end-to-end portfolio project:

```text
SAP-Procurement-Fraud-Detection-Analytics/
├── 01_Project_Overview/      # Scope, objectives, business case, success criteria
├── 02_Data_Generation/       # Python scripts to simulate SAP-like procurement data
├── 03_Data/                  # Generated CSV data files
├── 04_SQL_Analysis/          # SQL fraud detection queries
├── 05_Python_Analysis/       # Jupyter notebooks for deeper analytics
├── 06_Visualizations/        # Executive dashboard and visual summaries
├── 07_Reports/               # Findings, recommendations, and SAP control guidance
└── README.md                 # Main project documentation
```

## Phase 1 Deliverables

| Deliverable | File | Status | Purpose |
|---|---|---:|---|
| Folder overview | `01_Project_Overview/README.md` | Complete | Explains why this phase exists and how it supports the overall project |
| Project scope | `01_Project_Overview/project_scope.md` | Complete | Defines the business problem, fraud patterns, SAP connection, deliverables, assumptions, and success criteria |

## Business Value Statement

Procurement fraud can create direct financial losses, weaken stakeholder trust, and expose gaps in ERP controls. SAP systems generate rich procurement transaction data across vendor master records, purchase orders, invoices, approvals, and payment activity. This project shows how that data can be transformed into practical fraud detection evidence and control recommendations.

The project is intentionally designed to demonstrate more than technical analysis. It connects each analytical detection rule to the SAP configuration or internal control weakness that would allow the fraud pattern to occur.

## SAP Knowledge Demonstrated

This project connects analytics outputs to SAP business processes and tables:

| Project Dataset | SAP Equivalent | Functional Meaning |
|---|---|---|
| `vendors.csv` | LFA1 / LFB1 / Business Partner vendor data | Vendor master records, payment terms, bank details, and vendor categories |
| `purchase_orders.csv` | EKKO / EKPO | Purchase order header and item-level procurement activity |
| `invoices.csv` | RBKP / RSEG | Vendor invoice and invoice line information |
| `employees.csv` | Employee and workflow authorization master | Approver identity, approval level, and approval limit |

## Planned Analysis Flow

```text
1. Define business scope and SAP fraud risk context
2. Generate realistic SAP-like procurement master and transaction data
3. Inject controlled fraud patterns into the simulated dataset
4. Write SQL detection logic for each fraud pattern
5. Build Python notebooks for statistical analysis and visualization
6. Combine findings into an executive dashboard
7. Document SAP control recommendations and business conclusions
```

## Fraud Detection Logic at a Glance

| Detection Area | Core Rule | Expected Evidence |
|---|---|---|
| Duplicate invoices | Same vendor and same amount within 30 days | Suspected duplicate invoice pairs and total value at risk |
| Split purchases | Same vendor, same day, multiple POs below ¥500,000 but combined above ¥500,000 | Circumvented approval threshold and split transaction clusters |
| Abnormal vendors | New vendors, duplicate bank accounts, high single invoice values, sudden payment activity | Vendor risk categories and ghost vendor candidates |
| Approval bypasses | PO amount exceeds approving employee's limit | Excess amount over authorization limit and responsible department |

## Success Criteria

Phase 1 is successful when a reviewer can understand:

- The business problem being solved.
- Why SAP procurement data is appropriate for fraud detection.
- Which fraud patterns will be detected.
- How each fraud pattern maps to SAP transactions, tables, and controls.
- What evidence the project will produce for job applications and interviews.

## How This Supports the Portfolio

A job application reviewer should be able to use this folder as a quick business case before reading code or notebooks. The folder demonstrates that the project is not just a data exercise; it is an ERP consulting-style solution that connects business risk, SAP controls, analytics, and executive communication.

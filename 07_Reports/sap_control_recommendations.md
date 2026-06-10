# SAP Control Recommendations — Procurement Fraud Analytics

## 1. Purpose

This document translates the Phase 6 dashboard findings into practical SAP S/4HANA control improvements. It is written from the perspective of an SAP functional consultant, internal controls analyst, or ERP audit reviewer.

The objective is to reduce future exposure from:

- Duplicate invoices.
- Split purchases.
- Abnormal or ghost vendors.
- Approval bypasses.

## 2. Control Recommendation Summary

| Fraud risk | Exposure | SAP process area | Primary control objective | Recommended priority |
|---|---:|---|---|---|
| Duplicate invoices | ¥60,706,000 | Logistics Invoice Verification / Accounts Payable | Prevent duplicate or near-duplicate vendor invoices before payment. | High |
| Abnormal vendors | ¥52,934,000 | Vendor master governance / Business Partner management | Prevent unauthorized vendors and risky bank account changes. | High |
| Approval bypasses | ¥10,723,000 | Materials Management release strategy / workflow | Prevent approval by missing, inactive, or under-authorized approvers. | Medium |
| Split purchases | ¥7,253,000 | Purchasing workflow and spend monitoring | Detect cumulative vendor spend that bypasses single-PO thresholds. | Medium |

## 3. Duplicate Invoice Controls

### SAP Risk Context

Duplicate invoice risk occurs when the same vendor invoice is posted more than once or when a near-identical invoice bypasses duplicate validation due to inconsistent invoice references, amount differences, or posting date differences.

### SAP Objects and Transactions

| Area | SAP reference |
|---|---|
| Invoice verification | MIRO |
| Duplicate invoice configuration | OMRDC |
| Invoice header and item data | RBKP / RSEG |
| Vendor line item monitoring | FBL1N or supplier line item apps |
| Payment processing | F110 payment run controls |

### Recommended Controls

| Control | Description | Expected benefit |
|---|---|---|
| Activate strict duplicate invoice checks | Configure duplicate checks using vendor, company code, invoice reference, amount, currency, and date fields. | Blocks exact duplicate postings before payment. |
| Normalize invoice reference review | Standardize invoice-number entry rules, including removal of spaces, punctuation, and case differences. | Reduces false negatives caused by inconsistent invoice references. |
| Add near-match exception report | Run a recurring report for same vendor, similar amount, and close posting dates. | Detects duplicates that standard exact-match controls may miss. |
| Payment run exception review | Require AP review of high-value duplicate candidates before F110 payment release. | Prevents cash leakage before bank payment execution. |
| Recovery workflow | Track confirmed duplicate payments to vendor credit memo or recovery status. | Converts detection into measurable financial recovery. |

### Success Metrics

- Duplicate invoice exceptions reviewed before payment.
- Confirmed duplicate payment recovery value.
- Reduction in repeat duplicate exceptions by vendor.
- Percentage of high-risk invoice exceptions resolved within 30 days.

## 4. Vendor Master Controls

### SAP Risk Context

Abnormal vendor risk occurs when vendors are created, modified, or paid without sufficient validation. Duplicate bank accounts, new vendors with high payment activity, and unusual invoice patterns can indicate ghost vendors or unauthorized supplier changes.

### SAP Objects and Transactions

| Area | SAP reference |
|---|---|
| Vendor / Business Partner master | BP, XK01, XK02, MK01, MK02 |
| Vendor master tables | LFA1 / LFB1 / LFBK |
| Vendor account groups and field status | OMSG |
| Change documents | CDHDR / CDPOS |
| Workflow and dual control | SAP Business Workflow / flexible workflow depending on system design |

### Recommended Controls

| Control | Description | Expected benefit |
|---|---|---|
| Dual approval for vendor creation | Require separate requester and approver for new vendor setup. | Reduces ability for one user to create and pay a fake vendor. |
| Bank account duplicate blocking | Identify duplicate bank accounts across active vendors and route exceptions for approval. | Reduces ghost-vendor and related-party payment risk. |
| New-vendor monitoring period | Flag vendors in their first 90 days for enhanced review when cumulative payments exceed threshold. | Detects suspicious early payment activity. |
| Mandatory vendor documentation | Require tax registration, bank confirmation, contract or onboarding evidence, and responsible business owner. | Improves auditability and supplier legitimacy. |
| Vendor master change review | Monitor changes to bank details, payment terms, vendor name, and address. | Detects unauthorized master-data manipulation. |

### Success Metrics

- Percentage of new vendors with complete onboarding evidence.
- Number of duplicate bank account exceptions approved or remediated.
- Vendor master changes reviewed within defined SLA.
- Reduction in high-payment new-vendor exceptions.

## 5. Approval Workflow Controls

### SAP Risk Context

Approval bypass risk occurs when a purchase order is approved by an employee who is missing from the approver master, inactive, or not authorized for the purchase order value.

### SAP Objects and Transactions

| Area | SAP reference |
|---|---|
| Purchase order creation/change | ME21N / ME22N |
| PO approval / release | ME28 or Fiori flexible workflow apps |
| PO tables | EKKO / EKPO |
| Release strategy configuration | SPRO Materials Management purchasing release procedure |
| Workflow monitoring | SWI1 / SWIA / workflow logs |

### Recommended Controls

| Control | Description | Expected benefit |
|---|---|---|
| Hard stop for approval-limit exceptions | Prevent approval when PO value exceeds employee authority. | Eliminates under-authorized approvals. |
| Approver master synchronization | Regularly reconcile SAP approver assignments with active employee records and delegation-of-authority limits. | Prevents missing or inactive approvers from being used. |
| Emergency approval workflow | Route emergency approvals through documented escalation instead of manual bypass. | Maintains business continuity without weakening audit trail. |
| Periodic access and limit review | Review approver limits by department, role, and job level. | Keeps workflow aligned with current authority structure. |
| Exception dashboard | Monitor POs with missing approver, inactive approver, or amount above limit. | Enables continuous control monitoring. |

### Success Metrics

- Zero POs approved by inactive or missing approvers.
- Number of approval-limit exceptions by department.
- Percentage of approver records reconciled monthly.
- Aging of unresolved approval exceptions.

## 6. Split Purchase Controls

### SAP Risk Context

Split purchase risk occurs when a buyer or requestor divides one procurement need into multiple smaller purchase orders to stay below approval thresholds.

### SAP Objects and Transactions

| Area | SAP reference |
|---|---|
| Purchase order processing | ME21N / ME22N |
| Purchase requisition and release | ME51N / ME54N |
| PO data | EKKO / EKPO |
| Purchasing analytics | Fiori procurement analytics or custom CDS reports |
| Workflow threshold configuration | MM release strategy / flexible workflow |

### Recommended Controls

| Control | Description | Expected benefit |
|---|---|---|
| Cumulative vendor spend check | Monitor same vendor, same day, same requester, same plant, or same material group spend above threshold. | Detects threshold circumvention across multiple POs. |
| Pre-approval aggregation rule | Route multiple related POs to higher approval when combined value exceeds limit. | Prevents split transactions before commitment. |
| Buyer/requestor exception review | Identify employees repeatedly involved in split purchase clusters. | Finds training needs or deliberate bypass behavior. |
| Contract and source-of-supply check | Compare split POs against contracts, catalogs, and approved sourcing channels. | Detects maverick spend and purchasing policy violations. |
| Monthly procurement control report | Provide Internal Audit and Procurement with recurring split-purchase exception list. | Converts analytics into continuous monitoring. |

### Success Metrics

- Number of same-day same-vendor split purchase clusters.
- Repeat split-purchase vendors and requestors.
- Value of purchases rerouted to proper approval level.
- Reduction in below-threshold duplicate PO patterns.

## 7. Recommended Implementation Roadmap

| Phase | Timeline | Activities | Main owner |
|---|---|---|---|
| Stabilize | 0–30 days | Review top duplicate invoices, place holds where appropriate, validate duplicate bank accounts, and check missing approvers. | AP, Vendor Master, Internal Audit |
| Configure | 30–60 days | Tighten duplicate checks, update release strategy rules, reconcile approver master data, and define new-vendor monitoring thresholds. | SAP MM/FI, Workflow Owner |
| Automate | 60–90 days | Schedule recurring exception reports and publish dashboard outputs to control owners. | Analytics / Internal Controls |
| Sustain | Ongoing | Track remediation KPIs, false positives, confirmed recoveries, and repeat offenders. | Finance Governance / Procurement Leadership |

## 8. Final Recommendation

The highest-value remediation should begin with duplicate invoices and vendor master governance because these areas represent the largest suspected exposure. Workflow and split-purchase monitoring should follow because they strengthen upstream prevention before invoices reach Accounts Payable.

A mature SAP control environment should combine preventive configuration, detective analytics, clear ownership, and recurring exception review.

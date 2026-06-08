-- SAP Procurement Fraud Detection Analytics
-- Task 3.4 / Folder 04: Approval Bypass Detection
--
-- SAP context:
--   SAP MM release strategy / workflow should route purchase orders to an
--   approver with sufficient authority. This query joins purchase orders to the
--   employee approval-authority master to find approvals that exceed the
--   approver's limit, plus missing/inactive approver exceptions.
--
-- Fraud pattern:
--   PO total amount > approving employee's approval limit.
--
-- Assumptions:
--   * SQLite-compatible SQL.
--   * Blank approved_by values are treated as missing approvals and reported as
--     approval control exceptions.

WITH approval_base AS (
    SELECT
        po.po_number,
        po.vendor_id,
        v.vendor_name,
        po.po_date,
        CAST(po.total_amount AS INTEGER) AS po_amount_jpy,
        po.approved_by AS approver_employee_id,
        e.employee_name AS approver_name,
        e.department AS approver_department,
        e.approval_level AS approver_master_level,
        po.approval_level AS po_recorded_approval_level,
        CAST(e.approval_limit AS INTEGER) AS approver_limit_jpy,
        CAST(po.approval_threshold_limit AS INTEGER) AS po_recorded_threshold_limit_jpy,
        po.approval_date,
        po.material_group,
        e.is_active AS approver_is_active,
        CASE
            WHEN po.approved_by IS NULL OR TRIM(po.approved_by) = '' THEN 'MISSING_APPROVAL'
            WHEN e.employee_id IS NULL THEN 'APPROVER_NOT_FOUND'
            WHEN e.is_active <> 'True' THEN 'INACTIVE_APPROVER'
            WHEN CAST(po.total_amount AS INTEGER) > CAST(e.approval_limit AS INTEGER) THEN 'LIMIT_EXCEEDED'
        END AS exception_category
    FROM purchase_orders AS po
    LEFT JOIN employees AS e
        ON po.approved_by = e.employee_id
    LEFT JOIN vendors AS v
        ON po.vendor_id = v.vendor_id
), approval_exceptions AS (
    SELECT
        *,
        CASE
            WHEN exception_category IN ('MISSING_APPROVAL', 'APPROVER_NOT_FOUND', 'INACTIVE_APPROVER') THEN po_amount_jpy
            WHEN exception_category = 'LIMIT_EXCEEDED' THEN po_amount_jpy - approver_limit_jpy
            ELSE 0
        END AS excess_amount_jpy
    FROM approval_base
    WHERE exception_category IS NOT NULL
)
SELECT
    po_number,
    vendor_id,
    vendor_name,
    po_date,
    po_amount_jpy,
    approver_employee_id,
    approver_name,
    approver_department,
    approver_master_level,
    po_recorded_approval_level,
    approver_limit_jpy,
    po_recorded_threshold_limit_jpy,
    excess_amount_jpy,
    exception_category,
    approval_date,
    material_group,
    approver_is_active
FROM approval_exceptions
ORDER BY excess_amount_jpy DESC, po_amount_jpy DESC, po_date DESC;

-- Executive roll-up: approval bypass exposure by exception category and department.
WITH approval_base AS (
    SELECT
        po.po_number,
        CAST(po.total_amount AS INTEGER) AS po_amount_jpy,
        e.department AS approver_department,
        CAST(e.approval_limit AS INTEGER) AS approver_limit_jpy,
        CASE
            WHEN po.approved_by IS NULL OR TRIM(po.approved_by) = '' THEN 'MISSING_APPROVAL'
            WHEN e.employee_id IS NULL THEN 'APPROVER_NOT_FOUND'
            WHEN e.is_active <> 'True' THEN 'INACTIVE_APPROVER'
            WHEN CAST(po.total_amount AS INTEGER) > CAST(e.approval_limit AS INTEGER) THEN 'LIMIT_EXCEEDED'
        END AS exception_category
    FROM purchase_orders AS po
    LEFT JOIN employees AS e
        ON po.approved_by = e.employee_id
), approval_exceptions AS (
    SELECT
        *,
        CASE
            WHEN exception_category IN ('MISSING_APPROVAL', 'APPROVER_NOT_FOUND', 'INACTIVE_APPROVER') THEN po_amount_jpy
            WHEN exception_category = 'LIMIT_EXCEEDED' THEN po_amount_jpy - approver_limit_jpy
            ELSE 0
        END AS excess_amount_jpy
    FROM approval_base
    WHERE exception_category IS NOT NULL
)
SELECT
    exception_category,
    COALESCE(approver_department, 'Unassigned / Missing Approval') AS approver_department,
    COUNT(*) AS exception_count,
    SUM(po_amount_jpy) AS total_po_value_jpy,
    SUM(excess_amount_jpy) AS total_excess_amount_jpy
FROM approval_exceptions
GROUP BY exception_category, COALESCE(approver_department, 'Unassigned / Missing Approval')
ORDER BY total_excess_amount_jpy DESC, exception_count DESC;

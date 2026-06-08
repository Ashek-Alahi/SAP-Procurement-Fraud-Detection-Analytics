-- SAP Procurement Fraud Detection Analytics
-- Task 3.2 / Folder 04: Split Purchase Detection
--
-- SAP context:
--   Split purchases bypass SAP MM release strategy / workflow approval controls
--   by breaking one business purchase into multiple smaller POs. This query
--   analyzes simplified EKKO/EKPO-style purchase order data.
--
-- Fraud pattern:
--   Same vendor + same PO date + multiple POs + each PO below ¥500,000 approval
--   threshold + combined daily amount above ¥500,000.
--
-- Assumptions:
--   * Approval threshold is fixed at ¥500,000 for this portfolio scenario.
--   * SQLite-compatible SQL.

WITH threshold AS (
    SELECT 500000 AS approval_threshold_jpy
), candidate_pos AS (
    SELECT
        po.po_number,
        po.vendor_id,
        v.vendor_name,
        po.po_date,
        CAST(po.total_amount AS INTEGER) AS total_amount,
        po.material_group,
        po.approved_by,
        po.approval_level
    FROM purchase_orders AS po
    INNER JOIN vendors AS v
        ON po.vendor_id = v.vendor_id
    CROSS JOIN threshold AS t
    WHERE CAST(po.total_amount AS INTEGER) < t.approval_threshold_jpy
), split_groups AS (
    SELECT
        vendor_id,
        vendor_name,
        po_date,
        COUNT(*) AS number_of_splits,
        SUM(total_amount) AS combined_total_jpy,
        GROUP_CONCAT(po_number) AS po_numbers,
        GROUP_CONCAT(total_amount) AS individual_po_amounts_jpy,
        GROUP_CONCAT(material_group) AS material_groups,
        MIN(total_amount) AS smallest_po_jpy,
        MAX(total_amount) AS largest_po_jpy
    FROM candidate_pos
    GROUP BY vendor_id, vendor_name, po_date
    HAVING COUNT(*) > 1
       AND SUM(total_amount) > (SELECT approval_threshold_jpy FROM threshold)
)
SELECT
    vendor_id,
    vendor_name,
    po_date,
    po_numbers,
    individual_po_amounts_jpy,
    combined_total_jpy,
    number_of_splits,
    smallest_po_jpy,
    largest_po_jpy,
    combined_total_jpy - (SELECT approval_threshold_jpy FROM threshold) AS amount_above_threshold_jpy,
    material_groups
FROM split_groups
ORDER BY po_date DESC, combined_total_jpy DESC, vendor_name;

-- Executive roll-up: total split-purchase exposure by vendor.
WITH threshold AS (
    SELECT 500000 AS approval_threshold_jpy
), candidate_pos AS (
    SELECT
        po.po_number,
        po.vendor_id,
        v.vendor_name,
        po.po_date,
        CAST(po.total_amount AS INTEGER) AS total_amount
    FROM purchase_orders AS po
    INNER JOIN vendors AS v
        ON po.vendor_id = v.vendor_id
    CROSS JOIN threshold AS t
    WHERE CAST(po.total_amount AS INTEGER) < t.approval_threshold_jpy
), split_groups AS (
    SELECT
        vendor_id,
        vendor_name,
        po_date,
        COUNT(*) AS number_of_splits,
        SUM(total_amount) AS combined_total_jpy
    FROM candidate_pos
    GROUP BY vendor_id, vendor_name, po_date
    HAVING COUNT(*) > 1
       AND SUM(total_amount) > (SELECT approval_threshold_jpy FROM threshold)
)
SELECT
    vendor_id,
    vendor_name,
    COUNT(*) AS split_activity_dates,
    SUM(number_of_splits) AS split_transactions,
    SUM(combined_total_jpy) AS total_circumvented_amount_jpy,
    SUM(combined_total_jpy - (SELECT approval_threshold_jpy FROM threshold)) AS total_amount_above_threshold_jpy
FROM split_groups
GROUP BY vendor_id, vendor_name
ORDER BY total_circumvented_amount_jpy DESC, split_transactions DESC;

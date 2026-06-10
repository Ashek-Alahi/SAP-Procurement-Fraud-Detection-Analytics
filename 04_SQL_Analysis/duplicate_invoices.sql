-- SAP Procurement Fraud Detection Analytics
-- Task 3.1 / Folder 04: Duplicate Invoice Detection
--
-- SAP context:
--   This query mimics and extends SAP MIRO duplicate invoice checking by
--   comparing vendor invoice postings from the same vendor within a 30-day
--   window. In SAP terms this approximates controls around RBKP-LIFNR,
--   RBKP-RMWWR, RBKP-XBLNR, and RBKP-BUDAT.
--
-- Fraud pattern:
--   Same vendor + invoice amount within 5% + posted within 30 days = likely duplicate.
--
-- Assumptions:
--   * SQLite-compatible SQL using julianday() for date differences.
--   * invoices.posting_date is the SAP posting date used for the duplicate window.
--   * The second/later invoice amount is counted as the value at risk.
--   * Amount tolerance is 5%, matching the project README and Python analysis.

WITH duplicate_parameters AS (
    SELECT 0.05 AS amount_tolerance_pct
), duplicate_pairs AS (
    SELECT
        v.vendor_id,
        v.vendor_name,
        i1.invoice_id AS original_invoice_id,
        i1.invoice_number AS original_invoice_number,
        CAST(i1.invoice_amount AS INTEGER) AS original_amount_jpy,
        i1.posting_date AS original_posting_date,
        i2.invoice_id AS suspected_duplicate_invoice_id,
        i2.invoice_number AS suspected_duplicate_invoice_number,
        CAST(i2.invoice_amount AS INTEGER) AS suspected_duplicate_amount_jpy,
        ROUND(
            ABS(CAST(i1.invoice_amount AS REAL) - CAST(i2.invoice_amount AS REAL))
            / MAX(CAST(i1.invoice_amount AS REAL), CAST(i2.invoice_amount AS REAL)),
            4
        ) AS amount_difference_pct,
        i2.posting_date AS suspected_duplicate_posting_date,
        CAST(julianday(i2.posting_date) - julianday(i1.posting_date) AS INTEGER) AS days_between_postings,
        CAST(i2.invoice_amount AS INTEGER) AS value_at_risk_jpy,
        i2.payment_status AS suspected_duplicate_payment_status,
        i2.three_way_match_status AS suspected_duplicate_match_status
    FROM invoices AS i1
    INNER JOIN invoices AS i2
        ON i1.vendor_id = i2.vendor_id
       AND ABS(CAST(i1.invoice_amount AS REAL) - CAST(i2.invoice_amount AS REAL))
           / MAX(CAST(i1.invoice_amount AS REAL), CAST(i2.invoice_amount AS REAL)) <= (
               SELECT amount_tolerance_pct FROM duplicate_parameters
           )
       AND i1.invoice_id <> i2.invoice_id
       AND julianday(i2.posting_date) >= julianday(i1.posting_date)
       AND (
           i2.posting_date > i1.posting_date
           OR i2.invoice_id > i1.invoice_id
       )
       AND julianday(i2.posting_date) - julianday(i1.posting_date) <= 30
    INNER JOIN vendors AS v
        ON i1.vendor_id = v.vendor_id
)
SELECT
    vendor_id,
    vendor_name,
    original_invoice_id,
    original_invoice_number,
    original_amount_jpy,
    original_posting_date,
    suspected_duplicate_invoice_id,
    suspected_duplicate_invoice_number,
    suspected_duplicate_amount_jpy,
    amount_difference_pct,
    suspected_duplicate_posting_date,
    days_between_postings,
    value_at_risk_jpy,
    suspected_duplicate_payment_status,
    suspected_duplicate_match_status
FROM duplicate_pairs
ORDER BY suspected_duplicate_posting_date DESC, value_at_risk_jpy DESC, vendor_name;

-- Executive roll-up: total duplicate exposure and vendors involved.
WITH duplicate_parameters AS (
    SELECT 0.05 AS amount_tolerance_pct
), duplicate_pairs AS (
    SELECT
        v.vendor_id,
        v.vendor_name,
        i1.invoice_id AS original_invoice_id,
        i2.invoice_id AS suspected_duplicate_invoice_id,
        CAST(i2.invoice_amount AS INTEGER) AS value_at_risk_jpy
    FROM invoices AS i1
    INNER JOIN invoices AS i2
        ON i1.vendor_id = i2.vendor_id
       AND ABS(CAST(i1.invoice_amount AS REAL) - CAST(i2.invoice_amount AS REAL))
           / MAX(CAST(i1.invoice_amount AS REAL), CAST(i2.invoice_amount AS REAL)) <= (
               SELECT amount_tolerance_pct FROM duplicate_parameters
           )
       AND i1.invoice_id <> i2.invoice_id
       AND julianday(i2.posting_date) >= julianday(i1.posting_date)
       AND (
           i2.posting_date > i1.posting_date
           OR i2.invoice_id > i1.invoice_id
       )
       AND julianday(i2.posting_date) - julianday(i1.posting_date) <= 30
    INNER JOIN vendors AS v
        ON i1.vendor_id = v.vendor_id
)
SELECT
    COUNT(*) AS suspected_duplicate_pairs,
    COUNT(DISTINCT vendor_id) AS vendors_involved,
    SUM(value_at_risk_jpy) AS total_value_at_risk_jpy,
    GROUP_CONCAT(DISTINCT vendor_name) AS vendor_names_involved
FROM duplicate_pairs;

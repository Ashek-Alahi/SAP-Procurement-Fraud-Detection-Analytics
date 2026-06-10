-- SAP Procurement Fraud Detection Analytics
-- Task 3.3 / Folder 04: Abnormal Vendor Detection
--
-- SAP context:
--   Ghost vendors and shell companies are commonly hidden in SAP vendor master
--   data (LFA1/LFB1). This query combines vendor master attributes with invoice
--   behavior to identify vendors that require audit follow-up.
--
-- Fraud patterns covered:
--   1. Vendors registered less than 90 days before the analysis date with
--      payments over ¥1,000,000.
--   2. Vendors with abnormal average invoice size versus portfolio (Z-score > 2.5).
--   3. Vendors with only one invoice and a very high invoice amount.
--   4. Vendors sharing duplicate bank accounts.
--   5. Vendors inactive for 6+ months and then suddenly reactivated.
--
-- Assumptions:
--   * SQLite-compatible SQL.
--   * The analysis date is the latest available invoice posting date so the
--     simulated dataset remains reproducible even when run in future calendar
--     years.
--   * A "very high" single invoice is defined as greater than ¥1,000,000.

WITH analysis_parameters AS (
    SELECT
        MAX(posting_date) AS analysis_date,
        90 AS recent_vendor_days,
        1000000 AS high_payment_jpy,
        180 AS inactive_days,
        2.5 AS z_score_threshold
    FROM invoices
), vendor_invoice_metrics AS (
    SELECT
        v.vendor_id,
        v.vendor_name,
        v.bank_account_number,
        v.registration_date,
        v.payment_terms,
        v.vendor_category,
        v.is_active,
        v.is_ghost_vendor,
        v.similar_to_vendor,
        COUNT(i.invoice_id) AS invoice_count,
        COALESCE(SUM(CAST(i.invoice_amount AS INTEGER)), 0) AS total_invoice_amount_jpy,
        COALESCE(MAX(CAST(i.invoice_amount AS INTEGER)), 0) AS largest_invoice_amount_jpy,
        MIN(i.posting_date) AS first_invoice_posting_date,
        MAX(i.posting_date) AS last_invoice_posting_date,
        AVG(CAST(i.invoice_amount AS REAL)) AS average_invoice_amount_jpy
    FROM vendors AS v
    LEFT JOIN invoices AS i
        ON v.vendor_id = i.vendor_id
    GROUP BY
        v.vendor_id,
        v.vendor_name,
        v.bank_account_number,
        v.registration_date,
        v.payment_terms,
        v.vendor_category,
        v.is_active,
        v.is_ghost_vendor,
        v.similar_to_vendor
), portfolio_statistics AS (
    SELECT
        AVG(average_invoice_amount_jpy) AS portfolio_average_invoice_jpy,
        AVG(average_invoice_amount_jpy * average_invoice_amount_jpy)
            - AVG(average_invoice_amount_jpy) * AVG(average_invoice_amount_jpy) AS portfolio_average_invoice_variance
    FROM vendor_invoice_metrics
    WHERE invoice_count > 0
), vendor_z_scores AS (
    SELECT
        m.*,
        CASE
            WHEN ps.portfolio_average_invoice_variance > 0 THEN ROUND(
                (m.average_invoice_amount_jpy - ps.portfolio_average_invoice_jpy)
                / SQRT(ps.portfolio_average_invoice_variance),
                4
            )
            ELSE 0
        END AS avg_invoice_z_score
    FROM vendor_invoice_metrics AS m
    CROSS JOIN portfolio_statistics AS ps
), duplicate_bank_accounts AS (
    SELECT
        bank_account_number,
        COUNT(*) AS vendors_on_bank_account,
        GROUP_CONCAT(vendor_id) AS vendor_ids_on_bank_account,
        GROUP_CONCAT(vendor_name) AS vendor_names_on_bank_account
    FROM vendors
    WHERE bank_account_number IS NOT NULL
      AND TRIM(bank_account_number) <> ''
    GROUP BY bank_account_number
    HAVING COUNT(*) > 1
), invoice_gaps AS (
    SELECT
        vendor_id,
        invoice_id,
        posting_date,
        CAST(invoice_amount AS INTEGER) AS invoice_amount,
        LAG(posting_date) OVER (PARTITION BY vendor_id ORDER BY posting_date, invoice_id) AS previous_posting_date
    FROM invoices
), long_inactivity_events AS (
    SELECT
        vendor_id,
        posting_date AS reactivation_posting_date,
        invoice_amount AS reactivation_invoice_amount_jpy,
        CAST(julianday(posting_date) - julianday(previous_posting_date) AS INTEGER) AS inactive_gap_days,
        ROW_NUMBER() OVER (
            PARTITION BY vendor_id
            ORDER BY
                CAST(julianday(posting_date) - julianday(previous_posting_date) AS INTEGER) DESC,
                posting_date DESC,
                invoice_id DESC
        ) AS inactivity_rank
    FROM invoice_gaps
    WHERE previous_posting_date IS NOT NULL
      AND CAST(julianday(posting_date) - julianday(previous_posting_date) AS INTEGER) >= (SELECT inactive_days FROM analysis_parameters)
), long_inactivity_reactivations AS (
    SELECT
        vendor_id,
        inactive_gap_days AS longest_inactive_gap_days,
        reactivation_posting_date,
        reactivation_invoice_amount_jpy
    FROM long_inactivity_events
    WHERE inactivity_rank = 1
), abnormal_reasons AS (
    SELECT
        m.vendor_id,
        m.vendor_name,
        m.bank_account_number,
        m.registration_date,
        m.payment_terms,
        m.vendor_category,
        m.is_active,
        m.is_ghost_vendor,
        m.similar_to_vendor,
        m.invoice_count,
        m.total_invoice_amount_jpy,
        m.largest_invoice_amount_jpy,
        m.avg_invoice_z_score,
        m.first_invoice_posting_date,
        m.last_invoice_posting_date,
        CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) AS vendor_age_days_at_analysis,
        'NEW_VENDOR_HIGH_PAYMENT' AS risk_category,
        'Vendor registered within 90 days of analysis date and received invoices over ¥1,000,000.' AS risk_description,
        m.total_invoice_amount_jpy AS value_at_risk_jpy,
        NULL AS related_vendor_details
    FROM vendor_z_scores AS m
    CROSS JOIN analysis_parameters AS p
    WHERE CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) BETWEEN 0 AND p.recent_vendor_days
      AND m.total_invoice_amount_jpy > p.high_payment_jpy

    UNION ALL

    SELECT
        m.vendor_id,
        m.vendor_name,
        m.bank_account_number,
        m.registration_date,
        m.payment_terms,
        m.vendor_category,
        m.is_active,
        m.is_ghost_vendor,
        m.similar_to_vendor,
        m.invoice_count,
        m.total_invoice_amount_jpy,
        m.largest_invoice_amount_jpy,
        m.avg_invoice_z_score,
        m.first_invoice_posting_date,
        m.last_invoice_posting_date,
        CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) AS vendor_age_days_at_analysis,
        'ABNORMAL_AVERAGE_INVOICE_AMOUNT' AS risk_category,
        'Vendor average invoice amount has an absolute portfolio Z-score above 2.5.' AS risk_description,
        m.total_invoice_amount_jpy AS value_at_risk_jpy,
        'Average invoice Z-score: ' || m.avg_invoice_z_score AS related_vendor_details
    FROM vendor_z_scores AS m
    CROSS JOIN analysis_parameters AS p
    WHERE ABS(m.avg_invoice_z_score) > p.z_score_threshold

    UNION ALL

    SELECT
        m.vendor_id,
        m.vendor_name,
        m.bank_account_number,
        m.registration_date,
        m.payment_terms,
        m.vendor_category,
        m.is_active,
        m.is_ghost_vendor,
        m.similar_to_vendor,
        m.invoice_count,
        m.total_invoice_amount_jpy,
        m.largest_invoice_amount_jpy,
        m.avg_invoice_z_score,
        m.first_invoice_posting_date,
        m.last_invoice_posting_date,
        CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) AS vendor_age_days_at_analysis,
        'SINGLE_HIGH_VALUE_INVOICE' AS risk_category,
        'Vendor has only one invoice and that invoice exceeds ¥1,000,000.' AS risk_description,
        m.largest_invoice_amount_jpy AS value_at_risk_jpy,
        NULL AS related_vendor_details
    FROM vendor_z_scores AS m
    CROSS JOIN analysis_parameters AS p
    WHERE m.invoice_count = 1
      AND m.largest_invoice_amount_jpy > p.high_payment_jpy

    UNION ALL

    SELECT
        m.vendor_id,
        m.vendor_name,
        m.bank_account_number,
        m.registration_date,
        m.payment_terms,
        m.vendor_category,
        m.is_active,
        m.is_ghost_vendor,
        m.similar_to_vendor,
        m.invoice_count,
        m.total_invoice_amount_jpy,
        m.largest_invoice_amount_jpy,
        m.avg_invoice_z_score,
        m.first_invoice_posting_date,
        m.last_invoice_posting_date,
        CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) AS vendor_age_days_at_analysis,
        'DUPLICATE_BANK_ACCOUNT' AS risk_category,
        'Vendor bank account is used by more than one vendor master record.' AS risk_description,
        m.total_invoice_amount_jpy AS value_at_risk_jpy,
        d.vendor_names_on_bank_account AS related_vendor_details
    FROM vendor_z_scores AS m
    INNER JOIN duplicate_bank_accounts AS d
        ON m.bank_account_number = d.bank_account_number
    CROSS JOIN analysis_parameters AS p

    UNION ALL

    SELECT
        m.vendor_id,
        m.vendor_name,
        m.bank_account_number,
        m.registration_date,
        m.payment_terms,
        m.vendor_category,
        m.is_active,
        m.is_ghost_vendor,
        m.similar_to_vendor,
        m.invoice_count,
        m.total_invoice_amount_jpy,
        m.largest_invoice_amount_jpy,
        m.avg_invoice_z_score,
        m.first_invoice_posting_date,
        m.last_invoice_posting_date,
        CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) AS vendor_age_days_at_analysis,
        'REACTIVATED_AFTER_INACTIVITY' AS risk_category,
        'Vendor had no invoice activity for at least 180 days and then received a new invoice.' AS risk_description,
        r.reactivation_invoice_amount_jpy AS value_at_risk_jpy,
        'Longest inactive gap: ' || r.longest_inactive_gap_days || ' days; reactivation posting date: ' || r.reactivation_posting_date AS related_vendor_details
    FROM vendor_z_scores AS m
    INNER JOIN long_inactivity_reactivations AS r
        ON m.vendor_id = r.vendor_id
    CROSS JOIN analysis_parameters AS p
)
SELECT
    vendor_id,
    vendor_name,
    risk_category,
    risk_description,
    value_at_risk_jpy,
    invoice_count,
    total_invoice_amount_jpy,
    largest_invoice_amount_jpy,
    avg_invoice_z_score,
    registration_date,
    vendor_age_days_at_analysis,
    first_invoice_posting_date,
    last_invoice_posting_date,
    bank_account_number,
    related_vendor_details,
    similar_to_vendor,
    is_ghost_vendor,
    payment_terms,
    vendor_category,
    is_active
FROM abnormal_reasons
ORDER BY value_at_risk_jpy DESC, vendor_name, risk_category;

-- Executive roll-up: abnormal vendor exposure by risk category.
WITH analysis_parameters AS (
    SELECT MAX(posting_date) AS analysis_date, 90 AS recent_vendor_days, 1000000 AS high_payment_jpy, 180 AS inactive_days, 2.5 AS z_score_threshold FROM invoices
), vendor_invoice_metrics AS (
    SELECT v.vendor_id, v.vendor_name, v.bank_account_number, v.registration_date, COUNT(i.invoice_id) AS invoice_count,
           COALESCE(SUM(CAST(i.invoice_amount AS INTEGER)), 0) AS total_invoice_amount_jpy,
           COALESCE(MAX(CAST(i.invoice_amount AS INTEGER)), 0) AS largest_invoice_amount_jpy,
           AVG(CAST(i.invoice_amount AS REAL)) AS average_invoice_amount_jpy
    FROM vendors AS v
    LEFT JOIN invoices AS i ON v.vendor_id = i.vendor_id
    GROUP BY v.vendor_id, v.vendor_name, v.bank_account_number, v.registration_date
), portfolio_statistics AS (
    SELECT
        AVG(average_invoice_amount_jpy) AS portfolio_average_invoice_jpy,
        AVG(average_invoice_amount_jpy * average_invoice_amount_jpy)
            - AVG(average_invoice_amount_jpy) * AVG(average_invoice_amount_jpy) AS portfolio_average_invoice_variance
    FROM vendor_invoice_metrics
    WHERE invoice_count > 0
), vendor_z_scores AS (
    SELECT
        m.*,
        CASE
            WHEN ps.portfolio_average_invoice_variance > 0 THEN
                (m.average_invoice_amount_jpy - ps.portfolio_average_invoice_jpy) / SQRT(ps.portfolio_average_invoice_variance)
            ELSE 0
        END AS avg_invoice_z_score
    FROM vendor_invoice_metrics AS m
    CROSS JOIN portfolio_statistics AS ps
), duplicate_bank_accounts AS (
    SELECT bank_account_number FROM vendors WHERE bank_account_number IS NOT NULL AND TRIM(bank_account_number) <> '' GROUP BY bank_account_number HAVING COUNT(*) > 1
), invoice_gaps AS (
    SELECT vendor_id, invoice_id, posting_date, invoice_amount,
           LAG(posting_date) OVER (PARTITION BY vendor_id ORDER BY posting_date, invoice_id) AS previous_posting_date
    FROM invoices
), long_inactivity_events AS (
    SELECT
        vendor_id,
        CAST(invoice_amount AS INTEGER) AS reactivation_invoice_amount_jpy,
        ROW_NUMBER() OVER (
            PARTITION BY vendor_id
            ORDER BY
                CAST(julianday(posting_date) - julianday(previous_posting_date) AS INTEGER) DESC,
                posting_date DESC,
                invoice_id DESC
        ) AS inactivity_rank
    FROM invoice_gaps
    WHERE previous_posting_date IS NOT NULL
      AND CAST(julianday(posting_date) - julianday(previous_posting_date) AS INTEGER) >= (SELECT inactive_days FROM analysis_parameters)
), long_inactivity_reactivations AS (
    SELECT vendor_id, reactivation_invoice_amount_jpy
    FROM long_inactivity_events
    WHERE inactivity_rank = 1
), abnormal_reasons AS (
    SELECT m.vendor_id, 'NEW_VENDOR_HIGH_PAYMENT' AS risk_category, m.total_invoice_amount_jpy AS value_at_risk_jpy
    FROM vendor_z_scores AS m CROSS JOIN analysis_parameters AS p
    WHERE CAST(julianday(p.analysis_date) - julianday(m.registration_date) AS INTEGER) BETWEEN 0 AND p.recent_vendor_days
      AND m.total_invoice_amount_jpy > p.high_payment_jpy
    UNION ALL
    SELECT m.vendor_id, 'ABNORMAL_AVERAGE_INVOICE_AMOUNT' AS risk_category, m.total_invoice_amount_jpy AS value_at_risk_jpy
    FROM vendor_z_scores AS m CROSS JOIN analysis_parameters AS p
    WHERE ABS(m.avg_invoice_z_score) > p.z_score_threshold
    UNION ALL
    SELECT m.vendor_id, 'SINGLE_HIGH_VALUE_INVOICE' AS risk_category, m.largest_invoice_amount_jpy AS value_at_risk_jpy
    FROM vendor_z_scores AS m CROSS JOIN analysis_parameters AS p
    WHERE m.invoice_count = 1 AND m.largest_invoice_amount_jpy > p.high_payment_jpy
    UNION ALL
    SELECT m.vendor_id, 'DUPLICATE_BANK_ACCOUNT' AS risk_category, m.total_invoice_amount_jpy AS value_at_risk_jpy
    FROM vendor_z_scores AS m INNER JOIN duplicate_bank_accounts AS d ON m.bank_account_number = d.bank_account_number
    UNION ALL
    SELECT m.vendor_id, 'REACTIVATED_AFTER_INACTIVITY' AS risk_category, r.reactivation_invoice_amount_jpy AS value_at_risk_jpy
    FROM vendor_z_scores AS m INNER JOIN long_inactivity_reactivations AS r ON m.vendor_id = r.vendor_id
)
SELECT
    risk_category,
    COUNT(*) AS abnormal_vendor_flags,
    COUNT(DISTINCT vendor_id) AS distinct_vendors,
    SUM(value_at_risk_jpy) AS total_value_at_risk_jpy
FROM abnormal_reasons
GROUP BY risk_category
ORDER BY total_value_at_risk_jpy DESC;

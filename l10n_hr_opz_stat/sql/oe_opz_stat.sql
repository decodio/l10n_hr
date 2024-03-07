-- Function: oe_rep_aged_partner_balance(date,int)

-- DROP FUNCTION oe_opz_stat(date, bigint);

/* DEBUG
select *
from oe_opz_stat(
        _date_to   := '2016-12-31'
        ,_opz_id   := 38998192
)

*/

CREATE OR REPLACE FUNCTION oe_opz_stat(IN _date_to date, IN _opz_id bigint) RETURNS varchar AS
$BODY$
BEGIN

WITH inv_data AS (
--        with r_line as(
--           SELECT amrl.move_line_id, amrl.closing_amount
--              FROM account_move_reconcile_line amrl
--              JOIN account_move_line amli on amli.id = amrl.move_line_id
--              JOIN account_move_line amlp on amlp.id = amrl.reconciled_move_line_id
--             WHERE amrl.reconciled_move_line_id is not null
--               AND amrl.move_line_id is not null
--               AND amrl.closing_amount !=0.0
--               AND amrl.reconciliation_date <= date_trunc('month', (_date_to::date  + INTERVAL '1 month'))::date + INTERVAL '1 month' - interval '1 day'
--               AND amli."date" <= _date_to
--               AND amlp."date" <= date_trunc('month', (_date_to::date  + INTERVAL '1 month'))::date + INTERVAL '1 month' - interval '1 day'
--           )
    WITH r_line AS (
        SELECT apr.debit_move_id AS move_line_id, COALESCE(apr.amount, apr.amount_currency) AS closing_amount
            FROM account_partial_reconcile apr
            WHERE 1 = 1
            AND apr.max_date <= _date_to
            AND apr.max_date <= date_trunc('month', (_date_to::date  + INTERVAL '1 month'))::date + INTERVAL '1 month' - interval '1 day'
    )
    ,ml_closed AS (
        SELECT rl.move_line_id, SUM(rl.closing_amount) AS closed_amount
            FROM r_line rl
        GROUP BY rl.move_line_id
    )
    ,open_move_line AS (
        SELECT aml.partner_id
            ,COALESCE(inv.date_invoice, aml.date) AS date_invoice
            ,COALESCE(aml.date_maturity, inv.date_due) AS date_due
            ,inv."id" AS invoice_id
            ,COALESCE(inv.number, aml.name) AS invoice_number
            ,COALESCE(inv.amount_untaxed, 0.0) AS invoice_amount
            ,COALESCE(inv.amount_tax, 0.0) AS invoice_amount_tax
            ,COALESCE(inv.amount_total, 0.0) AS invoice_amount_total
            ,am.state AS move_state
            ,COALESCE( NULLIF(aml.amount_currency, 0.0), aml.debit - aml.credit) AS amount_currency
            --,aml.debit - aml.credit as amount_lcy
            ,CASE WHEN (aml.debit + aml.credit) != 0.0
                  THEN COALESCE(ABS(NULLIF(aml.amount_currency,0.0)), ABS(aml.debit + aml.credit))/ABS(aml.debit + aml.credit)
                  ELSE 1.0
              END AS currency_rate
            --,Coalesce(aml.currency_id, rc.currency_id) as currency_id
            ,CASE WHEN (COALESCE(NULLIF(aml.amount_currency,0.0), aml.debit - aml.credit)) > 0.00
                  THEN (COALESCE(NULLIF(aml.amount_currency,0.0), aml.debit - aml.credit)) - COALESCE(mc.closed_amount, 0.0)
                  ELSE (COALESCE(NULLIF(aml.amount_currency,0.0), aml.debit - aml.credit)) + COALESCE(mc.closed_amount, 0.0)
              END as open_amount
             ,(CASE WHEN COALESCE(mc.closed_amount, 0.0) > 0.0 THEN mc.closed_amount ELSE 0.0 END) AS closed_amount
            --,Coalesce(aml.date_maturity, aml."date") as date_maturity
            --,aml."date" as posting_date
        FROM account_move_line aml
        JOIN account_move am ON (aml.move_id = am.id)
        JOIN account_account aa ON (aml.account_id = aa.id)
        JOIN account_account_type aat ON (aa.user_type_id = aat.id)
        LEFT JOIN account_invoice inv ON (inv.move_id = aml.move_id)
        LEFT JOIN res_company rc ON (aml.company_id = rc.id)
        LEFT JOIN ml_closed mc ON (mc.move_line_id = aml.id)
        WHERE 1 = 1
        AND aat.type in ('receivable')
        AND am.state = 'posted'
        AND COALESCE(aa.exclude_from_opz_stat, FALSE) = FALSE
        AND COALESCE(aml.date_maturity, inv.date_due) <= _date_to  --+ INTERVAL '1 month'
    )
    SELECT oml.partner_id
        ,par.name AS partner_name
        ,COALESCE((CASE WHEN par.vat LIKE 'HR%'
                        THEN SUBSTRING(par.vat, 3)
                   ELSE par.vat
                   END), '-') AS partner_vat_number
        ,(CASE WHEN par.vat LIKE 'HR%'
               THEN 'vat'
          ELSE 'vatid' END) AS partner_vat_type
        ,(CASE WHEN oml.date_invoice > oml.date_due THEN oml.date_due ELSE oml.date_invoice END ) AS date_invoice
        ,oml.date_due
        ,oml.invoice_id
        ,oml.invoice_number
        ,ROUND((CASE WHEN oml.currency_rate != 0.0
            THEN oml.invoice_amount / oml.currency_rate
            ELSE oml.invoice_amount
         END::numeric), 2) AS lcy_invoice_amount
        ,ROUND((CASE WHEN oml.currency_rate != 0.0
            THEN oml.invoice_amount_tax / oml.currency_rate
            ELSE oml.invoice_amount_tax
        END::numeric),2) AS lcy_invoice_amount_tax
        ,ROUND((CASE WHEN oml.currency_rate != 0.0
            THEN oml.invoice_amount_total / oml.currency_rate
            ELSE oml.invoice_amount_total
        END::numeric),2) AS lcy_invoice_amount_total
        ,((date_trunc('month', (_date_to::date  + INTERVAL '1 month'))::date + INTERVAL '1 month' - interval '1 day')::date - oml.date_due)
           AS overdue_days
        ,ROUND((CASE WHEN oml.currency_rate != 0.0
            THEN oml.closed_amount / oml.currency_rate
            ELSE oml.closed_amount
        END::numeric), 2) AS closed_amount  -- lcy_closed_amount
        --,oml.date_maturity::date
        --,oml.posting_date::date
        ,ROUND((CASE WHEN oml.currency_rate != 0.0
            THEN oml.open_amount / oml.currency_rate
            ELSE oml.open_amount
        END::numeric), 2) AS open_amount_lcy
        FROM open_move_line as oml
        JOIN res_partner par ON par.id = oml.partner_id
        WHERE 1 = 1
        AND oml.open_amount != 0.0
        AND oml.invoice_amount_total != 0.0
)
INSERT INTO opz_stat_line(
       due_date  , partner_name  , invoice_id  , invoice_date  , opz_id , amount_tax          , unpaid          , amount
      ,partner_vat_number  , partner_vat_type , invoice_number  , partner_id  , amount_total          , overdue_days , paid
       ,create_uid, create_date          , write_date           , write_uid)
SELECT d.date_due, d.partner_name, d.invoice_id, d.date_invoice, _opz_id, d.lcy_invoice_amount_tax, d.open_amount_lcy, d.lcy_invoice_amount
      ,d.partner_vat_number, d.partner_vat_type, d.invoice_number, d.partner_id, d.lcy_invoice_amount_total, d.overdue_days, d.closed_amount
       ,1         , timezone('UTC', now()), timezone('UTC', now()), 1
 FROM inv_data d
WHERE d.open_amount_lcy != 0.0 AND d.invoice_number IS NOT NULL -- can happen, garbage in data
AND NOT EXISTS (SELECT 1 FROM opz_stat_line opzl WHERE opzl.partner_id = d.partner_id
                    AND (opzl.invoice_id IS NOT NULL AND opzl.invoice_id = d.invoice_id)
                    AND opzl.opz_id =_opz_id
                )
;
RETURN '';
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;

-- Function: oe_rep_aged_partner_balance(date,int)

-- DROP FUNCTION oe_opz_stat(date, bigint);

CREATE OR REPLACE FUNCTION oe_opz_stat(
                            IN _date_to date
                            ,IN _opz_id bigint
                           )
  RETURNS varchar AS

$BODY$
BEGIN

/* DEBUG
select *
from oe_opz_stat(
        _date_to   := '2016-12-31'
        ,_opz_id   := 38998192
)

*/
WITH inv_data AS (
        with r_line as(
           SELECT amrl.move_line_id, amrl.closing_amount
              FROM account_move_reconcile_line amrl
              JOIN account_move_line amli on amli.id = amrl.move_line_id
              JOIN account_move_line amlp on amlp.id = amrl.reconciled_move_line_id
             WHERE amrl.reconciled_move_line_id is not null
               AND amrl.move_line_id is not null
               AND amrl.closing_amount !=0.0
               AND amrl.reconciliation_date  <= _date_to  + INTERVAL '1 month'
               AND amli."date" <= _date_to
               AND amlp."date" <= _date_to
           )
        ,ml_closed AS(
            SELECT rl.move_line_id, sum(rl.closing_amount) as closed_amount
              FROM r_line rl
          GROUP BY rl.move_line_id
        )
        ,open_move_line AS (
           SELECT aml.partner_id
                ,coalesce(inv.date_invoice, aml."date") as date_invoice
                ,coalesce(inv.date_due, aml.date_maturity) as date_due
                ,inv."id" as invoice_id
                ,coalesce(inv."number", aml."name") as invoice_number
                ,coalesce(inv.amount_untaxed,0.0) as invoice_amount
                ,coalesce(inv.amount_tax, 0.0) as invoice_amount_tax
                ,coalesce(inv.amount_total,0.0) as invoice_amount_total
                ,am.state as move_state
                ,Coalesce( Nullif(aml.amount_currency, 0.0), aml.debit - aml.credit) as amount_currency
                --,aml.debit - aml.credit as amount_lcy
                ,CASE WHEN (aml.debit + aml.credit) != 0.0
                      THEN Coalesce(ABS(Nullif(aml.amount_currency,0.0)), ABS(aml.debit + aml.credit))/ABS(aml.debit + aml.credit)
                      ELSE 1.0
                  END as currency_rate
                --,Coalesce(aml.currency_id, rc.currency_id) as currency_id
                ,CASE WHEN (Coalesce(Nullif(aml.amount_currency,0.0), aml.debit - aml.credit)) > 0.00
                      THEN (Coalesce(Nullif(aml.amount_currency,0.0), aml.debit - aml.credit)) - coalesce(mc.closed_amount, 0.0)
                      ELSE (Coalesce(Nullif(aml.amount_currency,0.0), aml.debit - aml.credit)) + coalesce(mc.closed_amount, 0.0)
                  END as open_amount
                 ,(CASE WHEN coalesce(mc.closed_amount, 0.0) > 0.0 THEN mc.closed_amount ELSE 0.0 END) as closed_amount
                --,Coalesce(aml.date_maturity, aml."date") as date_maturity
                --,aml."date" as posting_date
            FROM account_move_line  aml
            left join account_account    aa on aa.id=aml.account_id
            left join account_move       am on am.id=aml.move_id
            --left join account_journal    aj on aj.id=aml.journal_id
            left join res_company        rc on rc.id=aml.company_id
            left join ml_closed          mc on mc.move_line_id=aml.id
            LEFT join account_invoice        inv on inv.move_id = aml.move_id

           WHERE 1=1
            /*
             AND Coalesce(nullif(aml.amount_currency, 0.0), aml.debit + aml.credit)
                 - nullif(mc.closed_amount, 0.0) --as open_amount
                 != 0.0
            */
             AND aa.type in ('receivable')
             AND (aa.exclude_from_opz_stat is NULL OR aa.exclude_from_opz_stat = False)
             AND coalesce(aml.curr_exch_difference,False)= False
             --AND aml."date" <= _date_from -- (_from_date)
             AND aml.date_maturity <= _date_to  --+ INTERVAL '1 month'
             AND am."state" = 'posted'
             --AND account_account.active
            -- AND (_partner_id = 0 OR coalesce(aml.partner_id, -1) = coalesce(_partner_id, -1) ) --speed
        )
         SELECT oml.partner_id
                ,par."name" as partner_name
                ,COALESCE((CASE WHEN par.vat LIKE 'HR%' THEN SUBSTRING(par.vat, 3)
                               ELSE par.vat END), '-') as partner_vat_number
                 ,(CASE WHEN par.vat LIKE 'HR%' THEN 'vat'
                               ELSE 'vatid' END) as partner_vat_type
                ,(CASE WHEN oml.date_invoice > oml.date_due THEN oml.date_due ELSE oml.date_invoice END ) AS date_invoice
                ,oml.date_due
                ,oml.invoice_id
                ,oml.invoice_number
                ,ROUND((CASE WHEN oml.currency_rate != 0.0
                    THEN oml.invoice_amount / oml.currency_rate
                    ELSE oml.invoice_amount
                 END::numeric),2) as lcy_invoice_amount
                ,ROUND((CASE WHEN oml.currency_rate != 0.0
                    THEN oml.invoice_amount_tax / oml.currency_rate
                    ELSE oml.invoice_amount_tax
                END::numeric),2) as lcy_invoice_amount_tax
                ,ROUND((CASE WHEN oml.currency_rate != 0.0
                    THEN oml.invoice_amount_total / oml.currency_rate
                    ELSE oml.invoice_amount_total
                END::numeric),2) as lcy_invoice_amount_total
                ,(_date_to::date - oml.date_due) as overdue_days
               --,oml.move_state::varchar
               --,oml.amount_currency::numeric
               --,oml.amount_lcy::numeric
               --,oml.currency_rate::numeric
               --,oml.currency_id::int
               --,ROUND((oml.open_amount::numeric),2) as open_amount
               ,oml.closed_amount::numeric
               --,oml.date_maturity::date
               --,oml.posting_date::date
              ,ROUND((CASE WHEN oml.currency_rate != 0.0
                    THEN oml.open_amount / oml.currency_rate
                    ELSE oml.open_amount
              END::numeric),2) as open_amount_lcy

          FROM open_move_line as oml
          JOIN res_partner par ON par.id = oml.partner_id
          where oml.open_amount > 0.0
          AND oml.invoice_amount_total >= 0.0
        )
INSERT INTO opz_stat_line(
       due_date  , partner_name  , invoice_id  , invoice_date  , opz_id , amount_tax          , unpaid          , amount
      ,partner_vat_number  , partner_vat_type , invoice_number  , partner_id  , amount_total          , overdue_days , paid
       ,create_uid, create_date          , write_date           , write_uid)
SELECT d.date_due, d.partner_name, d.invoice_id, d.date_invoice, _opz_id, d.lcy_invoice_amount_tax, d.open_amount_lcy, d.lcy_invoice_amount
      ,d.partner_vat_number, d.partner_vat_type, d.invoice_number, d.partner_id, d.lcy_invoice_amount_total, d.overdue_days, d.closed_amount
       ,1         , timezone('UTC', now()), timezone('UTC', now()), 1
 FROM inv_data d
WHERE d.open_amount_lcy > 0.0
AND NOT EXISTS (SELECT 1 FROM opz_stat_line opzl WHERE opzl.partner_id = d.partner_id
                                                     AND (opzl.invoice_id IS nOT NULL AND opzl.invoice_id = d.invoice_id)
                                                     AND opzl.opz_id =_opz_id
                    )
;


RETURN '';
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

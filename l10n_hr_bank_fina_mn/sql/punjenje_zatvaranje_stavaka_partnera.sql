UPDATE account_move_line acm SET payment_ref = inv.reference 
FROM account_invoice inv
        LEFT JOIN account_move am ON (am.id = inv.move_id)
        LEFT JOIN account_move_line aml ON (am.id = aml.move_id)
        WHERE acm.id = aml.id
                AND aml.payment_ref IS NULL

UPDATE account_move_line aml SET amount_unreconciled = 
        (SELECT 
          CASE 
            WHEN aml2.amount_currency <> 0.0 THEN aml2.amount_currency
           WHEN aml2.debit <> 0.0 THEN aml2.debit
           ELSE -aml2.credit
          END as amount
        FROM account_move_line aml2
        WHERE aml2.id =aml.id)
WHERE partner_id IS NOT NULL
  AND invoice_line_id IS NULL
  AND account_id IN (select id from account_account WHERE type IN ('receivable', 'payable'))


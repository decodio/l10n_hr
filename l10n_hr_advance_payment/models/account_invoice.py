from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    advance_payment = fields.Boolean(string='Advance Payment', index=True, default=False, copy=False)
    advance_invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='account_advance_invoice_invoice_rel',
        column1='invoice_id', column2='advance_invoice_id',
        string='Advance Invoices', readonly=False, copy=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        res = super()._onchange_journal_id()
        if self.journal_id.advance_payment:
            self.advance_payment = self.journal_id.advance_payment
        return res

    def action_move_create(self):
        res = super().action_move_create()
        aml_obj = self.env['account.move.line']
        for invoice in self:
            advance_payment_move_lines = aml_obj
            for advance in invoice.advance_invoice_ids.filtered(lambda adv: adv.state in {'open', 'paid'}):
                advance_move_line = advance.move_id.line_ids.filtered(
                    lambda l: l.account_id == advance.account_id and l.full_reconcile_id)
                advance_payment_move_line = advance_move_line.full_reconcile_id.reconciled_line_ids - advance_move_line
                # remove payment reconciliation
                advance_payment_move_line.remove_move_reconcile()
                # save reference to payments for next reconciliation
                advance_payment_move_lines |= advance_payment_move_line
                # reverse moves and reconcile it
                advance.move_id and advance.move_id.reverse_moves_insert_into_existing(date=invoice.date_invoice,
                                                                                       existing_move=invoice.move_id)
            if advance_payment_move_lines:
                aml_obj._reconcile_lines(invoice.move_id.line_ids.
                                         filtered(lambda l: l.account_id == advance_move_line.account_id),
                                         advance_payment_move_lines, 'amount_residual')
        return res

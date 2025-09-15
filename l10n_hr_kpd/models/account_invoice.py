from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        for line_info in res:
            line_info['l10n_hr_kpd_id'] = self.invoice_line_ids.filtered(
                lambda line: line.id == line_info['invl_id']).l10n_hr_kpd_id.id
        return res
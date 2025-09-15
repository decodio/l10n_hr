from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_hr_business_process_type_id = fields.Many2one(
        comodel_name='l10n.hr.business.process.type',
        string="Business Process Type")

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        res = super()._onchange_journal_id()
        if self.company_id.country_id.code != "HR":
            return res
        if self.journal_id.l10n_hr_business_process_type_id:
            self.l10n_hr_business_process_type_id = self.journal_id.l10n_hr_business_process_type_id.id
        return res

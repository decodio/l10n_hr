from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_hr_untdid1001_document_type_id = fields.Many2one(
        comodel_name='l10n.hr.document.type',
        readonly=True, states={'draft': [('readonly', False)]},
        string="Document Type")

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        res = super()._onchange_journal_id()
        if self.company_id.country_id.code != "HR":
            return res
        # Better safe than sorry
        # if self.journal_id.l10n_hr_untdid1001_document_type_id:
        #     self.l10n_hr_untdid1001_document_type_id = self.journal_id.l10n_hr_untdid1001_document_type_id.id
        return res

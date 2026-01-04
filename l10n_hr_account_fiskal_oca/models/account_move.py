# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _gen_fiskal_number(self, invoice, move):
        # don't change fiscal_number if fiscalization is started
        if invoice.zki:
            return
        return super()._gen_fiskal_number(invoice, move)

    @api.multi
    def post(self, invoice=False):
        res = super(AccountMove, self).post(invoice=invoice)
        bp_type = (invoice and invoice.l10n_hr_business_process_type_id
                   and invoice.l10n_hr_business_process_type_id.code or '')
        # Do not check/fiscalize for other business process types
        if bp_type != 'XF1':
            return res
        if invoice and invoice.type in ('out_invoice', 'out_refund') \
                and invoice.company_id.croatia and invoice.journal_id.fiscalisation_active:
            invoice.fiskaliziraj()
        return res

# -*- coding: utf-8 -*-
# © 2016 DECODIO (<http://www.decod.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(
            self, grouped=False, states=None, date_invoice=False):
        invoice_id = super(SaleOrder, self).action_invoice_create(
            grouped=grouped, states=states, date_invoice=date_invoice)
        if self.journal_id and self.journal_id.nac_plac:
            self.env['account.invoice'].browse(invoice_id).write(
                {'nac_plac': self.journal_id.nac_plac})
        return invoice_id

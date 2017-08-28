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
        for invoice in self:
            if invoice.journal_id and invoice.journal_id.nac_plac:
                uredjaj_id = invoice.journal_id .fiskal_uredjaj_ids and \
                             invoice.journal_id.fiskal_uredjaj_ids[0].id or False
                self.env['account.invoice'].browse(invoice_id).write(
                    {'nac_plac': invoice.journal_id.nac_plac,
                     'journal_id': invoice.journal_id and invoice.journal_id.id or False,
                     'uredjaj_id': uredjaj_id})
        return invoice_id


class sale_order_line_make_invoice(models.TransientModel):
    _inherit = "sale.order.line.make.invoice"

    @api.model
    def _prepare_invoice(self, order, lines):
        res = super(sale_order_line_make_invoice, self)._prepare_invoice(order,lines)
        journal_id = order.journal_id and order.journal_id.id or self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            uredjaj_id = journal.fiskal_uredjaj_ids and \
                         journal.fiskal_uredjaj_ids[0].id or None
            nac_plac = journal.nac_plac or None
        if res and journal_id:
            res.update({'nac_plac': nac_plac,
                        'uredjaj_id': uredjaj_id
                        })
        return res
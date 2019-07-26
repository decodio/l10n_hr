# -*- coding: utf-8 -*-
# © 2016 DECODIO (<http://www.decod.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move, picking=None):
        res = super(StockPicking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            uredjaj_id = journal.fiskal_uredjaj_ids and journal.fiskal_uredjaj_ids[0].id or None
            nac_plac = journal.nac_plac or None
            res.update({
                'uredjaj_id': uredjaj_id,
                'nac_plac': nac_plac,
                })
        return res

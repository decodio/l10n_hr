# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = "res.company"

    # Fields, DB: NAMJERNO SU SVI NAZIVI NA HRVATSKOM!

    nkd_id = fields.Many2one(
        comodel_name='l10n.hr.nkd',
        string="NKD",
        help="Glavna djelatnost klasificirana prema NKD-2007")



    @api.onchange('nkd_id')
    def _onchange_nkd_id(self):
        self.nkd = self.nkd_id.code
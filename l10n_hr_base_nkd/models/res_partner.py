# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = "res.partner"

    nkd_id = fields.Many2one(
        comodel_name='l10n.hr.nkd',
        string="NKD",
        help="Glavna djelatnost klasificirana prema NKD-2007")

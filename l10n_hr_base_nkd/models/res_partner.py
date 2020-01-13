# -*- encoding: utf-8 -*-

import pytz
from tzlocal import get_localzone
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class Partenr(models.Model):
    _inherit = "res.partner"

    nkd_id = fields.Many2one(
        comodel_name='l10n.hr.nkd',
        string="NKD",
        help="Glavna djelatnost klasificirana prema NKD-2007")

# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError


class Users(models.Model):
    _inherit = 'res.users'

    vat = fields.Char(
        related='partner_id.vat',
        inherited=True,
        help="Mandatory only for users that needs to validate invoices")

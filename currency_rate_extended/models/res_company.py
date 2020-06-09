# Copyright 2020 Decodio Applications d.o.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import Warning


class Company(models.Model):
    _inherit = 'res.company'

    currency_rate_provider_id = fields.Many2one(
        comodel_name='res.currency.rate.provider',
        string="Default currency rate provider",
        sp_8="base_base.update_service_id",
        help="Default currency rate provider in case you use more than one",
        old_sp_name="update_service_id"
    )
    inverse_currency_rate = fields.Boolean(
        string="Inverse currency rate",
        sp_8="base_base,inverse_currency_rate",
        help="""
Normal rate is expressed as Amount of domestic for one foreign, 
Inverse rate is expressed as Amount domestic 
for one(or more) foreign.  Example: 0,13333  <-> 7,5
"""
    )


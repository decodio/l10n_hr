# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # DB: netrebam fiskal_percent...
    hr_fiskal_type = fields.Selection(
        selection=[
            ('Pdv', 'PDV'),
            ('Pnp', 'Porez na potrosnju'),
            ('OstaliPor', 'Ostali porezi'),
            ('oslobodenje', 'Oslobodjenje'),
            ('marza', 'Oporezivanje marze'),
            ('ne_podlijeze', 'Ne podlijeze oporezivanju'),
            ('Naknade', 'Naknade (npr. ambalaza)')],
        string="Fiskalni tip poreza",
        domain="[('type_tax_use', '!=', 'purchase')]")

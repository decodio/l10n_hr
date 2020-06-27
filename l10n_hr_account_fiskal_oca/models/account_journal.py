# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # FIELDS
    fiscalisation_active = fields.Boolean(
        string="Fiskaliziranje računa",
        help="Fiskalizacija aktivna za ovaj dnevnik")
    default_nacin_placanja = fields.Selection(
        selection_add=[
            ('G', 'GOTOVINA'),
            ('K', 'KARTICE'),
            ('C', 'CEKOVI'),
            ('O', 'OSTALO')
        ])

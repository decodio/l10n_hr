# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_hr_hnb_rate = fields.Selection(
        selection=[
            ('kupovni', 'Buy rate'),
            ('srednji', 'Mid rate'),
            ('prodajni', 'Sell rate')
        ], string="Rate type", default='srednji'
    )


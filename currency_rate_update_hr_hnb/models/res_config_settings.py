# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

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


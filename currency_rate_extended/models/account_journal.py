# Copyright 2020 Decodio Applications d.o.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    currency_rate_provider_id = fields.Many2one(
        comodel_name='res.currency.rate.provider',
        string="Currency rate provider",
        help="Specific currency rate provider for this journal",
        old_name="currency_update_service_id"
    )


# Copyright 2020 Decodio Applications d.o.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    currency_rate_provider_id = fields.Many2one(
        comodel_name='res.currency.rate.provider',
        string="Default currency rate provider",
        old_name="update_service_id",
        help="Default currency rate provider in case you use more than one",
        # sp_8="base_base.update_service_id",
        # old_sp_name="update_service_id"
    )
    inverse_currency_rate = fields.Boolean(
        string="Inverse currency rate",
        help="Normal rate is expressed as Amount of domestic for one foreign,"
             "Inverse rate is expressed as Amount domestic"
             "for one(or more) foreign.  Example: 0,13333  <-> 7,5"
        # sp_8 = "base_base,inverse_currency_rate",
    )
    # country_id = fields.Many2one(store=False)

    # @api.one
    # @api.depends("country_id", "country_id.inverse_currency_rate")
    # def _get_inverse_curreny_rate(self):
    #     if self.country_id and self.country_id.inverse_currency_rate:
    #         self.inverse_currency_rate = self.country_id.inverse_currency_rate
    #     else:
    #         self.inverse_currency_rate = False

    @api.multi
    def on_change_country(self, country_id):
        # This function is called from account/models/chart_template.py,
        # hence decorated with `multi`.
        res = super().on_change_country(country_id)
        inverse_currency_rate = False
        if country_id:
            inverse_currency_rate = self.env['res.country'].browse(
                country_id).inverse_currency_rate
        res['value']['inverse_currency_rate'] = inverse_currency_rate
        return res

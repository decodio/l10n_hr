# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
from datetime import timedelta
import urllib.request as request

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResCurrencyRateProvider_HR_HNB(models.Model):
    _inherit = 'res.currency.rate.provider'

    service = fields.Selection(
        selection_add=[('HR-HNB', 'Croatia-HNB')],
    )
    rate_type = fields.Selection(
        selection=[
            ('kupovni', 'Buy rate'),
            ('srednji', 'Mid rate'),
            ('prodajni', 'Sell rate')
        ], string="Rate type", default='srednji'
    )

    @api.multi
    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != 'HR-HNB':
            return super()._get_supported_currencies()  # pragma: no cover

        data = self._l10n_hr_hnb_urlopen()
        currencies = [c['valuta'] for c in data]
        # BOLE: ovo paziti jer moguce je da bas na taj dan nemam
        # sve valute.. ali very low impact pa se ne mucim oko ovog
        return currencies


    @api.multi
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != 'HR-HNB':
            return super()._obtain_rates(base_currency, currencies, date_from,
                                         date_to)  # pragma: no cover
        result = {}
        currencies = [c.name for c in self.currency_ids]
        data = self._l10n_hr_hnb_urlopen(
            currencies=currencies,
            date_from=date_from, date_to=date_to)
        for cd in data:
            currency = cd['valuta']
            if currency not in currencies:
                continue
            rate_date = cd['datum_primjene']


            qty = cd['jedinica']
            rate = cd.get(self.rate_type + '_tecaj').replace(',', '.')
            try:
                rate = float(rate)
            except:
                continue
            if not result.get(rate_date):
                result[rate_date] = {currency: rate}
            else:
                result[rate_date].update({currency: rate})

        return result


    @api.multi
    def _l10n_hr_hnb_urlopen(self, currencies=None, date_from=None, date_to=None):
        url = "http://api.hnb.hr/tecajn/v2"
        if date_from is not None:
            if date_to is not None:
                url += "?datum-primjene-od=%s&datum-primjene-do=%s" % (
                    fields.Date.to_string(date_from),
                    fields.Date.to_string(date_to)
                )
        if currencies is not None:
            for cur in currencies:
                url += "?valuta=" + cur

        res = request.urlopen(url)
        data = json.loads(res.read().decode("UTF-8"))
        return data


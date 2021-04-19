# Copyright 2020 Decodio Applications d.o.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from lxml import etree, objectify
from odoo import models, fields, api


class Currency(models.Model):
    _inherit = "res.currency"

    rate_inverse = fields.Float(
        string="Inverse rate",
        digits=(16, 6), default=1.0,
        compute='_compute_current_rate',
        help='The rate of the currency of rate 1 to the currency'
    )

    def _get_rates(self, company, date, provider_id=None):
        """
        Override base.res_currency method:
        - currency_rate has default on company_id so it is never null
        - retrieve rate set on company or first one if not set on company

        BEWARE: if provider is set on company, but not yet updated,
                even if some rates exist in database shown rates will be 1!
        """

        if provider_id is None:
            journal_id = self.env.context.get('journal_id')
            if journal_id:
                # comming from account_invoice with journal_id in context
                # need to check all cases for this
                journal = self.env['account.journal'].browse(journal_id)
                provider_id = journal.currency_rate_provider_id and \
                                journal.currency_rate_provider_id.id or False

        if not provider_id:
            # provider not set on journal, OR journal did not came in context!
            provider_id = company.currency_rate_provider_id and \
                          company.currency_rate_provider_id.id or False

        # if still no provider id:
        # check if 1. only one provider is defined on company...
        params = {
            'date': date,
            'company': company.id,
            'currency_ids': tuple(self.ids)
        }
        if provider_id:
            query = """
            SELECT c.id
                 , COALESCE(
                   (SELECT r.rate 
                    FROM res_currency_rate r
                    WHERE r.currency_id = c.id 
                      AND r.name <= %(date)s
                      AND (r.company_id IS NULL OR r.company_id = %(company)s)
                      AND r.provider_id = %(provider)s
                    ORDER BY r.company_id, r.name DESC
                    LIMIT 1), 1.0) AS rate
            FROM res_currency c
            WHERE c.id IN %(currency_ids)s
            """
            params['provider'] = provider_id
        else:
            query = """
            SELECT c.id
                 , COALESCE((SELECT r.rate FROM res_currency_rate r
                                      WHERE r.currency_id = c.id AND r.name <= %(date)s
                                        AND (r.company_id IS NULL OR r.company_id = %(company)s)
                                   ORDER BY r.company_id, r.name DESC
                                      LIMIT 1), 1.0) AS rate
                       FROM res_currency c
                       WHERE c.id IN %(currency_ids)s
            """
        self.env.cr.execute(query, params)
        currency_rates = dict(self._cr.fetchall())
        return currency_rates

    def _get_current_company(self):
        company = self.env['res.company'].browse(
            self._context.get('company_id')) or \
            self.env['res.users']._get_company()
        return company

    @api.model
    def _get_rate_or_inverse_rate(self, from_currency, to_currency, company, date):
        rate = self._get_conversion_rate(
            from_currency, to_currency, company, date)
        if company.inverse_currency_rate and rate:
            return 1 / rate
        else:
            return rate

    def _convert(self, from_amount, to_currency, company, date, round=True,
                 force_rate=None):
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
           :param force_rate: apply manually entered rate
        """

        if force_rate:
            if self == to_currency:
                to_amount = from_amount
            else:
                if company.inverse_currency_rate:
                    to_amount = from_amount * (1 / force_rate)
                else:
                    to_amount = from_amount * force_rate
            return to_currency.round(to_amount) if round else to_amount

        return super()._convert(
            from_amount, to_currency, company, date, round=round)

    @api.multi
    @api.depends('rate_ids.rate')
    def _compute_current_rate(self):
        date = self._context.get('date') or fields.Date.today()
        company = self._get_current_company()
        # the subquery selects the last rate before 'date'
        # for the given currency/company
        currency_rates = self._get_rates(company, date)
        for currency in self:
            currency.rate = currency_rates.get(currency.id) or 1.0
            currency.rate_inverse = 1 / currency_rates.get(currency.id) or 1.0


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    # na currency rate opcija tipa tečaja za dohvat

    rate_inverse = fields.Float(
        string="Inverse rate",
        digits=(16, 6), default=1.0,
        help='The rate of the currency of rate 1 to the currency'
    )
    rate = fields.Float(digits=(16, 8), default=1.0,
                        help='The rate of the currency to the currency of rate 1')

    # redefinition of the constraint inherited from res.currency.rate and
    # wich adds a rate_type option so we can maintain multiple rates for one day
    _sql_constraints = [
        ('unique_name_per_day',
         'unique (name, currency_id, company_id, provider_id)',
         'Only one currency rate per provider and day allowed!'),
    ]

    def _calc_inverse_rate(self, vals):
        if vals.get('rate') and not vals.get('rate_inverse'):
            vals['rate_inverse'] = 1 / vals['rate']
        if not vals.get('rate') and vals.get('rate_inverse'):
            vals['rate'] = 1 / vals['rate_inverse']
        return vals

    @api.model
    def create(self, vals):
        vals = self._calc_inverse_rate(vals)
        return super(ResCurrencyRate, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self._calc_inverse_rate(vals)
        return super(ResCurrencyRate, self).write(vals)

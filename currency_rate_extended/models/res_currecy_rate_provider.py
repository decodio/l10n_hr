# Copyright 2020 Decodio Applications d.o.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import logging
from sys import exc_info
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


_logger = logging.getLogger(__name__)


class ResCurrencyRateProvider(models.Model):
    _inherit = 'res.currency.rate.provider'

    service = fields.Selection(
        selection_add=[('manual', 'Manual entry')],
    )

    fetch_inverse = fields.Boolean(
        string="Provides inverse rate")
    provide_rates = fields.Selection(
        selection=[
            ('one', 'One rate'),
            ('multi', 'Multiple rates')
        ], string="Providing rates", default='one',
        help="Single rate is default, but some providers use"
             " multiple rates ( buy, mid, sell)"
    )
    rate_type = fields.Selection(
        selection=[
            ('std', 'Standard rate'),
            ('buy', 'Buy rate'),
            ('mid', 'Mid rate'),
            ('sell', 'Sell rate'),
            ('manual', 'Manual Entry')
        ], string="Rate type", default='std'
    )

    cron_id = fields.Many2one(
        comodel_name='ir.cron',
        string="Cron update service",
    )

    # Modify res_currency_update original constrain for multiple rates support
    _sql_constraints = [
       (
           'service_company_id_uniq',
           'UNIQUE(service, rate_type, company_id)',
           'Service can only be used in one provider per company!'
       ),
    ]

    @api.multi
    @api.depends('provider_id', 'rate_type')
    def name_get(self):
        res = []
        for provider in self:
            name = provider.name
            if provider.rate_type not in ('std', 'manual'):
                name += ' - ' + provider.rate_type
            res.append((provider.id, name))
        return res

    @api.multi
    def onchange_service(self):
        """
        Inherit in other modules and modify some values depending on service
        - inverse currency rate, providing rates value etc...
        """
        return True

    @api.multi
    def _update(self, date_from, date_to, newest_only=False):
        # override original currency_rate_update method
        # in order to enable provider id based search and update
        Currency = self.env['res.currency']
        CurrencyRate = self.env['res.currency.rate']
        is_scheduled = self.env.context.get('scheduled')
        for provider in self:
            try:
                data = provider._obtain_rates(
                    provider.company_id.currency_id.name,
                    provider.currency_ids.mapped('name'),
                    date_from,
                    date_to
                ).items()
            except:
                e = exc_info()[1]
                _logger.warning(
                    'Currency Rate Provider "%s" failed to obtain data since'
                    ' %s until %s' % (
                        provider.name,
                        date_from,
                        date_to,
                    ),
                    exc_info=True,
                )
                provider.message_post(
                    subject=_('Currency Rate Provider Failure'),
                    body=_(
                        'Currency Rate Provider "%s" failed to obtain data'
                        ' since %s until %s:\n%s'
                    ) % (
                        provider.name,
                        date_from,
                        date_to,
                        str(e) if e else _('N/A'),
                    ),
                )
                continue

            if not data:
                if is_scheduled:
                    provider._schedule_next_run()
                continue
            if newest_only:
                data = [max(
                    data,
                    key=lambda x: fields.Date.from_string(x[0])
                )]

            for content_date, rates in data:
                timestamp = fields.Date.from_string(content_date)
                for currency_name, rate in rates.items():
                    if currency_name == provider.company_id.currency_id.name:
                        continue

                    currency = Currency.search([
                        ('name', '=', currency_name),
                    ], limit=1)
                    if not currency:
                        raise UserError(
                            _(
                                'Unknown currency from %(provider)s: %(rate)s'
                            ) % {
                                'provider': provider.name,
                                'rate': rate,
                            }
                        )
                    rate = provider._process_rate(
                        currency,
                        rate
                    )

                    record = CurrencyRate.search([
                        ('company_id', '=', provider.company_id.id),
                        ('currency_id', '=', currency.id),
                        ('provider_id', '=', provider.id),  # missing
                        ('name', '=', timestamp),
                    ], limit=1)
                    if record:
                        if float_compare(
                                record.rate, rate, precision_digits=6) != 0:
                            msg = "Updating %s-%s %s on %s: %s -> %s" % (
                                provider.name, provider.rate_type,
                                currency.name, fields.Date.to_string(timestamp),
                                record.rate, rate)
                            _logger.info(msg)
                            record.write({
                                'rate': rate,
                                'provider_id': provider.id,
                            })
                    else:
                        record = CurrencyRate.create({
                            'company_id': provider.company_id.id,
                            'currency_id': currency.id,
                            'name': timestamp,
                            'rate': rate,
                            'provider_id': provider.id,
                            'rate_type': provider.rate_type,
                        })

            if is_scheduled:
                provider._schedule_next_run()

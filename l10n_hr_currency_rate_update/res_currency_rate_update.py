# -*- encoding: utf-8 -*-
##############################################################################
#
#    Slobodni programi d.o.o.
#    Copyright (C) 2012- Slobodni programi (<http://www.slobodni-programi.hr>).
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsability of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs
#    End users who are looking for a ready-to-use solution with commercial
#    garantees and support are strongly adviced to contract a Free Software
#    Service Company
#
#    This program is Free Software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# TODO "nice to have" : restain the list of currencies that can be added for
# a webservice to the list of currencies supported by the Webservice
# TODO : implement max_delta_days for Yahoo webservice

#import string
#import logging
import time
#from mx import DateTime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#from lxml import etree
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.base_base.res.res_currency_rate_update import Currency_getter_factory, Currency_getter_interface
import requests
import json
# , UnknownClassError


class res_currency_rate_update_service(orm.Model):
    """Class that tells for which services which currencies have to be updated"""
    _inherit = "res.currency.rate.update.service"

    def _get_curr_services(self, cr, uid, context=None):
        res = super(res_currency_rate_update_service, self)._get_curr_services(cr, uid, context=context)
        return res + [('HNB_getter', u'Hrvatska Narodna Banka'),
                      ('ZABA_getter', u'Zagrebacka Banka'),
                      ('hr_RBA_getter', u'Raiffeisen Bank'),
                      ('hr_SB_getter', u'Splitska banka'), ]
    _columns = {
        'service': fields.selection(_get_curr_services, string='Webservice to use', required=True),
    }


class HNB_getter(Currency_getter_interface):  # class added according to Croatian needs
    """Implementation of Currency_getter_factory interface for HNB service"""

    def get_available_currencies(self):
        """implementation of abstract method of Currency_getter_interface"""
        currencies = []
        date_start = datetime.now()
        counter = 0
        found = False
        while counter < 20 and not found:
            tmp_date = date_start - relativedelta(days= +counter)
            url = 'http://www.hnb.hr/tecajn/%s' % (tmp_date.strftime('f%d%m%y.dat'))  # %s is supposed to be f040412.dat in format 'f%d%m%Y.dat'
            raw_file = self.get_url(url)
            if '<html>' in raw_file:
                counter += 1
                continue
            found = True
            raw_file = raw_file.strip()
            lines = raw_file.split("\r\n")
            for line in lines[1:]:
                vals = line.strip().split()
                currencies.append(vals[0][3:6].upper())
            return currencies
        return False

    def get_currency_for_period(self, currency_array, main_currency, max_delta_days,
                                date_start, date_end, currency_type_array=None):
        """implementation of abstract method of Currency_getter_interface"""
        if currency_type_array is None:
            currency_type_array = []

        self.updated_currency = {'data': {}, 'log_message': '', 'exception': {}}

        # This is the default currency of the service ('HRK' in Croatia, this is croatian service)
        service_currency = u'HRK'
        current_time = datetime.now()
        if date_start is None or date_start > datetime.now():
            date_start = current_time - timedelta(days=7)
        if date_end is None or date_end > datetime.now():
            date_end = current_time

        date_diff = (date_end - date_start).days + 1
        for single_date in [d for d in (date_start + relativedelta(days= +n) for n in range(date_diff)) if d <= date_end]:
            rate_name = single_date.strftime("%Y-%m-%d")
            url = 'http://www.hnb.hr/tecajn/%s' % (single_date.strftime('f%d%m%y.dat'))  # %s is supposed to be f040412.dat in format 'f%d%m%Y.dat'
            data = {}
            # every currency to upper letters, just in case
            # currency_array = map(lambda x: x.upper(), currency_array) - ALREADY DONE IN CALLING METHOD

            self.logger.debug(_("HNB currency rate service : connecting..."))
            raw_file = self.get_url(url)
            if '<html>' in raw_file:
                msg = _("Could not locate data for date '%(data)s' from url '%(url)s'") % {'data':rate_name, 'url':url, }
                self.updated_currency['log_message'] += msg + '\n'
                self.logger.error(msg)
                continue
            raw_file = raw_file.replace(',', '.').strip()
            lines = raw_file.split("\r\n")
            if len(lines[0]) < 10:
                # trim the first line sometimes we get 325 sometimes 2ed pattern unknown
                lines = lines[1:]
            # header
            line = lines[0]
            rate_date_datetime = datetime.strptime(line[11:19], '%d%m%Y')
            # If start and end date are the same, it means we called this method from method for only one date, we should check if it is allowed
            # if date_diff == 1:
            #    retval = self.check_rate_date(rate_date_datetime, max_delta_days)
            #    if retval:
            #        return retval
            self.logger.debug(_("HNB sent a valid text file"))
            self.logger.debug(_("Supported currencies = ") + str(self.supported_currency_array))

            # create dict from currency lines
            # LINE FORMAT: code(3)name(3)numOfUnits(3)    bid(8,6)    middle(8,6)    ask(8,6)
            # 036AUD001       6,239750       6,258526       6,277302
            # code = 036
            # name = AUD
            # num_of_units = 001
            # buy = 6,239750
            # middle = 6,258526
            # sell = 6,277302

            # Usually there are these three types of currency
            # kupovni - bid_rate, prodajni - ask_rate
            # types_of_value = ['ask_value','middle_value','bid_value']

            for line in lines[1:]:
                if len(line.strip()) < 10:
                    # last line is 0
                    continue
                vals = line.strip().split()
                if vals[0][3:6].upper() in currency_array:
                    tmp_dict = {
                        'ratio': float(vals[0][6:9]),
                        'middle_rate': float(vals[2]),
                    }
                    if 'bid_rate' in currency_type_array:
                        tmp_dict['bid_rate'] = float(vals[1])
                    if 'ask_rate' in currency_type_array:
                        tmp_dict['ask_rate'] = float(vals[3])
                    data[vals[0][3:6].upper()] = tmp_dict

            self.validate_cur(main_currency)
            # Check if HNB supports all of expected currencies
            curr_error_list = [curr for curr in currency_array if curr not in data and curr not in [service_currency, main_currency]]
            if curr_error_list:
                warning = _('Your tried to update %s %s which are not available from the current service !!!' \
                '\nPlease remove those currencies from the service update list and refresh currencies again.') % \
                ('currency' if len(curr_error_list) == 1 else 'currencies', ','.join(curr_error_list))
                self.updated_currency['log_message'] += warning + '\n'
                self.logger.error(warning)
                # return {'exception': {'title': _('Currency update error'), 'message': warning,} }
            if curr_error_list:
                currency_array = [x for x in currency_array if x not in curr_error_list]
            to_remove = set(data) - set(currency_array)
            for key in to_remove:
                del data[key]

            # if HRK is NOT main currency we have to add it because it is not in the data by default
            if main_currency != service_currency:
                # 1 MAIN_CURRENCY = main_rate HRK
                main_rate_middle = data[main_currency]['middle_rate'] / data[main_currency]['ratio']
                if 'bid_rate' in currency_type_array:
                    main_rate_bid = data[main_currency]['bid_rate'] / data[main_currency]['ratio']
                if 'ask_rate' in currency_type_array:
                    main_rate_ask = data[main_currency]['ask_rate'] / data[main_currency]['ratio']

                data[service_currency] = {
                    'ratio': 1,
                    'middle_rate': main_rate_middle,
                }
                if 'bid_rate' in currency_type_array:
                    data[service_currency]['bid_rate'] = main_rate_bid
                if 'ask_rate' in currency_type_array:
                    data[service_currency]['ask_rate'] = main_rate_ask

            data[main_currency] = {
                'ratio': 1,
                'middle_rate': 1.,
            }
            if 'bid_rate' in currency_type_array:
                data[main_currency]['bid_rate'] = 1.
            if 'ask_rate' in currency_type_array:
                data[main_currency]['ask_rate'] = 1.

            for curr in currency_array:
                if curr == main_currency or curr == service_currency:
                    continue

                curr_data = data[curr]
                self.validate_cur(curr)

                if main_currency == service_currency:
                    middle_rate = curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        bid_rate = curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': bid_rate})
                    if 'ask_rate' in currency_type_array:
                        ask_rate = curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': ask_rate})
                else:
                    middle_rate = main_rate_middle * curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        middle_rate_bid = main_rate_bid * curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': middle_rate_bid})
                    if 'ask_rate' in currency_type_array:
                        middle_rate_ask = main_rate_ask * curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': middle_rate_ask})
                    curr_data['ratio'] = 1  # as in 1 EUR = 285 HUF, shown as main_rate = EUR, ratio = 1, rate = 285

                log_msg = _("Middle rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['middle_rate']) + ' ' + curr
                if 'bid_rate' in currency_type_array:
                    log_msg += _("\nBid rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['bid_rate']) + ' ' + curr
                if 'ask_rate' in currency_type_array:
                    log_msg += _("\nAsk rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['ask_rate']) + ' ' + curr

                self.logger.debug(log_msg)
            self.updated_currency['data'][rate_name] = data
        return self.updated_currency


class ZABA_getter(Currency_getter_interface):  # class added according to Croatian needs
    """Implementation of Currency_getter_factory interface for ZABA service(ajax POST)"""

    def get_available_currencies(self):
        """implementation of abstract method of Currency_getter_interface"""
        currencies = []
        date_start = datetime.now()
        counter = 0
        found = False
        while counter < 20 and not found:
            tmp_date = date_start - relativedelta(days= +counter)
            date = tmp_date.strftime('%d/%m/%Y')
            url = 'http://www.zaba.hr/ZabaUtilsWeb/utils/tecaj/tecajna'
            headers = {'Content-Type': 'application/json',
                       }
            payload = {"datumTecajne": date,
                       "brojTecajne": "",
                       "godinaTecajne": "",
                       }
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code != requests.codes.ok:
                counter += 1
                continue

            found = True
            resp_data = json.loads(response.content)
            for line in resp_data['lista']['tecajevi']:
                if line['tecajSrednji']:
                    currencies.append(line['oznakaDevAlpha'].upper())
            return currencies

        return False

    def get_currency_for_period(self, currency_array, main_currency, max_delta_days,
                                date_start, date_end, currency_type_array=None):
        """implementation of abstract method of Currency_getter_interface"""
        if currency_type_array is None:
            currency_type_array = []

        self.updated_currency = {'data': {}, 'log_message': '', 'exception': {}}

        # This is the default currency of the service ('HRK' in Croatia, this is croatian service)
        service_currency = u'HRK'

        if date_start is None or date_start > datetime.now():
            date_start = datetime.now() - timedelta(days=1)
        if date_end is None or date_end > datetime.now():
            date_end = datetime.now() - timedelta(days=7)

        date_diff = (date_end - date_start).days + 1
        for single_date in [d for d in (date_start + relativedelta(days= +n) for n in range(date_diff)) if d <= date_end]:
            datas = {}
            rate_name = single_date.strftime("%Y-%m-%d")
            date = single_date.strftime('%d/%m/%Y')
            # url = 'http://www.zaba.hr/ZabaUtilsWeb/utils/tecaj/tecajna' url changed 26.02.2019
            url = "https://www.zaba.hr/home/tecajna-filter"
            headers = {'Content-Type': 'application/json',
                       }
            """ payload changed 26.02.2019
            payload = {"datumTecajne": date,
                       "brojTecajne": "",
                       "godinaTecajne": "",
                       }
            """
            payload = {
                ' self.logger.error(msg)g': str(single_date.year),
                'm': str(single_date.month),
                'd': str(single_date.day),
            }
            response = requests.get(url, params=json.dumps(payload), headers=headers) # request changed from post to get and data with params
            resp_data = json.loads(response.content)
            try:
                resp_data = resp_data['obj']
            except Exception, e:
                msg = _(
                    "Invalide response for date '%(data)s' from url '%(url)s'") % {
                          'data': rate_name, 'url': url, }
                self.logger.error(msg)
                continue
            # resp_data example:
            """
            {u'lista': {u'brojTecajneListe': 21,
                        u'brojTecajneListeS': u'21',
                        u'datumTecajne': u'2016-02-02',
                        u'datumTecajneString': u'02.02.2016 00:00:00',
                        u'dccTecajevi': None,
                        u'godinaTecajneListe': 2016,
                        u'godinaTecajneListeS': None,
                        u'oznakaBurze': u'001',
                        u'tecajevi': [{u'brDecMj': 0,
                                       u'broj_liste': u'001',
                                       u'dozvoljenoTrgovanje': True,
                                       u'drzave_ENG': [],
                                       u'drzave_HRV': [],
                                       u'ozn_drzave': [],
                                       u'oznakaDevAlpha': u'AUD',
                                       u'oznakaDevNum': u'036',
                                       u'paritet': u'1',
                                       u'tecajKupDev': 4.875018,
                                       u'tecajKupDevS': u'4,875018',
                                       u'tecajKupEfe': 4.801892,
                                       u'tecajKupEfeS': u'4,801892',
                                       u'tecajProdDev': 5.094393,
                                       u'tecajProdDevS': u'5,094393',
                                       u'tecajProdEfe': 5.138025,
                                       u'tecajProdEfeS': u'5,138025',
                                       u'tecajSrednji': 4.983777,
                                       u'tecajSrednjiS': u'4,983777',
                                       u'vaziDo': None,
                                       u'vaziOd': u'2016-02-02'},
                                     ]},
            u'poruka': None,
            u'postojiPDF': True,
            u'postojiPRN': True,
            u'status': u'true'}
            """

            self.logger.debug(_("ZABA currency rate service : connecting..."))

            if (response.status_code != requests.codes.ok) or (rate_name != resp_data['lista']['datumTecajne']):
                msg = _("Could not locate data for date '%(data)s' from url '%(url)s'") % {'data':rate_name, 'url':url, }
                self.updated_currency['log_message'] += msg + '\n'
                self.logger.error(msg)
                continue

            self.logger.debug(_("ZABA sent a valid response"))
            self.logger.debug(_("Supported currencies = ") + str(self.supported_currency_array))

            for line in resp_data['lista']['tecajevi']:
                if line['oznakaDevAlpha'].upper() in currency_array:
                    tmp_dict = {
                        'ratio': float(line['paritet']),
                        'middle_rate': float(line['tecajSrednji']),
                    }
                    if 'bid_rate' in currency_type_array:
                        tmp_dict['bid_rate'] = float(line['tecajKupDev'])
                    if 'ask_rate' in currency_type_array:
                        tmp_dict['ask_rate'] = float(line['tecajProdDev'])
                    datas[line['oznakaDevAlpha'].upper()] = tmp_dict

            self.validate_cur(main_currency)

            curr_error_list = [curr for curr in currency_array if curr not in datas and curr not in [service_currency, main_currency]]
            if curr_error_list:
                warning = _('Your tried to update %s %s which are not available from the current service !!!' \
                '\nPlease remove those currencies from the service update list and refresh currencies again.') % \
                ('currency' if len(curr_error_list) == 1 else 'currencies', ','.join(curr_error_list))
                self.updated_currency['log_message'] += warning + '\n'
                self.logger.error(warning)

            if curr_error_list:
                currency_array = [x for x in currency_array if x not in curr_error_list]
            to_remove = set(datas) - set(currency_array)
            for key in to_remove:
                del datas[key]

            # if HRK is NOT main currency we have to add it because it is not in the datas by default
            if main_currency != service_currency:
                # 1 MAIN_CURRENCY = main_rate HRK
                main_rate_middle = datas[main_currency]['middle_rate'] / datas[main_currency]['ratio']
                if 'bid_rate' in currency_type_array:
                    main_rate_bid = datas[main_currency]['bid_rate'] / datas[main_currency]['ratio']
                if 'ask_rate' in currency_type_array:
                    main_rate_ask = datas[main_currency]['ask_rate'] / datas[main_currency]['ratio']

                datas[service_currency] = {
                    'ratio': 1,
                    'middle_rate': main_rate_middle,
                }
                if 'bid_rate' in currency_type_array:
                    datas[service_currency]['bid_rate'] = main_rate_bid
                if 'ask_rate' in currency_type_array:
                    datas[service_currency]['ask_rate'] = main_rate_ask

            datas[main_currency] = {
                'ratio': 1,
                'middle_rate': 1.,
            }
            if 'bid_rate' in currency_type_array:
                datas[main_currency]['bid_rate'] = 1.
            if 'ask_rate' in currency_type_array:
                datas[main_currency]['ask_rate'] = 1.

            for curr in currency_array:
                if curr == main_currency or curr == service_currency:
                    continue

                curr_data = datas[curr]
                self.validate_cur(curr)

                if main_currency == service_currency:
                    middle_rate = curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        bid_rate = curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': bid_rate})
                    if 'ask_rate' in currency_type_array:
                        ask_rate = curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': ask_rate})
                else:
                    middle_rate = main_rate_middle * curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        middle_rate_bid = main_rate_bid * curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': middle_rate_bid})
                    if 'ask_rate' in currency_type_array:
                        middle_rate_ask = main_rate_ask * curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': middle_rate_ask})
                    curr_data['ratio'] = 1  # as in 1 EUR = 285 HUF, shown as main_rate = EUR, ratio = 1, rate = 285

                log_msg = _("Middle rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['middle_rate']) + ' ' + curr
                if 'bid_rate' in currency_type_array:
                    log_msg += _("\nBid rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['bid_rate']) + ' ' + curr
                if 'ask_rate' in currency_type_array:
                    log_msg += _("\nAsk rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['ask_rate']) + ' ' + curr

                self.logger.debug(log_msg)

            self.updated_currency['data'][rate_name] = datas
        return self.updated_currency


class hr_RBA_getter(Currency_getter_interface) :  # class added according to Croatian needs = based on class Admin_ch_getter
    """Implementation of Currency_getter_factory interface for RBA service"""

    #@classmethod
    def get_available_currencies(self):
        """implementation of abstract method of Currency_getter_interface"""
        currencies = []
        date_start = datetime.now()
        counter = 0
        found = False
        while counter < 20 and not found:
            tmp_date = date_start + relativedelta(days= +counter)
            url = "http://www.rba.hr/my/bank/redir.jsp?src=/my/bank/rates/rates_exchange.jsp&language=HR&datum=%(datum_tecaja)s&formatTL=ASCII&subref=8" % {'datum_tecaja': tmp_date.strftime("%d.%m.%Y")}
            rawfile = self.get_url(url)
            if 'Nema podataka !' in rawfile:
                counter += 1
                continue
            found = True
            rawfile = rawfile.strip()
            lines = rawfile.split("\n")
            for line in lines[1:]:
                vals = line.strip().split()
                currencies.append(vals[0][0:3].upper())
            return currencies
        return False

    def get_currency_for_period(self, currency_array, main_currency, max_delta_days, date_start, date_end, currency_type_array=None):
        """implementation of abstract method of Currency_getter_interface"""
        if currency_type_array is None:
            currency_type_array = []

        self.updated_currency = {'data': {}, 'log_message': '', 'exception': {}}

        # This is the default currency of the service ('HRK' in Croatia, this is croatian service)
        service_currency = u'HRK'

        if date_start is None or date_start > datetime.now():
            date_start = datetime.now()
        if date_end is None or date_end > datetime.now():
            date_end = datetime.now()

        date_diff = (date_end - date_start).days + 1
        for single_date in [d for d in (date_start + relativedelta(days= +n) for n in range(date_diff)) if d <= date_end]:
            rate_name = single_date.strftime("%Y-%m-%d")

            url = "http://www.rba.hr/my/bank/redir.jsp?src=/my/bank/rates/rates_exchange.jsp&language=HR&datum=%(datum_tecaja)s&formatTL=ASCII&subref=8" % {'datum_tecaja': single_date.strftime("%d.%m.%Y")}
            data = {}

            # every currency to upper letters, just in case
            # currency_array = map(lambda x: x.upper(), currency_array) - ALREADY DONE IN CALLING METHOD

            self.logger.debug(_("RBA currency rate service : connecting..."))
            rawfile = self.get_url(url)
            if 'Nema podataka !' in rawfile:
                msg = _("Could not locate data for date '%(data)s' from url '%(url)s'") % {'data':rate_name, 'url':url, }
                self.updated_currency['log_message'] += msg + '\n'
                self.logger.error(msg)
                continue
            rawfile = rawfile.replace(',', '.').strip()
            lines = rawfile.split("\n")
            # header
            line = lines[0]
            rate_date_datetime = datetime.strptime(line[11:19], '%d%m%Y')
            # If start and end date are the same, it means we called this method from method for only one date, we should check if it is allowed
            # if date_diff == 1:
            #    retval = self.check_rate_date(rate_date_datetime, max_delta_days)
            #    if retval:
            #        return retval
            self.logger.debug(_("RBA sent a valid text file"))
            self.logger.debug(_("Supported currencies = ") + str(self.supported_currency_array))

            # create dict from currency lines
            # LINE FORMAT: code(3)name(3)numOfUnits(3)    bid(8,6)    middle(8,6)    ask(8,6)
            # AUD036001       6,239750       6,258526       6,277302
            # code = 036
            # name = AUD
            # num_of_units = 001
            # buy = 6,239750
            # middle = 6,258526
            # sell = 6,277302

            # Usually there are these three types of currency
            # kupovni - bid_rate, prodajni - ask_rate
            # types_of_value = ['ask_value','middle_value','bid_value']

            for line in lines[1:]:
                vals = line.strip().split()
                if vals[0][0:3].upper() in currency_array:
                    tmp_dict = {
                        'ratio': float(vals[0][6:9]),
                        'middle_rate': float(vals[2]),
                    }
                    if 'bid_rate' in currency_type_array:
                        tmp_dict['bid_rate'] = float(vals[1])
                    if 'ask_rate' in currency_type_array:
                        tmp_dict['ask_rate'] = float(vals[3])
                    data[vals[0][0:3].upper()] = tmp_dict

            self.validate_cur(main_currency)
            # Check if RBA supports all of expected currencies
            curr_error_list = [curr for curr in currency_array if curr not in data and curr not in [service_currency, main_currency]]
            if curr_error_list:
                warning = _('Your tried to update %s %s which are not available from the current service !!!' \
                '\nPlease remove those currencies from the service update list and refresh currencies again.') % \
                ('currency' if len(curr_error_list) == 1 else 'currencies', ','.join(curr_error_list))
                self.updated_currency['log_message'] += warning + '\n'
                self.logger.error(warning)
                # return {'exception': {'title': _('Currency update error'), 'message': warning,} }
            if curr_error_list:
                currency_array = [x for x in currency_array if x not in curr_error_list]
            to_remove = set(data) - set(currency_array)
            for key in to_remove:
                del data[key]

            # if HRK is NOT main currency we have to add it because it is not in the data by default
            if main_currency != service_currency:
                # 1 MAIN_CURRENCY = main_rate HRK
                main_rate_middle = data[main_currency]['middle_rate'] / data[main_currency]['ratio']
                if 'bid_rate' in currency_type_array:
                    main_rate_bid = data[main_currency]['bid_rate'] / data[main_currency]['ratio']
                if 'ask_rate' in currency_type_array:
                    main_rate_ask = data[main_currency]['ask_rate'] / data[main_currency]['ratio']

                data[service_currency] = {
                    'ratio': 1,
                    'middle_rate':  main_rate_middle,
                }
                if 'bid_rate' in currency_type_array:
                    data[service_currency]['bid_rate'] = main_rate_bid
                if 'ask_rate' in currency_type_array:
                    data[service_currency]['ask_rate'] = main_rate_ask

            data[main_currency] = {
                'ratio': 1,
                'middle_rate': 1.,
            }
            if 'bid_rate' in currency_type_array:
                data[main_currency]['bid_rate'] = 1.
            if 'ask_rate' in currency_type_array:
                data[main_currency]['ask_rate'] = 1.

            for curr in currency_array:
                if curr == main_currency or curr == service_currency:
                    continue

                curr_data = data[curr]
                self.validate_cur(curr)

                if main_currency == service_currency:
                    middle_rate = curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        bid_rate = curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': bid_rate})
                    if 'ask_rate' in currency_type_array:
                        ask_rate = curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': ask_rate})
                else:
                    middle_rate = main_rate_middle * curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        middle_rate_bid = main_rate_bid * curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': middle_rate_bid})
                    if 'ask_rate' in currency_type_array:
                        middle_rate_ask = main_rate_ask * curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': middle_rate_ask})
                    curr_data['ratio'] = 1  # as in 1 EUR = 285 HUF, shown as main_rate = EUR, ratio = 1, rate = 285

                log_msg = _("Middle rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['middle_rate']) + ' ' + curr
                if 'bid_rate' in currency_type_array:
                    log_msg += _("\nBid rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['bid_rate']) + ' ' + curr
                if 'ask_rate' in currency_type_array:
                    log_msg += _("\nAsk rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['ask_rate']) + ' ' + curr

                self.logger.debug(log_msg)
            self.updated_currency['data'][rate_name] = data
        return self.updated_currency


class hr_SB_getter(Currency_getter_interface) :  # class added according to Croatian needs = based on class Admin_ch_getter
    """Implementation of Currency_getter_factory interface for SB service"""
    def get_available_currencies(self):
        """implementation of abstract method of Currency_getter_interface"""
        from lxml.html import parse

        currencies = []
        date_start = datetime.now()
        counter = 0
        found = False
        while counter < 20 and not found:
            tmp_date = date_start + relativedelta(days= +counter)
            url = "http://www.splitskabanka.hr/tecajna-lista/arhiva?lista=%(datum_tecaja)s" % {'datum_tecaja': tmp_date.strftime("%Y%m%d")}
            doc = parse(url).getroot()
            table = doc.xpath('//table[@class="mainTable eRateAll"]')
            if table:
                table = table[0]
            else:
                msg = _("Could not locate data for date '%(data)s' from url '%(url)s'") % {'data':tmp_date.strftime("%Y-%m-%d"), 'url':url, }
                self.logger.error(msg)
                counter += 1
                continue
            found = True
            for tr in table:
                if tr[0].tag == 'td':
                    currencies.append(tr[1].text_content())
            return currencies
        return False

    def get_currency_for_period(self, currency_array, main_currency, max_delta_days, date_start, date_end, currency_type_array=None):
        """implementation of abstract method of Currency_getter_interface"""
        if currency_type_array is None:
            currency_type_array = []

        self.updated_currency = {'data': {}, 'log_message': '', 'exception': {}}

        # This is the default currency of the service ('HRK' in Croatia, this is croatian service)
        service_currency = u'HRK'

        if date_start is None or date_start > datetime.now():
            date_start = datetime.now()
        if date_end is None or date_end > datetime.now():
            date_end = datetime.now()

        # import lxml.html as ht
        from lxml.html import parse

        date_diff = (date_end - date_start).days + 1
        for single_date in [d for d in (date_start + relativedelta(days= +n) for n in range(date_diff)) if d <= date_end]:
            rate_name = single_date.strftime("%Y-%m-%d")

            url = "http://www.splitskabanka.hr/tecajna-lista/arhiva?lista=%(datum_tecaja)s" % {'datum_tecaja': single_date.strftime("%Y%m%d")}
            data = {}

            # every currency to upper letters, just in case
            # currency_array = map(lambda x: x.upper(), currency_array) - ALREADY DONE IN CALLING METHOD

            self.logger.debug(_("SB currency rate service : connecting..."))
            doc = parse(url).getroot()
            table = doc.xpath('//table[@class="mainTable eRateAll"]')
            if table:
                table = table[0]
            else:
                msg = _("Could not locate data for date '%(data)s' from url '%(url)s'") % {'data':rate_name, 'url':url, }
                self.updated_currency['log_message'] += msg + '\n'
                self.logger.error(msg)
                continue

            tmp_date = doc.xpath('//div[@class="ExchangeRate LongER"]/p[@class="Description"]/strong/label')[1].text_content().replace('.', '')
            rate_date_datetime = datetime.strptime(tmp_date, '%d/%m/%Y')

            # If start and end date are the same, it means we called this method from method for only one date, we should check if it is allowed
            # if date_diff == 1:
            #    retval = self.check_rate_date(rate_date_datetime, max_delta_days)
            #    if retval:
            #        return retval
            self.logger.debug(_("SB sent a valid text file"))
            self.logger.debug(_("Supported currencies = ") + str(self.supported_currency_array))

            # create dict from currency lines
            # 1. Valuta
            # 2. Jed.
            # 3. Kupovni za devize
            # 4. Srednji
            # 5. Prodajni za devize
            for tr in table:
                if tr[0].tag == 'td':
                    bid_rate = tr[4].text_content().strip().replace(',', '.').replace('-', '') or '0.0'
                    ask_rate = tr[6].text_content().strip().replace(',', '.').replace('-', '') or '0.0'
                    middle_rate = tr[5].text_content().strip().replace(',', '.').replace('-', '') or ask_rate or bid_rate
                    tmp_dict = {
                        'ratio': float(tr[2].text_content()),
                        'middle_rate': float(middle_rate),
                    }
                    if 'bid_rate' in currency_type_array:
                        tmp_dict['bid_rate'] = float(bid_rate)
                    if 'ask_rate' in currency_type_array:
                        tmp_dict['ask_rate'] = float(ask_rate)
                    data[tr[1].text_content()] = tmp_dict

            # Usually there are these three types of currency
            # kupovni - bid_rate, prodajni - ask_rate
            # types_of_value = ['ask_value','middle_value','bid_value']
            self.validate_cur(main_currency)
            # Check if HNB supports all of expected currencies
            curr_error_list = [curr for curr in currency_array if curr not in data and curr not in [service_currency, main_currency]]
            if curr_error_list:
                warning = _('Your tried to update %s %s which are not available from the current service !!!' \
                '\nPlease remove those currencies from the service update list and refresh currencies again.') % \
                ('currency' if len(curr_error_list) == 1 else 'currencies', ','.join(curr_error_list))
                self.updated_currency['log_message'] += warning + '\n'
                self.logger.error(warning)
                # return {'exception': {'title': _('Currency update error'), 'message': warning,} }
            if curr_error_list:
                currency_array = [x for x in currency_array if x not in curr_error_list]
            to_remove = set(data) - set(currency_array)
            for key in to_remove:
                del data[key]
            # if HRK is NOT main currency we have to add it because it is not in the data by default
            if main_currency != service_currency:
                # 1 MAIN_CURRENCY = main_rate HRK
                main_rate_middle = data[main_currency]['middle_rate'] / data[main_currency]['ratio']
                if 'bid_rate' in currency_type_array:
                    main_rate_bid = data[main_currency]['bid_rate'] / data[main_currency]['ratio']
                if 'ask_rate' in currency_type_array:
                    main_rate_ask = data[main_currency]['ask_rate'] / data[main_currency]['ratio']

                data[service_currency] = {
                    'ratio': 1,
                    'middle_rate': main_rate_middle,
                }
                if 'bid_rate' in currency_type_array:
                    data[service_currency]['bid_rate'] = main_rate_bid
                if 'ask_rate' in currency_type_array:
                    data[service_currency]['ask_rate'] = main_rate_ask

            data[main_currency] = {
                'ratio': 1,
                'middle_rate': 1.,
            }
            if 'bid_rate' in currency_type_array:
                data[main_currency]['bid_rate'] = 1.
            if 'ask_rate' in currency_type_array:
                data[main_currency]['ask_rate'] = 1.

            for curr in currency_array:
                if curr == main_currency or curr == service_currency:
                    continue
                curr_data = data[curr]
                self.validate_cur(curr)
                if main_currency == service_currency:
                    middle_rate = curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        bid_rate = curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': bid_rate})
                    if 'ask_rate' in currency_type_array:
                        ask_rate = curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': ask_rate})
                else:
                    middle_rate = main_rate_middle * curr_data['ratio'] / curr_data['middle_rate']
                    curr_data.update({'middle_rate': middle_rate})
                    if 'bid_rate' in currency_type_array:
                        middle_rate_bid = main_rate_bid * curr_data['ratio'] / curr_data['bid_rate']
                        curr_data.update({'bid_rate': middle_rate_bid})
                    if 'ask_rate' in currency_type_array:
                        middle_rate_ask = main_rate_ask * curr_data['ratio'] / curr_data['ask_rate']
                        curr_data.update({'ask_rate': middle_rate_ask})
                    curr_data['ratio'] = 1  # as in 1 EUR = 285 HUF, shown as main_rate = EUR, ratio = 1, rate = 285

                log_msg = _("Middle rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['middle_rate']) + ' ' + curr
                if 'bid_rate' in currency_type_array:
                    log_msg += _("\nBid rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['bid_rate']) + ' ' + curr
                if 'ask_rate' in currency_type_array:
                    log_msg += _("\nAsk rate retrieved : 1 ") + main_currency + ' = ' + str(curr_data['ask_rate']) + ' ' + curr

                self.logger.debug(log_msg)
            self.updated_currency['data'][rate_name] = data
        return self.updated_currency

Currency_getter_factory._services['HNB_getter'] = eval('HNB_getter')
Currency_getter_factory._services['ZABA_getter'] = eval('ZABA_getter')
Currency_getter_factory._services['RBA_getter'] = eval('hr_RBA_getter')
Currency_getter_factory._services['SB_getter'] = eval('hr_SB_getter')

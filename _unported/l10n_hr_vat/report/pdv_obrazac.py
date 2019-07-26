# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Author: 
#    mail:   
#    Copyright: 
#    Contributions: 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from datetime import datetime


class pdv_obrazac(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_ids = []
        period_obj = self.pool.get('account.period')
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)
        company_id = self.pool.get('account.tax.code').browse(self.cr, self.uid,
                                   data['form']['chart_tax_id'][0]).company_id.id or False
        period_from = data['form'].get('period_from', False) and data['form'].get('period_from', False)[0]
        period_to = data['form'].get('period_to', False) and data['form'].get('period_to', False)[0]
        fiscal_year = data['form'].get('fiscalyear_id', False) and data['form'].get('fiscalyear_id', False)[0]

        if not period_from:
            where_clause = ""
            if fiscal_year:
                where_clause = " where fiscalyear_id = " + str(fiscal_year) + " AND company_id = " + company_id
            self.cr.execute("select id from account_period where date_start = (select min(date_start) from account_period " + where_clause + " )")
            period_from = self.cr.fetchone()[0]

        if not period_to:
            where_clause = ""
            if fiscal_year:
                where_clause = " where fiscalyear_id = " + str(fiscal_year) + " AND company_id = " + company_id
            self.cr.execute("select id from account_period where date_start = (select max(date_start) from account_period " + where_clause + " )")
            period_to = self.cr.fetchone()[0]

        self.period_ids = period_obj.build_ctx_periods(self.cr, self.uid, period_from, period_to)
        periods_l = period_obj.read(self.cr, self.uid, self.period_ids, ['name'])
        for period in periods_l:
            if res['periods'] == '':
                res['periods'] = period['name']
            else:
                res['periods'] += ", " + period['name']
        return super(pdv_obrazac, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(pdv_obrazac, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_company_name': self._get_company_name,
            'get_company_oib': self._get_company_oib,
            'get_company_nkd': self._get_company_nkd,
            'get_company_ispostava': self._get_company_ispostava,
            'get_value': self._get_value,
            'get_start_date': self._get_start_date,
            'get_end_date': self._get_end_date,
        })

    def _get_start_date(self):
        start_date = None
        if self.period_ids:
            for period in self.period_ids:
                period_date_start = self.pool.get('account.period').browse(self.cr, self.uid, period).date_start
                if start_date is None:
                    start_date = period_date_start
                if datetime.strptime(period_date_start, '%Y-%m-%d') < datetime.strptime(start_date, '%Y-%m-%d'):
                    start_date = period_date_start
            return start_date
        else:
            return False

    def _get_end_date(self):
        end_date = None
        if self.period_ids:
            for period in self.period_ids:
                period_date_stop = self.pool.get('account.period').browse(self.cr, self.uid, period).date_stop
                if end_date is None:
                    end_date = period_date_stop
                if datetime.strptime(period_date_stop, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                    end_date = period_date_stop
            return end_date
        else:
            return False

    def _get_company_name(self, data):
        atc_obj = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0])
        if isinstance(atc_obj, (list, tuple)):
            atc_obj = atc_obj[0]
        name = atc_obj.company_id.name or False
        return name

    def _get_company_oib(self, data):
        atc_obj = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0])
        if isinstance(atc_obj, (list, tuple)):
            atc_obj = atc_obj[0]
        name = atc_obj.company_id.partner_id.vat and \
            atc_obj.company_id.partner_id.vat[2:] or False
        return name

    def _get_company_nkd(self, data):
        atc_obj = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0])
        if isinstance(atc_obj, (list, tuple)):
            atc_obj = atc_obj[0]
        name = atc_obj.company_id.l10n_hr_base_nkd_id and \
               atc_obj.company_id.l10n_hr_base_nkd_id.code or False
        return name

    def _get_company_ispostava(self, data):
        chart_tax = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0])
        if isinstance(chart_tax, (list, tuple)):
            chart_tax = chart_tax[0]
        name = chart_tax.company_id.porezna_ispostava or False
        return name

    def _get_value(self, data, poz, rbr):
        value = 0.0
        value_sum = 0.0
        account_tax_code_obj = self.pool.get('account.tax.code')
        company_id = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0]).company_id.id or False

        if poz:
            poz_id = self.pool.get('l10n_hr_pdv.report.obrazac').search(self.cr, self.uid,
                                   [('position', '=', poz), ('company_id', '=', company_id),
                                    ('obrazac_id', '=', data['form']['obrazac_id'][0])])
            if poz_id:
                obrazac = self.pool.get('l10n_hr_pdv.report.obrazac').browse(self.cr, self.uid, poz_id[0])
                base_code_ids = obrazac.stavka_osnovice_ids
                tax_code_ids = obrazac.stavka_poreza_ids
                tax_code_2_ids = obrazac.stavka_nepriznati_porez_ids
            else:
                return value
        else:
            return value

        if rbr == 0:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), tax_code_2_ids)
        elif rbr == 1:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), base_code_ids)
        else:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), tax_code_ids)

        if len(self.period_ids) == 1:
            where_clause = 'and line.period_id = ' + str(self.period_ids[0]) + " and move.state <> 'draft' "
        else:
            where_clause = 'and line.period_id in ' + str(tuple(self.period_ids)) + " and move.state <> 'draft' "

        for line in current_tax_code_ids:
            value_tax = account_tax_code_obj._sum(self.cr, self.uid, [line[0]], self.name, {}, {},
                                                   where_clause)
            if value_tax:
                value = value_tax[line[0]]
            if line[1] == 0:
                value = 0
            else:
                value = value / line[1]
            value_sum += value

        return value_sum or 0.0

report_sxw.report_sxw('report.pdv.obrazac', 'account.tax.code',
    'addons/l10n_hr_vat/report/pdv_obrazac.rml', parser=pdv_obrazac, header=False)
report_sxw.report_sxw('report.pdv.obrazac.july.2013', 'account.tax.code',
    'addons/l10n_hr_vat/report/pdv_obrazac_july_2013.rml', parser=pdv_obrazac, header=False)
report_sxw.report_sxw('report.pdv.obrazac.january.2014', 'account.tax.code',
    'addons/l10n_hr_vat/report/pdv_obrazac_january_2014.rml', parser=pdv_obrazac, header=False)
report_sxw.report_sxw('report.pdv.obrazac.january.2015', 'account.tax.code',
    'addons/l10n_hr_vat/report/pdv_obrazac_january_2015.rml', parser=pdv_obrazac, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
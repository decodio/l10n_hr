# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp import pooler
from openerp.tools.translate import _
from openerp.report import report_sxw

class account_vat_settlement(report_sxw.rml_parse):
    _name = 'account.vat.settlement'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_ids = []
        period_obj = self.pool.get('account.period')
        self.journal_id = data['form']['property_vat_close_journal']
        self.closing_date = data['form']['closing_date']
        self.vat_account_payable = data['form']['property_vat_account_payable']
        self.vat_account_receivable = data['form']['property_vat_account_receivable']
        self.close_vat = data['form']['close_vat']
        if self.close_vat:
            self.display_detail = True
        else:
            self.display_detail = data['form']['display_detail']
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)

        if data['form'].get('period_from', False):
            self.period_ids = period_obj.build_ctx_periods(self.cr, self.uid, data['form']['period_from'],
                                                           data['form']['period_from'])
            periods_l = period_obj.read(self.cr, self.uid, self.period_ids, ['name'])
            for period in periods_l:
                if res['periods'] == '':
                    res['periods'] = period['name']
                else:
                    res['periods'] += ", " + period['name']
        return super(account_vat_settlement, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(account_vat_settlement, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_codes': self._get_codes,
            'get_general': self._get_general,
            'get_currency': self._get_currency,
            'get_lines': self._get_lines,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_start_period,
            'get_basedon': self._get_basedon,
        })
    
    def _get_fiscalyear(self, data):
        if data.get('form', False) and data['form'].get('fiscalyear_id', False):
            return pooler.get_pool(self.cr.dbname).get('account.fiscalyear').browse(self.cr, self.uid, data['form']['fiscalyear_id']).name
        return ''
    
    def _get_account(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return pooler.get_pool(self.cr.dbname).get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).name
        return ''

    def get_start_period(self, data):
        if data.get('form', False) and data['form'].get('period_from', False):
            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr,self.uid,data['form']['period_from']).name
        return ''

    def _get_basedon(self, form):
        return form['form']['based_on']

    def _get_lines(self, based_on, company_id=False, parent=False, level=0, context=None):
        period_list = self.period_ids
        res = self._get_codes(based_on, company_id, parent, level, period_list, context=context)
        if period_list:
            res = self._add_codes(based_on, res, period_list, context=context)
        else:
            self.cr.execute ("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute ("select id from account_period where fiscalyear_id = %s",(fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
            res = self._add_codes(based_on, res, period_list, context=context)
        #TB +
        tax_obj = self.pool.get('account.tax')
        
        tax_codes_list = []
        tax_ids = tax_obj.search(self.cr, self.uid, [('tax_code_id', '!=', False), ('account_collected_id', '!=', False), ('exclude_from_vat_settlement', '=', False)])
        taxes = tax_obj.browse(self.cr, self.uid, tax_ids)
        for tax in taxes:
            tax_codes_list.append(tax.tax_code_id.id)

        #TB -
        i = 0
        top_result = []
        res2 =[]
        while i < len(res):
            if res[i][1].id in tax_codes_list: #TB
                res2.append(res[i][1].id)
                lines = self._sum(self.cr, self.uid, res[i][1].id, period_list, company_id, context)
                if not lines:
                    i+=1
                    continue
                res_dict = { 'code': res[i][1].code,
                    'name': res[i][1].name,
                    'debit': 0,
                    'credit': 0,
                    'tax_amount': lines[0]['tax_amount'] or 0,
                    'type': 1,
                    #'level': res[i][0],
                    'level': '',
                    'pos': 0
                }

                top_result.append(res_dict)
                res_general = self._get_general(res[i][1].id, period_list, company_id, based_on, context=context)
                ind_general = 0
                while ind_general < len(res_general):
                    res_general[ind_general]['type'] = 2
                    res_general[ind_general]['pos'] = 0
                    res_general[ind_general]['level'] = res_dict['level'] + '..........'
                    top_result.append(res_general[ind_general])
                    ind_general+=1
            i+=1
        if self.close_vat:
            self._close_vat(self.cr, self.uid, res2, top_result, period_list, company_id, context=context)
        return top_result

    def _get_general(self, tax_code_id, period_list, company_id, based_on, context=None):
        if not self.display_detail:
            return []
        res = []
        obj_account = self.pool.get('account.account')
        periods_ids = tuple(period_list)

        self.cr.execute('SELECT SUM(line.tax_amount) AS tax_amount, \
                    SUM(line.debit) AS debit, \
                    SUM(line.credit) AS credit, \
                    COUNT(*) AS count, \
                    account.id AS account_id, \
                    account.name AS name,  \
                    account.code AS code \
                FROM account_move_line AS line, \
                    account_account AS account \
                WHERE line.state <> %s \
                    AND line.tax_code_id = %s   \
                    AND line.account_id = account.id \
                    AND account.company_id = %s \
                    AND line.period_id IN %s\
                    AND account.active \
                    AND line.closed_vat IS NOT %s \
                GROUP BY account.id,account.name,account.code \
                HAVING SUM(line.tax_amount) <> 0', \
                ('draft', tax_code_id, company_id, periods_ids, True,))
        res = self.cr.dictfetchall()

        i = 0
        while i<len(res):
            res[i]['account'] = obj_account.browse(self.cr, self.uid, res[i]['account_id'], context=context)
            i+=1
        return res

    def _get_codes(self, based_on, company_id, parent=False, level=0, period_list=[], context=None):
        obj_tc = self.pool.get('account.tax.code')
        #ids = obj_tc.search(self.cr, self.uid, [('parent_id','=',parent),('company_id','=',company_id)], order='sequence', context=context)
        ids = obj_tc.search(self.cr, self.uid, [('parent_id','=',parent),('company_id','=',company_id), ('payment_tax_code_id', '=', False)], order='sequence', context=context)
        res = []
        for code in obj_tc.browse(self.cr, self.uid, ids, {'based_on': based_on}):
            res.append(('.'*2*level, code))

            res += self._get_codes(based_on, company_id, code.id, level+1, context=context)

        return res

    def _add_codes(self, based_on, account_list=[], period_list=[], context=None):
        res = []
        obj_tc = self.pool.get('account.tax.code')
        for account in account_list:
            ids = obj_tc.search(self.cr, self.uid, [('id','=', account[1].id)], context=context)
            sum_tax_add = 0
            for period_ind in period_list:
                for code in obj_tc.browse(self.cr, self.uid, ids, {'period_id':period_ind,'based_on': based_on}):
                    sum_tax_add = sum_tax_add + code.sum_period

            code.sum_period = sum_tax_add
            if  code.sum_period != 0.0: #TB-20121011
                res.append((account[0], code))
        return res

    def _get_currency(self, form, context=None):
        return self.pool.get('res.company').browse(self.cr, self.uid, form['company_id'], context=context).currency_id.name

    def sort_result(self, accounts, context=None):
        result_accounts = []
        ind=0
        old_level=0
        while ind<len(accounts):
            #
            account_elem = accounts[ind]
            #

            #
            # we will now check if the level is lower than the previous level, in this case we will make a subtotal
            if (account_elem['level'] < old_level):
                bcl_current_level = old_level
                bcl_rup_ind = ind - 1

                while (bcl_current_level >= int(accounts[bcl_rup_ind]['level']) and bcl_rup_ind >= 0 ):
                    res_tot = { 'code': accounts[bcl_rup_ind]['code'],
                        'name': '',
                        'debit': 0,
                        'credit': 0,
                        'tax_amount': accounts[bcl_rup_ind]['tax_amount'],
                        'type': accounts[bcl_rup_ind]['type'],
                        'level': 0,
                        'pos': 0
                    }

                    if res_tot['type'] == 1:
                        res_tot['type'] = 2
                        result_accounts.append(res_tot)
                    bcl_current_level = accounts[bcl_rup_ind]['level']
                    bcl_rup_ind -= 1

            old_level = account_elem['level']
            result_accounts.append(account_elem)
            ind += 1

        return result_accounts

    def _sum(self, cr, uid, tax_code_id, period_list, company_id, context):
        periods_ids = tuple(period_list)
        self.cr.execute('SELECT SUM(line.tax_amount) AS tax_amount \
                FROM account_move_line AS line \
                WHERE line.state <> %s \
                    AND line.tax_code_id = %s   \
                    AND line.company_id = %s \
                    AND line.period_id IN %s\
                    AND line.closed_vat IS NOT %s \
                    HAVING SUM(line.tax_amount) <> 0', \
                ('draft', tax_code_id, company_id, periods_ids, True))
        res = self.cr.dictfetchall()
        return res

    def prepare_vat_lines(self, cr, uid, move_id, journal_id, account_id, counter_account,
                          debit_amount, credit_amount, closing_date, period, context=None):
        move_line = {
            'journal_id': journal_id,
            'period_id': period.id,
            'name': _(u'VAT Settlement ') + ': ' + (period.name or '/'),
            'account_id': account_id,
            'move_id': move_id,
            'currency_id': False,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': debit_amount or 0.0,
            'debit': credit_amount or 0.0,
            'date': closing_date,
            'closed_vat': True,
        }
        move_line_counterpart = {
            'journal_id': journal_id,
            'period_id': period.id,
            'name': _(u'VAT Settlement ') + ':' + (period.name or '/'),
            'account_id': counter_account,
            'move_id': move_id,
            'currency_id': False,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': credit_amount or 0.0,
            'debit': debit_amount or 0.0,
            'date': closing_date,
            'closed_vat': True,
        }
        return (move_line, move_line_counterpart)

    def _close_vat(self, cr, uid, tax_code_id, data, period_list, company_id, context=None):
        if context is None:
            context = {}
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        tax_grouped = {}
        res = []

        for tax in data:
            if tax.get('account', False):
                res.append(tax)
        if not res:
            return False
        for r in res:
            key = (r['account'])
            if not key in tax_grouped:
                tax_grouped[key] = r
            else:
                tax_grouped[key]['tax_amount'] += r['tax_amount']
                tax_grouped[key]['debit'] += r['debit']
                tax_grouped[key]['credit'] += r['credit']
        
        print tax_grouped
        period = period_obj.browse(cr, uid, period_list[0])
        new_move = {
            'name': _(u'VAT Settlement ')+': '+(period.name or '/'),
            'journal_id': self.journal_id,
            'date': self.closing_date,
            'period_id': period.id,
            }
        new_move_id = move_obj.create(cr, uid, new_move, context=context)
        
        for tax_acc in tax_grouped.values():
            if tax_acc['debit'] != 0:
                counter_account = self.vat_account_payable
            elif tax_acc['credit'] != 0:
                counter_account = self.vat_account_receivable
            else:
                counter_account = False
                
            new_lines = self.prepare_vat_lines(cr, uid, new_move_id, self.journal_id, tax_acc['account'].id, counter_account, tax_acc['debit'], tax_acc['credit'], self.closing_date, period, context=None)            
            move_line_obj.create(cr, uid, new_lines[0],context)
            move_line_obj.create(cr, uid, new_lines[1], context)               
        self.cr.execute('UPDATE account_move_line AS line SET closed_vat = True \
                        WHERE line.state <> %s \
                        AND line.tax_code_id IN %s   \
                        AND line.company_id = %s \
                        AND line.period_id IN %s\
                        AND line.closed_vat IS NOT %s', \
                    ('draft', tuple(tax_code_id), company_id, tuple(period_list), True,))
        
        move_obj.post(cr, uid, [new_move_id], context=context) 
        return False

report_sxw.report_sxw('report.account.vat.settlement', 'account.tax.code',
    'addons/l10n_hr_vat/report/account_vat_settlement_report.rml', parser=account_vat_settlement, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

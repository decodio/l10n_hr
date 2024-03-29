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
from openerp.tools.translate import _
from vat_book_report_common import get_vat_book_report_common


class Parser(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_ids = []
        period_obj = self.pool.get('account.period')
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)

        if data['form'].get('period_from', False) and data['form'].get('period_to', False):
            self.period_ids = period_obj.build_ctx_periods(self.cr, self.uid, data['form']['period_from'], data['form']['period_to'])
                    
        if not self.period_ids:
            company_id = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.id or False
            '''
            self.period_ids = period_obj.search(self.cr, self.uid, \
                              [('fiscalyear_id', '=', res['fiscalyear']), ('company_id', '=', company_id), ('special', '=', False)])
           '''
            if res.get('fiscalyear',False):
                self.cr.execute ("select id from account_period where fiscalyear_id = %s AND company_id = %s",(res['fiscalyear'], company_id))
            else:
                self.cr.execute ("select id from account_fiscalyear")
                fy = self.cr.fetchall()
                self.cr.execute ("select id from account_period where fiscalyear_id = %s",(fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                self.period_ids.append(p[0])

        periods_l = period_obj.read(self.cr, self.uid, self.period_ids, ['name'])
        for period in periods_l:
            if res['periods'] == '':
                res['periods'] = period['name']
            else:
                res['periods'] += ", "+ period['name']
                                                    
        return super(Parser, self).set_context(objects, data, new_ids, report_type=report_type)
              
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_lines': self._get_lines,   
            'get_knjiga_name': self._get_knjiga_name,             
            'get_company_name': self._get_company_name,
            'get_company_address': self._get_company_address,
            'get_company_nkd': self._get_company_nkd,
            'get_company_vat': self._get_company_vat,                     
            'get_totals': self._get_totals,  
            'get_header_data': self._get_header_data,        
        })        
 
    def _get_header_data(self,data):
        period_obj = self.pool.get('account.period')
        header_data = []
        filter = {'filter': ''}
        period_from = ''
        period_to = ''
        
        if data['form']['period_from']:
            periods_l = period_obj.read(self.cr, self.uid, data['form']['period_from'], ['name'])
            if periods_l:
                period_from = periods_l['name']
        if data['form']['period_to']:
            periods_l = period_obj.read(self.cr, self.uid, data['form']['period_to'], ['name'])
            if periods_l:
                period_to = periods_l['name']    
                                    
        if data['form']['date_stop']:
            try:
                date_stop_formated = self.pool.get('res.lang').format_date(self.cr, self.uid, data['form']['date_stop'], context=self.localcontext)
            except:
                date_stop_formated = data['form']['date_stop'] 
        if data['form']['date_start']:
            try:
                date_start_formated = self.pool.get('res.lang').format_date(self.cr, self.uid, data['form']['date_start'], context=self.localcontext)
            except:
                date_start_formated = data['form']['date_start']  
                
        if data['form']['period_from']:
            filter['filter'] = _('Filter: ') + _('For Period:') + ' ' + period_from
        if data['form']['period_to']:
            filter['filter'] += '- ' + period_to  
        if data['form']['date_start']:                    
            filter['filter'] =  ', ' + _('For Date:') + ' ' + date_start_formated
        if data['form']['date_stop']:                    
            filter['filter'] +=  '-' + date_stop_formated
        header_data.append(filter)
        return header_data       
           
    def _get_company_name(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.name or False
        return name
    
    def _get_company_address(self, data):
        name = (self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.city or '') \
            + ', ' + (self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.street or '')
        return name
    
    def _get_company_nkd(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.l10n_hr_base_nkd_id and \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.l10n_hr_base_nkd_id.code or False
        return name       
    
    def _get_company_vat(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.vat and \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.vat[2:] or \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.oib and \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.oib or False
        return name   

    def _get_knjiga_name(self, data):
        name = False
        knjiga_id = data['form']['knjiga_id'] or False
        if not knjiga_id:
            return name
        
        name = self.pool.get('l10n_hr_pdv.knjiga').browse(self.cr, self.uid, knjiga_id).name
        return name
       
    def _get_lines(self, data):
        stupci = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        row_start_values_sql = """rbr AS rbr, 
            --invoice.number AS invoice_number, 
            --invoice.date_invoice AS invoice_date,
            --COALESCE(invoice_partner_name, ' ') || ', ' || COALESCE(invoice_partner_street, ' ') || ', ' || COALESCE(invoice_partner_city, ' ') AS partner_name,
            --invoice_partner_oib AS partner_oib,
            stavka.name AS invoice_number,
            COALESCE(invoice_date_invoice, am.date) AS invoice_date, 
            COALESCE(invoice_partner_name, p.name, ' ') || ', ' || COALESCE(invoice_partner_street, p.street ,' ') || ', ' || COALESCE(invoice_partner_city, p.city, ' ') AS partner_name,
            SUBSTRING(COALESCE(invoice_partner_oib, p.vat, ' '), 3) AS partner_oib,        
            """
        self.crete_temp_table()

        insert_sql = 'INSERT INTO l10n_hr_vat_' + str(self.uid) +"""(
            rbr, invoice_number, invoice_date, partner_name, partner_oib,
            stupac6, stupac7, stupac8, stupac9, stupac10, stupac11, stupac12,
            stupac13, stupac14, stupac15, stupac16, stupac17, stupac18, stupac19,
            stupac20, stupac21, stupac22, stupac23) """
        return get_vat_book_report_common().get_lines(self, data, stupci, row_start_values_sql, invoice_sql='', insert_sql=insert_sql)


    def crete_temp_table(self):
        sql = """CREATE TEMPORARY TABLE l10n_hr_vat_%(name_sufix)s
                (
                  rbr bigint,
                  invoice_number character varying(64),
                  invoice_date date,
                  partner_name text,
                  partner_oib text,
                  stupac6 numeric,
                  stupac7 numeric,
                  stupac8 numeric,
                  stupac9 numeric,
                  stupac10 numeric,
                  stupac11 numeric,
                  stupac12 numeric,
                  stupac13 numeric,
                  stupac14 numeric,
                  stupac15 numeric,
                  stupac16 numeric,
                  stupac17 numeric,
                  stupac18 numeric,
                  stupac19 numeric,
                  stupac20 numeric,
                  stupac21 numeric,
                  stupac22 numeric,
                  stupac23 numeric
                )
                ON COMMIT DROP;

        """ % {'name_sufix': str(self.uid)}

        self.cr.execute(sql)
        return False
        
    def _get_totals(self):
        return self.sums
'''
report_sxw.report_sxw('report.knjiga.ira', 'account.tax.code',
    'addons/l10n_hr_vat/report/knjiga_ira.rml', parser=knjiga_ira, header=False)

report_sxw.report_sxw('report.knjiga.ira.eu.2014', 'account.tax.code',
    'addons/l10n_hr_vat/report/knjiga_ira_eu_2014.rml', parser=knjiga_ira, header=False)
'''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

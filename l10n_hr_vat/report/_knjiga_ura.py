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

class knjiga_ura(report_sxw.rml_parse):
          
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
            self.period_ids = period_obj.search(self.cr, self.uid, \
                              [('fiscalyear_id', '=', res['fiscalyear']), ('company_id', '=', company_id), ('special', '=', False)])

        periods_l = period_obj.read(self.cr, self.uid, self.period_ids, ['name'])
        for period in periods_l:
            if res['periods'] == '':
                res['periods'] = period['name']
            else:
                res['periods'] += ", "+ period['name']
                                                    
        return super(knjiga_ura, self).set_context(objects, data, new_ids, report_type=report_type)
              
    def __init__(self, cr, uid, name, context=None):
        super(knjiga_ura, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_lines': self._get_lines,   
            'get_knjiga_name': self._get_knjiga_name,             
            'get_company_name': self._get_company_name,
            'get_company_address': self._get_company_address,
            'get_company_nkd': self._get_company_nkd,
            'get_company_vat': self._get_company_vat,                     
        })        
        
    def _get_company_name(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.name or False
        return name
    
    def _get_company_address(self, data):
        name = (self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.city or '') \
            + ', ' + (self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.address and \
                      self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.address[0].street or '')
        return name
    
    def _get_company_nkd(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.l10n_hr_base_nkd_id and \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.l10n_hr_base_nkd_id.code or False
        return name       
    
    def _get_company_vat(self, data):
        name = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.vat and \
            self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.partner_id.vat or False
        return name   

    def _get_knjiga_name(self, data):
        name = False
        knjiga_id = data['form']['knjiga_id'] or False
        if not knjiga_id:
            return name
        
        name = self.pool.get('l10n_hr_pdv.knjiga').browse(self.cr, self.uid, knjiga_id).name
        return name
       
    def _get_lines(self, data):
        res = []
        periods_ids = tuple(self.period_ids)
        knjiga_id = data['form']['knjiga_id'] or False
        company_id = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id']).company_id.id or False
        if not knjiga_id:
            return False
        
#        exclude_tax_code_ids = []
#        for exclude in self.pool.get('l10n_hr_pdv.knjiga').browse(self.cr, self.uid, [knjiga_id])[0].exclude_tax_code_ids:
#            exclude_tax_code_ids.append(exclude.id)
            
        date_start = data['form']['date_start'] or False
        date_stop = data['form']['date_stop'] or False      
        
        where = []
        where.append(('l10n_hr_pdv_knjiga_id', '=', knjiga_id))  
        where.append(('period_id', 'in', periods_ids))
        if date_start:
            where.append(('invoice_date_invoice','>=',date_start))
        if date_stop:
            where.append(('invoice_date_invoice','<=',date_stop))            
        knjiga_obj = self.pool.get('l10n_hr_pdv.knjiga.stavka')
        line_ids = knjiga_obj.search(self.cr, self.uid,where) 

        stupci = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        for line in line_ids:
            rep_line = {}
            redak = knjiga_obj.browse(self.cr, self.uid, line)
            
            rep_line = {'rbr':redak.rbr or False,
                        'invoice_number':redak.invoice_number or False,
                        'invoice_date':redak.invoice_date_invoice or False,
                        'partner_name': (redak.invoice_partner_name or '') + ', ' \
                            + (redak.invoice_partner_street or '') + ', ' \
                            + (redak.invoice_partner_city or ''),
                        'partner_oib': redak.invoice_partner_oib and redak.invoice_partner_oib[2:] or False,}

            for stupac in stupci:
                parent_tax_ids = []
                value_stupac = 0.0
                value_tax = False
                stavka_ids = []
                
                poz_id = self.pool.get('l10n_hr_pdv.report.knjiga').search(self.cr, self.uid, 
                                                    [('knjiga_id','=',knjiga_id),
                                                     ('position','=',str(stupac))])
                if poz_id:
                    stavka_ids = self.pool.get('l10n_hr_pdv.report.knjiga.stavka').search(self.cr, self.uid,
                                                    [('report_knjiga_id','=',poz_id[0])]) 
                
                for stavka in stavka_ids:
#                    if stavka in exclude_tax_code_ids:
#                        continue
                    value = 0.0
                    stavka_obj = self.pool.get('l10n_hr_pdv.report.knjiga.stavka').browse(self.cr, self.uid, stavka)
                    parent_tax_ids = tuple(self.pool.get('account.tax.code').search(self.cr, self.uid, 
                                                    [('parent_id', 'child_of', [stavka_obj.tax_code_id.id])]))
                    koeficijent = stavka_obj.tax_code_koef
                    
                    self.cr.execute('SELECT COALESCE(SUM(line.tax_amount),0) AS tax_amount \
                                FROM account_move_line AS line, \
                                    account_account AS account \
                                WHERE line.state <> %s \
                                    AND line.tax_code_id IN %s  \
                                    AND line.account_id = account.id \
                                    AND account.company_id = %s \
                                    AND line.period_id IN %s \
                                    AND line.move_id = %s \
                                    AND account.active ', ('draft', parent_tax_ids,
                                    company_id, periods_ids,redak.move_id.id,))  
                    value_tax = self.cr.fetchone()
                    if value_tax:
                        value = value_tax[0]
                    if koeficijent == 0:
                        value = 0.0
                    else:
                        value = value / koeficijent                         
                    value_stupac = value_stupac + (value or 0.0) 
                              
                rep_line['stupac' + str(stupac)] = value_stupac       
  
            res.append(rep_line)
        
        res = sorted(res, key=lambda x:x['rbr'])
        return res

report_sxw.report_sxw('report.knjiga.ura', 'account.tax.code',
    'l10n_hr_vat/report/knjiga_ura.rml', parser=knjiga_ura, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

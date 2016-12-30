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

from openerp.osv import osv, fields
from openerp.tools.translate import _


class cancel_vat_settlement(osv.osv_memory):
    _name = 'cancel.vat.settlement'
    _inherit = 'account.vat.declaration'
 
    _columns = {
        'closing_date': fields.date('Closing Date', help='Posting date for posting of VAT Settlement.'),
        'property_cancel_vat_account_payable': fields.property(
            type='many2one',
            relation='account.account',
            string="VAT Account Payable",
            domain="[('type', '=', 'other')]",
            help="This account will be used for reconciliation of purchase VAT"),
                
         'property_cancel_vat_account_receivable': fields.property(
            type='many2one',
            relation='account.account',
            string="VAT Account Receivable",
            domain="[('type', '=', 'other')]",
            help="This account will be used for reconciliation of sale VAT"),

        'property_cancel_vat_close_journal': fields.property(
            type='many2one', 
            relation='account.journal', 
            domain=[('type','=','general')],
            string='VAT Settlement Journal', 
            help="This journal will be used for posting VAT Settlement"),
        }    

    def cancel_vat_settlement(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.tax.code'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if datas['form']['period_from'] == False:
            raise osv.except_osv(_('Error !'), _('Period is missing! Please enter one.')) 
        if datas['form']['close_vat'] == True:
            if datas['form']['property_cancel_vat_close_journal'] == False:
                raise osv.except_osv(_('Error !'), _('VAT closing journal is missing! Please enter one.'))
            if datas['form']['property_cancel_vat_account_receivable'] == False:
                raise osv.except_osv(_('Error !'), _('VAT Account Receivable is missing! Please enter one.'))
            if datas['form']['property_cancel_vat_account_payable'] == False:
                raise osv.except_osv(_('Error !'), _('VAT Account Payable is missing! Please enter one.'))
            if datas['form']['closing_date'] == False:
                raise osv.except_osv(_('Error !'), _('Closing Date is missing! Please enter one.'))
        datas['form']['company_id'] = self.pool.get('account.tax.code').browse(cr, uid, [datas['form']['chart_tax_id']], context=context)[0].company_id.id
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'cancel.vat.settlement',
            'datas': datas,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

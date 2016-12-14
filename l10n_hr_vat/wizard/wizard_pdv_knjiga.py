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
from openerp.osv import orm, fields
from openerp.tools.translate import _


class pdv_knjiga(orm.TransientModel):
    _name = 'pdv.knjiga'
    _inherit = 'account.common.report'

    _columns = {
        'chart_tax_id': fields.many2one('account.tax.code', 'Chart of Tax',
                          help='Select Charts of Taxes', required=True,
                          domain=[('parent_id', '=', False)]),
        'knjiga_id': fields.many2one('l10n_hr_pdv.knjiga', 'Porezna knjiga', 
                      help='Odaberite poreznu knjigu za ispis', required=True),
        'date_start': fields.date('Od datuma'),
        'date_stop': fields.date('Do datuma'),
        'journal_ids': fields.many2many('account.journal', 'pdv_knjiga_journal_rel2', 'pdv_knjiga_id', 'journal_id',
                                       'Journals')
    }

    def _get_tax(self, cr, uid, context=None):
        taxes = self.pool.get('account.tax.code').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return taxes and taxes[0] or False

    _defaults = {
        'chart_tax_id': _get_tax
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        if datas['form']['knjiga_id']:
            knjiga_type = self.pool.get('l10n_hr_pdv.knjiga').browse(cr, uid, datas['form']['knjiga_id']).type
        else:
            raise orm.except_orm(_('Knjiga nije upisana!'),
                                 _("Knjiga je obavezan podatak kod ovog ispisa!"))

#        if (datas['form']['period_from'] and not datas['form']['period_to']) or \
#            (not datas['form']['period_from'] and datas['form']['period_to']):
#            raise orm.except_orm(_('Krivi periodi!'),_("Potrebno je upisati oba perioda za ispis po periodima!"))
#
#        if (datas['form']['date_start'] and not datas['form']['date_stop']) or \
#            (not datas['form']['date_start'] and datas['form']['date_stop']):
#            raise orm.except_orm(_('Krivo razdoblje!'),_("Potrebno je upisati oba datuma za ispis po datumima!"))

        report_name = None
        if knjiga_type == 'ira':
            # report_name = 'knjiga.ira'
            # report_name = 'knjiga.ira.eu.2014'
            report_name = 'knjiga_ira_ods'
        elif knjiga_type in ('ura', 'ura_uvoz'):
            # report_name = 'knjiga.ura'
            # report_name = 'knjiga.ura.eu.2014'
            report_name = 'knjiga_ura_ods'
        elif knjiga_type in ('ura_tu', 'ura_st', 'ura_nerezident'):
            report_name = 'knjiga_ura_prijenos'

        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
        }

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

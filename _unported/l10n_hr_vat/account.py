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

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'do_not_check_vat': fields.boolean("Do not check partner VAT number",
                                           help="Do not check partner VAT number"),
        'pdv_eu': fields.boolean('PDV-EU', help="PDV EU"),
    }

    _defaults = {
        'do_not_check_vat': lambda *a : False,
        'pdv_eu':  lambda *a : False,
    }


class account_move(osv.osv):
    _inherit = "account.move"

    def check_vat_number(self, cr, uid, partner_id, context=None):
        if not partner_id:
            raise osv.except_osv(_('Partner missing!'),_("Partner is required for this type of posting!"))
        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, partner_id, context={})
        if (not partner.vat) or (not partner_obj.check_vat(cr, uid, [partner_id], context=None) ):
            raise osv.except_osv(_('Invalid VAT number!'),_("Partner (%s) does not have VAT number!") % partner.name)
        return True

    def validate(self, cr, uid, ids, context=None):
        res=super(account_move,self).validate(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context):
            if move.journal_id.type in ('purchase','sale','purchase_refund','sale_refund'):
                if move.journal_id.do_not_check_vat:
                    continue
            if move.journal_id.type in ('purchase','sale','purchase_refund','sale_refund') and move.partner_id:            
                self.check_vat_number(cr, uid, move.partner_id.id, context) 
        return res


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    _columns = {
       'closed_vat': fields.boolean('Closed', help='Mark if VAT is closed for given period!'),
       }


class account_tax(osv.osv):
    _inherit = "account.tax"
    
    _columns = {
       'exclude_from_vat_settlement': fields.boolean('Exclude from VAT Settlement',
            help="If this field is checked this tax will not be included in VAT settlement process."),
         }
    
    _defaults = {
        'exclude_from_vat_settlement': False,         
        }


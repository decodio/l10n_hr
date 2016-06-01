# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_fiskal_lazy
#    Author: Davor Bojkić
#    mail:   bole@dajmi5.com
#    Copyright (C) 2012- Daj Mi 5, 
#                  http://www.dajmi5.com
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

class res_users(osv.osv):
    _inherit = "res.users"
    
    _columns = {
                'prostor_id':fields.many2one('fiskal.prostor','Podružnica', help="Zadana podružnica"),
                'uredjaj_id':fields.many2one('fiskal.uredjaj','Naplatni uredjaj',help="Zadani naplatni uređaj"),
                'journal_id':fields.many2one('account.journal','Dokument', help="Zadani dnevnik"),
                'journals':fields.many2many('account.journal','account_journal_user_rel','journals','users','Dozvoljeni dnevnici knjženja'),
                'uredjaji':fields.many2many('fiskal.uredjaj','fiskal_uredjaj_user_rel','uredjaji','users','Dozvoljeni naplatni uredjaji'),
                'double_check':fields.boolean('Dvostruka provjera na računima'),
                }
    
class fiskal_uredjaj(osv.Model):
    _inherit = 'fiskal.uredjaj'
    _columns = {
                'users':fields.many2many('res.users','fiskal_uredjaj_user_rel','users','uredjaji','Odobreno za korisnike')
                }
    
class account_journal(osv.Model):
    _inherit = 'account.journal'
    
    _columns = {
                'users':fields.many2many('res.users','account_journal_user_rel','users','journals','Users allowed')
                }

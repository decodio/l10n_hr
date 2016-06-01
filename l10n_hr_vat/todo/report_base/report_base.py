# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 DAJ MI 5 (<http://www.dajmi5.com>).
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

from openerp.osv import fields, osv


class report_base(osv.Model):
    _name = 'report.base'

    _columns = {
                'name':fields.char('Report name', size=256),
                'code':fields.char('Report code', size=32),
                'type':fields.selection([('root',u'Glavni Izvještaj'),
                                         ('sum',u'Podizvještaj - sumirani podaci'),
                                         ('multi',u'Podizvještaj - redovi sa podacima')],'Tip'),
                'parent_id':fields.many2one('report.base',u'Nadređeni izvještaj', ondelete='restrict'),
                'child_ids':fields.one2many('report.base','parent_id',),
                'line_ids':fields.one2many('report.base.line','report_id','Report lines'),
                'name_construct':fields.selection([('desc',u'Samo opis'),
                                                   ('code',u'Samo šifra'),
                                                   ('cdes',u'Šifra + opis')],'Naziv', 
													help=u"Kontrukcija teksta za redak izvještaja"),
                }
    
class report_base_line(osv.Model):
    _name = 'report.base.line'
    
    _columns = {
        'sequence':fields.integer('Sequence'),
        'report_id':fields.many2one('report.base','Report'),
        'parent_id':fields.many2one('report.base.line','Parent'),
        'code':fields.char('Code',size=32),
        'description':fields.char('Description',size=256),
        'help':fields.text('Help'),
        'required':fields.boolean('Required'),
        'type':fields.selection([('char','Znakovni niz ograničene duljine'),
                                 ('txt','Tekst proizvoljne duljine'),
                                 ('int', 'Cjeloi broj'),
                                 ('float','Decimalni broj'),
                                 ('bool','DA/NE polje'),
                                 ('sel','Izbor zadanih podataka'),
                                 ('view','Informativno polje, ne traži unos podataka'),
                                 ('sum','Suma unešenih podataka')],'Field type'),
        'special':fields.text('Parametri', help="parametri za SQL upite u mogu varirati od izvjestaja do izvjestaja!!!")
    }
    
     
    def name_get(self, cr, uid, ids, context=None):
        res= []
        for r in self.browse(cr, uid, ids):
            construct = r.report_id.name_construct 
            if not construct: #zbog nepotpunih CSV-ova u JOPPD-u
                construct = 'cdes'

            if   construct == 'desc':
                name = r.description
            elif construct == 'code': 
                name = r.code
            elif construct == 'cdes': 
                name = " ".join([r.code,r.description])
            res.append((r.id,name))
        return res
        
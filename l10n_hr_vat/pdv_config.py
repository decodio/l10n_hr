# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Author: Marko Tribuson @Infokom.hr
#    mail:
#    Copyright:
#    Contributions: Bruno Bardic @Slobodni-programi.hr
#                   Tomislav Bosnjakovic @Slobodni-programi.hr
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

class l10n_hr_pdv_obrazac(osv.osv):
    _name = 'l10n_hr_pdv.obrazac'
    _description = 'Obrasci PDV'
   
   
    _columns = {
        'code': fields.char('Code', size=32, required=True),
        'name': fields.char('Description', size=64, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'sequence': fields.integer('Sequence', required=True, help="Poredak obrasca u prikazu"),

    }
    _order = "sequence"
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            return user.company_id.id
        return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]

    
    _defaults = {
        'company_id': _default_company,
        'sequence': 10,
    }


class l10n_hr_pdv_report_obrazac(osv.osv):
    _name = 'l10n_hr_pdv.report.obrazac'
    _description = 'Postavke ispisa PDV obrasca'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'id': fields.integer('Id', readonly=True), #TB                
        'obrazac_id': fields.many2one('l10n_hr_pdv.obrazac','Obrazac PDV', select=True, required=True), #TB
        'position': fields.selection([
            ('A','Redak (A)'),
            ('I','Redak (I)'),
            ('I1','Redak (I.1)'),            
            ('I2','Redak (I.2)'),
            ('I21','Redak (I.2.1)'),
            ('I22','Redak (I.2.2)'),
            ('I23','Redak (I.2.3)'),
            ('I24','Redak (I.2.4)'),
            ('I3','Redak (I.3)'),
            ('I4','Redak (I.4)'),
            ('I5','Redak (I.5)'),
            ('I6','Redak (I.6)'),
            ('I7','Redak (I.7)'), 
            ('I8','Redak (I.8)'),
            ('I9','Redak (I.9)'), 
            ('I10','Redak (I.10)'),                                                                                 
            ('II','Redak (II)'),
            ('II1','Redak (II.1)'),         
            ('II2','Redak (II.2)'),
            ('II3','Redak (II.3)'),               
            ('II4','Redak (II.4)'),
            ('II5','Redak (II.5)'),
            ('II6','Redak (II.6)'),
            ('II7','Redak (II.7)'),
            ('II8','Redak (II.8)'),
            ('II9','Redak (II.9)'),
            ('II10','Redak (II.10)'),
            ('II11','Redak (II.11)'),
            ('II12','Redak (II.12)'),
            ('II13','Redak (II.13)'),
            ('II14','Redak (II.14)'), 
            ('II15','Redak (II.15)'),                       
            ('III','Redak (III)'),               
            ('III1','Redak (III.1)'),
            ('III2','Redak (III.2)'),               
            ('III3','Redak (III.3)'),            
            ('III4','Redak (III.4)'),               
            ('III5','Redak (III.5)'),            
            ('III6','Redak (III.6)'),               
            ('III7','Redak (III.7)'),
            ('III8','Redak (III.8)'),
            ('III9','Redak (III.9)'), 
            ('III10','Redak (III.10)'), 
            ('III11','Redak (III.11)'), 
            ('III12','Redak (III.12)'),  
            ('III13','Redak (III.13)'),   
            ('III14','Redak (III.14)'),  
            ('III15','Redak (III.15)'),                                                                                                 
            ('IV','Redak (IV)'), 
            ('V','Redak (V)'), 
            ('VI','Redak (VI)'),
            ('VII','Redak (VII)'),
            ('VIII','Redak (VIII)'),
            ('VIII1','Redak (VIII.1)'),
            ('VIII11','Redak (VIII.1.1)'),
            ('VIII12','Redak (VIII.1.2)'),
            ('VIII13','Redak (VIII.1.3)'),
            ('VIII14','Redak (VIII.1.4)'),
            ('VIII15','Redak (VIII.1.5)'),
            ('VIII2','Redak (VIII.2)'),
            ('VIII3','Redak (VIII.3)'),
            ('VIII31','Redak (VIII.3.1)'),
            ('VIII32','Redak (VIII.3.2)'),
            ('VIII33','Redak (VIII.3.3)'),
            ('VIII4','Redak (VIII.4)'),
            ('VIII5','Redak (VIII.5)'),
            ('VIII6','Redak (VIII.6)'),
            ('VIII7','Redak (VIII.7)')
            ],'Pozicija', select=True, required=True),
        'stavka_osnovice_ids': fields.one2many('l10n_hr_pdv.report.obrazac.osnovica.stavka', 'redak_id', 'Osnovica'),
        'stavka_poreza_ids': fields.one2many('l10n_hr_pdv.report.obrazac.porez.stavka', 'redak_id', 'Porez'),     
        'stavka_nepriznati_porez_ids': fields.one2many('l10n_hr_pdv.report.obrazac.nepriznati_porez.stavka', 'redak_id', 'Nepriznati porez'),
        #'base_code_id': fields.many2one('account.tax.code', 'Osnovica', required=True),
        #'base_code_tax_koef': fields.float('Stopa',  help="Stopa za izračun. Upisati stopu po kojoj se izračunava osnovica iz upisane šifre poreza."), 
        #'tax_code_id': fields.many2one('account.tax.code', 'Porez', required=False),               
    }
    
    _sql_constraints = [
        #('l10n_hr_pdv_report_obrazac_uniq', 'unique (company_id,position)', 'Isti redak se smije korisiti samo jednom za jednu tvrtku!')
        ('l10n_hr_pdv_report_obrazac_uniq', 'unique (company_id, obrazac_id, position)', 'Isti redak se smije korisiti samo jednom za jednu tvrtku!')    
    ]
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            return user.company_id.id
        return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]

    _defaults = {
        'company_id': _default_company,
        #'base_code_tax_koef': 1.0,
    }
    

class l10n_hr_pdv_report_obrazac_osnovica_stavka(osv.osv):
    _name = 'l10n_hr_pdv.report.obrazac.osnovica.stavka'
    _description = 'Postavke ispisa PDV obrasca - stavke osnovice'
    _rec_name='base_code_id'
        
    _columns = {
        'redak_id': fields.many2one('l10n_hr_pdv.report.obrazac', 'Redak',
                                     required=True, ondelete='cascade', readonly=True, select=True),
        'base_code_id': fields.many2one('account.tax.code', 'Osnovica', required=True),
        'base_code_tax_koef': fields.float('Stopa',  help="Stopa za izračun. Upisati stopu po kojoj se izračunava osnovica."), 
    }
       
    _defaults = {
        'base_code_tax_koef': 1.0,
    }   


class l10n_hr_pdv_report_obrazac_porez_stavka(osv.osv):
    _name = 'l10n_hr_pdv.report.obrazac.porez.stavka'
    _description = 'Postavke ispisa PDV obrasca - stavke poreza'
    _rec_name='base_code_id'
        
    _columns = {
        'redak_id': fields.many2one('l10n_hr_pdv.report.obrazac', 'Redak', required=True, ondelete='cascade', readonly=True),        
        'base_code_id': fields.many2one('account.tax.code', 'Osnovica', required=True),
        'base_code_tax_koef': fields.float('Stopa',  help="Stopa za izračun. Upisati stopu po kojoj se izračunava porez."), 
    }
       
    _defaults = {
        'base_code_tax_koef': 1.0,
    }   

class l10n_hr_pdv_report_obrazac_nepriznati_porez_stavka(osv.osv):
    _name = 'l10n_hr_pdv.report.obrazac.nepriznati_porez.stavka'
    _description = 'Postavke ispisa PDV obrasca - stavke nepriznatog poreza'
    _rec_name='base_code_id'
        
    _columns = {
        'redak_id': fields.many2one('l10n_hr_pdv.report.obrazac', 'Redak', required=True, ondelete='cascade', readonly=True),        
        'base_code_id': fields.many2one('account.tax.code', 'Osnovica', required=True),
        'base_code_tax_koef': fields.float('Stopa',  help="Stopa za izračun. Upisati stopu po kojoj se izračunava nepriznati porez."), 
    }
       
    _defaults = {
        'base_code_tax_koef': 1.0,
    }   


class l10n_hr_pdv_report_knjiga(osv.osv):
    _name = 'l10n_hr_pdv.report.knjiga'
    _description = 'Postavke ispisa URA-IRA'
    _rec_name = 'id'
        
    _columns = {
#        'report_type': fields.selection([
#            ('ira','Knjiga IRA'),      
#            ('ura','Knjiga URA'),                                 
#            ],'Ispis', select=True, required=True),
        'id': fields.integer('Id', readonly=True),
        'knjiga_id': fields.many2one('l10n_hr_pdv.knjiga','Porezna knjiga', select=True, required=True),
        'position': fields.selection([
            ('6','Stupac 6'),
            ('7','Stupac 7'),
            ('8','Stupac 8'),
            ('9','Stupac 9'),
            ('10','Stupac 10'),
            ('11','Stupac 11'),         
            ('12','Stupac 12'),
            ('13','Stupac 13'),               
            ('14','Stupac 14'),
            ('15','Stupac 15'),               
            ('16','Stupac 16'),
            ('17','Stupac 17'),               
            ('18','Stupac 18'),  
            ('19','Stupac 19'), 
            ('20','Stupac 20'), 
            ('21','Stupac 21'), 
            ('22','Stupac 22'),                                         
            ('23','Stupac 23'),
            ],'Pozicija', select=True, required=True),
        'line_ids': fields.one2many('l10n_hr_pdv.report.knjiga.stavka', 'report_knjiga_id', 'Stavke poreza'),                
    }

    _sql_constraints = [
        ('l10n_hr_pdv_report_knjiga_uniq', 'unique (knjiga_id, position)', 'Isti redak se smije koristi samo jednom po ispisu !')
    ]
    

class l10n_hr_pdv_report_knjiga_stavka(osv.osv):
    _name = 'l10n_hr_pdv.report.knjiga.stavka'
    _description = 'Postavke ispisa URA-IRA po porezima'
    _rec_name='tax_code_id'
        
    _columns = {   
        'report_knjiga_id': fields.many2one('l10n_hr_pdv.report.knjiga', 'Ispis knjige', required=True),                           
        'tax_code_id': fields.many2one('account.tax.code', 'Porez', required=True),        
        'tax_code_koef': fields.float('Stopa',  required=True, help="Stopa za izračun. Upisati stopu po kojoj se izračunava osnovica iz upisane šifre poreza."),       
    }
    
    _defaults = {
        'tax_code_koef': 1.0,
    }    

class l10n_hr_pdv_report_eu_obrazac(osv.osv):
    _name = 'l10n_hr_pdv.report.eu.obrazac'
    _description = 'Postavke ispisa Obrazaca EU'
    _rec_name = 'id'

    _columns = {
        'id': fields.integer('Id', readonly=True),
        'obrazac_id': fields.many2one('l10n_hr_pdv.eu.obrazac', 'Obrazac EU', select=True, required=True),
        'position': fields.selection([
            ('11', 'Stupac 11'),
            ('12', 'Stupac 12'),
            ('13', 'Stupac 13'),
            ('14', 'Stupac 14')
            ], 'Pozicija', select=True, required=True),
        'line_ids': fields.one2many('l10n_hr_pdv.eu.obrazac.stavka', 'obrazac_eu_id', 'Stavke obrazca EU'),
    }

    _sql_constraints = [
        ('l10n_hr_pdv.report.eu.obrazac_uniq', 'unique (obrazac_id, position)',
         'Isti redak se smije koristi samo jednom po ispisu !')
    ]


class l10n_hr_pdv_eu_obrazac_stavka(osv.osv):
    _name = 'l10n_hr_pdv.eu.obrazac.stavka'
    _description = 'Postavke ispisa Obrazaca EU'
    _rec_name = 'tax_code_id'

    _columns = {
        'obrazac_eu_id': fields.many2one('l10n_hr_pdv.report.eu.obrazac', 'Obrazac EU', required=True),
        'tax_code_id': fields.many2one('account.tax.code', 'Porez', required=True),
        'tax_code_koef': fields.float('Stopa', required=True,
            help="Stopa za izračun. Upisati stopu po kojoj se izračunava osnovica iz upisane šifre poreza."),
    }

    _defaults = {
        'tax_code_koef': 1.0,
    }

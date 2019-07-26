# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 OCA-Croatia
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

import uuid
import os
import base64

import openerp.addons.decimal_precision as dp
from openerp.osv import osv, fields

from datetime import datetime
from dateutil.relativedelta import relativedelta

from lxml import etree
from lxml import objectify

from openerp.addons.report_base import reports_common as rc
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class res_company(osv.Model):
    _inherit = 'res.company'
    _columns = {
        #porezna za ispis, code za xml
        'porezna_code':fields.char('Šifra Porezne ispostave', size=12, help="Šifra nadležne ispostave Porezne uprave"),
        'porezna':fields.char('Porezna ispostava', size=128)
    }


class l10n_hr_porez(osv.Model):
    _name='l10n.hr.porez'
    _description = u'Porezni izvještaji'

# ne punim vise kao default već na preuzimanju podataka
#     def _populate_new_pdv(self, cr, uid, context=None):
#
#         report = self.pool.get('l10n.hr.report').search(cr, uid,[('code','=','PDV')])[0]
#         pdv_ids = self.pool.get('l10n.hr.report.line').search(cr, uid,[('report_id','=',report)])
#         return [(0,0, {'position':a}) for a in pdv_ids]
    
    def _get_start_period(self, cr, uid, context=None):
        period = self.pool.get('account.period').search(cr, uid, 
                    [('name','=',datetime.strftime(datetime.today() + relativedelta(day=1, months=-1), '%m/%Y'))])
        return period and period[0] or False #defaultno uzima prošli mjesec.
    
    def name_get(self, cr, uid, ids, context=None):
        return [(r.id,' '.join(((r.state=='draft'  and u'Nacrt PDV izvještaja' or
                                 r.state=='done'   and u'Predani PDV izvještaj' or
                                 r.state=='cancel' and u'Otkazani PDV izvještaj'),
                                'od',datetime.strftime(datetime.strptime(r.date_start,"%Y-%m-%d"),"%d.%m."),
                                'do',datetime.strftime(datetime.strptime(r.date_stop ,"%Y-%m-%d"),"%d.%m.%Y")))) 
                for r in self.browse(cr, uid, ids)]
    
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([('draft','Nacrt'),
                                   ('sent','Predano'),
                                   ('cancel','Otkazano')],'Status'), #TODO: .. flow
        'date' : fields.datetime('Sastavljeno', help="Datum i vrijeme sastavljanja izvještaja"),
        'period_start': fields.many2one('account.period','Početni Period'),
        'period_end': fields.many2one('account.period','Završni Period'),
        'date_start' : fields.date('Od datuma'),
        'date_stop' : fields.date('Do datuma'),
        'pdv_lines':fields.one2many('l10n.hr.pdv.line','obrazac',string='PDV Obrazac'),
        'uuid_pdv' : fields.char('PDV XML Id.', size=64, help="UUID identifikator u XML datoteci"),
        'pdvs_lines':fields.one2many('l10n.hr.pdvs.line','obrazac',string='PDV-S Obrazac'),
        'uuid_pdvs' : fields.char('PDV-S XML Id.', size=64, help="UUID identifikator u XML datoteci"),
        'pdvzp_lines':fields.one2many('l10n.hr.pdvzp.line','obrazac',string='PDV-ZP Obrazac'),
        'uuid_pdvzp' : fields.char('PDV-ZP XML Id.', size=64, help="UUID identifikator u XML datoteci"),
        'payment':fields.selection([('pov','POVRAT'),
                                    ('pred','PREDUJAM'),
                                    ('ust','USTUP POVRATA')],'Opcija uplate'),
        'payment_amm':fields.float('Iznos', digits_compute=dp.get_precision('Account'),)
    }
    
    _defaults = {
        'state':'draft',
        #'pdv_lines':lambda self,cr,uid,c: self._populate_new_pdv(cr, uid, context=c),
        'period_start':lambda self,cr,uid,c:self._get_start_period(cr, uid,context=c),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
    } 
    
    
    
    def onchange_period(self, cr, uid, ids, start, end, context=None):
        
        period_obj = self.pool.get('account.period')
        
        if start and not end: #ako nema zavrsni uzmi isti kao i pocetni
            period = period_obj.browse(cr, uid, start)
            res = {'value':{'period_end':start,
                            'date_start':period.date_start, 
                            'date_stop':period.date_stop },}
                   #'domain':{'period_end':['&',('state','=','draft'),('id','>=',start)]}} 
        else:
            pstart = period_obj.browse(cr, uid, start)
            pstop = period_obj.browse(cr, uid, end)
            
            if end < start : #za svaki slucaj! 
                res = {'value':{'period_end':start,
                                'date_start':pstart.date_start,
                                'date_stop':pstart.date_stop},}
            else:
                res = {'value':{'date_start':pstart.date_start,
                                'date_stop':pstop.date_stop},}
                       #'domain':{'period_end':['&',('state','=','draft'),('id','>=',start)]}}
        res['domain']={'period_end':['&',('state','=','draft'),('id','>=',start)]}
        return res

    def button_print(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if len(obj.pdv_lines) != 0:
            self.button_print_pdv(cr, uid, ids, context=context)
        if len(obj.pdvs_lines) != 0:
            self.button_pront_pdvs(cr, uid, ids, context=context)
        if len(obj.pdvzp_lines) != 0:
            self.button_print_pdvzp(cr, uid, ids, context=context)
        return True
    
    def button_print_pdv(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.report.xml',
                'report_name': 'pdv',
                'datas': {'ids': ids,
                          'model': 'l10n.hr.porez',
                          'form': self.read(cr, uid, ids[0], context=context)},
                'context':context,
                'nodestroy':True}
    
    def button_print_pdvs(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.report.xml',
                'report_name': 'pdvs',
                'datas': {'ids': ids,
                          'model': 'l10n.hr.porez',
                          'form': self.read(cr, uid, ids[0], context=context)},
                'context':context,
                'nodestroy':True}
        
    def button_print_pdvzp(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.report.xml',
                'report_name': 'pdvzp',
                'datas': {'ids': ids,
                          'model': 'l10n.hr.porez',
                          'form': self.read(cr, uid, ids[0], context=context)},
                'context':context,
                'nodestroy':True}
    
    def button_create_xml(self, cr, uid, ids, context=None):
        obrazac = self.browse(cr, uid, ids[0])
        
        izvjesce_sastavio = rc.get_izvjesce_sastavio(self,cr, uid, context)
        #autor = {'naziv':u'Pero Perić','ime':u'Pero','prezime':u'Perić'}
        meta = {
            'autor':izvjesce_sastavio['naziv'],
            'format':'text/xml',
            'jezik':'hr-HR',
            'tip':u'Elektronički obrazac',
            'adresant':u'Ministarstvo Financija, Porezna uprava, Zagreb'
        }
        
        company = rc.get_company_data(self, cr, uid, 'PDV', context )
        
        zaglavlje = {
            'datum_od': obrazac.date_start,
            'datum_do': obrazac.date_stop,
            'o_naziv': company['naziv'],
            'o_oib': company['oib'],
            'o_mjesto': company['mjesto'],
            'o_ulica': company['ulica'],
            'o_broj': company['kbr'],
            'tel': company['tel'], 
            'fax': company['fax'], 
            'ime': izvjesce_sastavio['ime'],
            'prezime': izvjesce_sastavio['prezime'],
            'email': company['email'],
            'ispostava': company['porezna_code'] 
        }

        zaglavlje = self.etree_zaglavlje(zaglavlje)   
        
        pdv, pdv_uuid = self.create_xml_pdv(cr, uid, ids, meta, zaglavlje, context)
        pdvs, pdvs_uuid = self.create_xml_pdvs(cr, uid, ids, meta, zaglavlje, context) if obrazac.pdvs_lines  else False, False
        pdvzp, pdvzp_uuid = self.create_xml_pdvzp(cr, uid, ids, meta, zaglavlje, context) if obrazac.pdvzp_lines else False, False
        
        
        pdv = ['Obrazac PDV', pdv, 'pdv2014', 'ObrazacPDV-v8-0.xsd']
        pdvs = pdvs and ['Obrazac PDV-S', pdvs, 'pdvs', 'ObrazacPDVS-v1-0.xsd'] or False
        pdvzp = pdvzp and ['Obrazac ZP', pdvzp, 'zp', 'ObrazacZP-v1-0.xsd'] or False
        period = obrazac.period_start.name.replace('/','-')
        for file in [pdv, pdvs, pdvzp]:
            if file:
                self.validate_xml(file)
                self.attach_xml_file(cr, uid, ids, file, period, context)
            
        return obrazac.write({'date':datetime.now(),
                              'uuid_pdv':pdv_uuid,
                              'uuid_pdvs':pdvs_uuid,
                              'uuid_pdvzp':pdvzp_uuid})    
    
    def attach_xml_file(self, cr, uid, ids, file, period, context=None):
        assert len(ids) == 1, "Only one ID accepted"
        file_name = '_'.join([file[0], period])+'.xml'
        attach_obj = self.pool.get('ir.attachment')
        context.update({'default_res_id': ids[0], 'default_res_model': 'l10n.hr.porez'})
        attach_id = attach_obj.create(cr, uid, {'name': file_name, 
                                                'datas': base64.encodestring(file[1]), 
                                                'datas_fname': file_name}, context=context)
        return attach_id
    
    def validate_xml(self, file):
        xsd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'schema',file[2])
        os.chdir(xsd_path)
        xsd_file = os.path.join(xsd_path,file[3])
        xsd = StringIO(open(xsd_file,'r').read()) 
        xml_schema = etree.XMLSchema(etree.parse(xsd))
        try:
            # print file[1] #test xml printout to console
            xml_schema.assert_(etree.parse(StringIO(file[1])))
        except AssertionError as E:
            print file[1] #test xml printout to console
            raise osv.except_osv(u'Greška u podacima',E[0])
        return True
        
    def etree_meta(self, metadata):
        identifikator = uuid.uuid4()
        datum_vrijeme = rc.get_current_datetime()
        
        MD = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0")
        md = MD.Metapodaci(
                MD.Naslov(metadata['naslov'], dc="http://purl.org/dc/elements/1.1/title"),
                MD.Autor(metadata['autor'], dc="http://purl.org/dc/elements/1.1/creator"), 
                MD.Datum(datum_vrijeme, dc="http://purl.org/dc/elements/1.1/date"),
                MD.Format(metadata['format'], dc="http://purl.org/dc/elements/1.1/format"),
                MD.Jezik(metadata['jezik'], dc="http://purl.org/dc/elements/1.1/language"),
                MD.Identifikator(identifikator, dc="http://purl.org/dc/elements/1.1/identifier"),
                MD.Uskladjenost(metadata['uskladjenost'], dc="http://purl.org/dc/terms/conformsTo"),
                MD.Tip(metadata['tip'], dc="http://purl.org/dc/elements/1.1/type"),
                MD.Adresant(metadata['adresant'])
                )
        return md, identifikator
    
    def etree_zaglavlje(self, zaglavlje):
        EM = objectify.ElementMaker(annotate=False)
        zagl = EM.Zaglavlje(
                    EM.Razdoblje(
                        EM.DatumOd(zaglavlje['datum_od']),
                        EM.DatumDo(zaglavlje['datum_do'])),
                    EM.Obveznik(
                        EM.Naziv(zaglavlje['o_naziv']),
                        EM.OIB(zaglavlje['o_oib']),
                        EM.Adresa(
                            EM.Mjesto(zaglavlje['o_mjesto']),
                            EM.Ulica(zaglavlje['o_ulica']),
                            #Broj dodam kasnije ako postoji
                            ),),
                    EM.ObracunSastavio(
                        EM.Ime(zaglavlje['ime']),
                        EM.Prezime(zaglavlje['prezime']),
                        #Tel, Fax i Email dodam kasnije ako postoje!
                        ),
                    EM.Ispostava(zaglavlje['ispostava'])) 
        #punim podatke ako postoje...
        if zaglavlje['o_broj']: zagl.Obveznik.Adresa.Broj    = EM.Broj(zaglavlje['o_broj'])
        if zaglavlje['tel']   : zagl.ObracunSastavio.Telefon = EM.Telefon(zaglavlje['tel'])
        if zaglavlje['fax']   : zagl.ObracunSastavio.Fax     = EM.Fax(zaglavlje['fax'])
        #if 'email' in zaglavlje.keys() : zagl.ObracunSastavio.Email   = EM.Email(zaglavlje['email'])
        return zagl
    
    def etree_tostring(self, object):
        objectify.deannotate(object)
        return etree.tostring(object, pretty_print=True).replace('ns0:','').replace(':ns0','') 
    
    def create_xml_pdvzp(self, cr, uid, ids, metadata, zaglavlje, context=None):
        metadata['naslov']       = u"Zbirna prijavu za isporuke dobara i usluga u druge države članice Europske unije"
        metadata['uskladjenost'] = u'ObrazacZP-v1-0'
        md, identifikator = self.etree_meta(metadata)
        
        cr.execute("""
        select row_number() over (order by c.id) rbr
            ,c.code drzava
            ,p.vat porbr
            ,coalesce(z.dobra,0) dobra
            ,coalesce(z.dobra_4263,0) dob_4263 -- nemam definirano pa punim nule
            ,coalesce(z.dobra_tro,0) dob_tro   -- nemam definirano
            ,coalesce(z.usluge,0) usluge 
        from l10n_hr_pdvzp_line z
            left join res_partner p on p.id=z.partner_id
            left join res_country c on c.id=p.country_id
        where obrazac=%(obrazac)s
        """ ,{'obrazac':ids[0]})
        zp_vals = cr.dictfetchall()
        
        cr.execute("""
        select sum(dobra) dob
            ,sum(dobra_4263) d_4263
            ,sum(dobra_tro) d_tro
            ,sum(usluge) usl 
        from l10n_hr_pdvzp_line where obrazac = %(obrazac)s
        """ ,{'obrazac':ids[0]})
        pdvs_sum = cr.dictfetchone()
        
        if len(zp_vals) == 0: return False,False
        EM = objectify.ElementMaker(annotate=False)
        zp_list = [ EM.Isporuka(
                          EM.RedBr(l['rbr']),
                          EM.KodDrzave(l['drzava']),
                          EM.PDVID(l['porbr'].startswith(l['drzava']) and l['porbr'][2:] or l['drzava']),
                          EM.I1(l['dobra']),
                          EM.I2(l['dob_4263']),
                          EM.I3(l['dob_tro']),
                          EM.I4(l['usluge'])) for l in zp_vals]
        
        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka),
                           EM.IsporukeUkupno(
                              EM.I1(pdvs_sum['dob']),
                              EM.I2(pdvs_sum['d_4263']),
                              EM.I3(pdvs_sum['d_tro']),
                              EM.I4(pdvs_sum['usl'])))
        tijelo.Isporuke.Isporuka = zp_list
        
        ZP = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacZP/v1-0")
        zp = ZP.ObrazacZP(md, zaglavlje, tijelo, verzijaSheme="1.0")
        return self.etree_tostring(zp), identifikator 
    
    def create_xml_pdvs(self, cr, uid, ids, metadata, zaglavlje, context=None):
        metadata['naslov']       = u"Prijava za stjecanje dobara i primljene usluge iz drugih država članica Europske unije"
        metadata['uskladjenost'] = u'ObrazacPDVS-v1-0'
        md, identifikator = self.etree_meta(metadata)

        cr.execute("""
        select row_number() over (order by c.id) rbr,
            c.code drzava, p.vat porbr, 
            coalesce(s.dobra,0) dobra, 
            coalesce(s.usluge,0) usluge
        from l10n_hr_pdvs_line s
            left join res_partner p on p.id=s.partner_id
            left join res_country c on c.id=p.country_id
        where obrazac = %(obrazac)s
        """ ,{'obrazac':ids[0]})
        pdvs_vals = cr.dictfetchall() 
        
        cr.execute("""
        select coalesce(sum(dobra),0) dobra
            ,coalesce(sum(usluge),0) usluge 
        from l10n_hr_pdvs_line where obrazac = %(obrazac)s
        """ ,{'obrazac':ids[0]})
        pdvs_sum = cr.dictfetchone()
        EM = objectify.ElementMaker(annotate=False)
        isporuke_list = [ EM.Isporuka(
                              EM.RedBr(l['rbr']),
                              EM.KodDrzave(l['drzava']),
                              EM.PDVID(l['porbr'].startswith(l['drzava']) and l['porbr'][2:] or l['drzava']),
                              EM.I1(l['dobra']),
                              EM.I2(l['usluge'])) for l in pdvs_vals]
        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka),
                           EM.IsporukeUkupno(
                              EM.I1(pdvs_sum['dobra']),
                              EM.I2(pdvs_sum['usluge'])))
        tijelo.Isporuke.Isporuka = isporuke_list
        
        
        PDVS = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDVS/v1-0")
        pdvs = PDVS.ObrazacPDVS(md, zaglavlje, tijelo, verzijaSheme="1.0")
        return self.etree_tostring(pdvs) , identifikator

    def create_xml_pdv(self, cr, uid, ids, metadata, zaglavlje, context=None):
        metadata['naslov']=u"Prijava poreza na dodanu vrijednost"
        metadata['uskladjenost'] = u'ObrazacPDV-v8-0'
        md, identifikator = self.etree_meta(metadata)
        
        cr.execute("""
        select rl.special
            ,coalesce(l.osnovica,0) osn
            ,coalesce(l.porez,0) por
        from l10n_hr_pdv_line l
            left join l10n_hr_report_line rl on rl.id=l.position
        where obrazac = %(obrazac)s order by l.id
        """ , {'obrazac':ids[0]})
        pdv_vals = cr.dictfetchall() 
        
        EM = objectify.ElementMaker(annotate=False)
        tijelo = EM.Tijelo(
                    EM.Podatak000(pdv_vals[0]['osn']),
                    EM.Podatak100(pdv_vals[1]['osn']),
                    EM.Podatak101(pdv_vals[2]['osn']),
                    EM.Podatak102(pdv_vals[3]['osn']),
                    EM.Podatak103(pdv_vals[4]['osn']),
                    EM.Podatak104(pdv_vals[5]['osn']),
                    EM.Podatak105(pdv_vals[6]['osn']),
                    EM.Podatak106(pdv_vals[7]['osn']),
                    EM.Podatak107(pdv_vals[8]['osn']),
                    EM.Podatak108(pdv_vals[9]['osn']),
                    EM.Podatak109(pdv_vals[10]['osn']),
                    EM.Podatak110(pdv_vals[11]['osn']),
                    EM.Podatak200(EM.Vrijednost(pdv_vals[12]['osn']), EM.Porez(pdv_vals[12]['por'])),
                    EM.Podatak201(EM.Vrijednost(pdv_vals[13]['osn']), EM.Porez(pdv_vals[13]['por'])),
                    EM.Podatak202(EM.Vrijednost(pdv_vals[14]['osn']), EM.Porez(pdv_vals[14]['por'])),
                    EM.Podatak203(EM.Vrijednost(pdv_vals[15]['osn']), EM.Porez(pdv_vals[15]['por'])),
                    EM.Podatak204(EM.Vrijednost(pdv_vals[16]['osn']), EM.Porez(pdv_vals[16]['por'])),
                    EM.Podatak205(EM.Vrijednost(pdv_vals[17]['osn']), EM.Porez(pdv_vals[17]['por'])),
                    EM.Podatak206(EM.Vrijednost(pdv_vals[18]['osn']), EM.Porez(pdv_vals[18]['por'])),
                    EM.Podatak207(EM.Vrijednost(pdv_vals[19]['osn']), EM.Porez(pdv_vals[19]['por'])),
                    EM.Podatak208(EM.Vrijednost(pdv_vals[20]['osn']), EM.Porez(pdv_vals[20]['por'])),
                    EM.Podatak209(EM.Vrijednost(pdv_vals[21]['osn']), EM.Porez(pdv_vals[21]['por'])),
                    EM.Podatak210(EM.Vrijednost(pdv_vals[22]['osn']), EM.Porez(pdv_vals[22]['por'])),
                    EM.Podatak211(EM.Vrijednost(pdv_vals[23]['osn']), EM.Porez(pdv_vals[23]['por'])),
                    EM.Podatak212(EM.Vrijednost(pdv_vals[24]['osn']), EM.Porez(pdv_vals[24]['por'])), 
                    EM.Podatak213(EM.Vrijednost(pdv_vals[25]['osn']), EM.Porez(pdv_vals[25]['por'])),
                    EM.Podatak214(EM.Vrijednost(pdv_vals[26]['osn']), EM.Porez(pdv_vals[26]['por'])),
                    EM.Podatak215(EM.Vrijednost(pdv_vals[27]['osn']), EM.Porez(pdv_vals[27]['por'])),
                    EM.Podatak300(EM.Vrijednost(pdv_vals[28]['osn']), EM.Porez(pdv_vals[28]['por'])),
                    EM.Podatak301(EM.Vrijednost(pdv_vals[29]['osn']), EM.Porez(pdv_vals[29]['por'])),
                    EM.Podatak302(EM.Vrijednost(pdv_vals[30]['osn']), EM.Porez(pdv_vals[30]['por'])),
                    EM.Podatak303(EM.Vrijednost(pdv_vals[31]['osn']), EM.Porez(pdv_vals[31]['por'])),
                    EM.Podatak304(EM.Vrijednost(pdv_vals[32]['osn']), EM.Porez(pdv_vals[32]['por'])),
                    EM.Podatak305(EM.Vrijednost(pdv_vals[33]['osn']), EM.Porez(pdv_vals[33]['por'])),
                    EM.Podatak306(EM.Vrijednost(pdv_vals[34]['osn']), EM.Porez(pdv_vals[34]['por'])),
                    EM.Podatak307(EM.Vrijednost(pdv_vals[35]['osn']), EM.Porez(pdv_vals[35]['por'])),
                    EM.Podatak308(EM.Vrijednost(pdv_vals[36]['osn']), EM.Porez(pdv_vals[36]['por'])),
                    EM.Podatak309(EM.Vrijednost(pdv_vals[37]['osn']), EM.Porez(pdv_vals[37]['por'])),
                    EM.Podatak310(EM.Vrijednost(pdv_vals[38]['osn']), EM.Porez(pdv_vals[38]['por'])),
                    EM.Podatak311(EM.Vrijednost(pdv_vals[39]['osn']), EM.Porez(pdv_vals[39]['por'])),
                    EM.Podatak312(EM.Vrijednost(pdv_vals[40]['osn']), EM.Porez(pdv_vals[40]['por'])),
                    EM.Podatak313(EM.Vrijednost(pdv_vals[41]['osn']), EM.Porez(pdv_vals[41]['por'])),
                    EM.Podatak314(EM.Vrijednost(pdv_vals[42]['osn']), EM.Porez(pdv_vals[42]['por'])),
                    EM.Podatak315(pdv_vals[43]['por']),
                    EM.Podatak400(abs(pdv_vals[44]['por'])),
                    EM.Podatak500(abs(pdv_vals[45]['por'])),
                    EM.Podatak600(abs(pdv_vals[46]['por'])),
                    EM.Podatak700(0.0))
            
        PDV = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDV/v8-0")
        pdv = PDV.ObrazacPDV(md, zaglavlje, tijelo, verzijaSheme="8.0")
        return self.etree_tostring(pdv), identifikator 
    
    #########################################################
    # GET DATA
    #########################################################    
    def check_repair_data(self, cr):
        """
        Diferent verzions of account_template leads to erros...
        ugly hack/ quick fix
        """
        cr.execute("""
        update account_tax_code
         set info = 'I.' || info where id in(
            select id from account_tax_code
            where name like 'I%' and info not like 'I%')
        """)
        cr.execute("""
        update account_tax_code
        set info = 'III. OBRAČUNANI PRETPOREZ UKUPNO (1.+2.+3.+4.+5.+6.+7.+8.+9.+10.+11.+12.+13.+14.+15.)'
        where info in ('III. OBRAČUNANI PRETPOREZ UKUPNO (1.+2.+3.+4.+ 5.+6.+7.)',
                       'III. OBRAČUNANI PRETPOREZ UKUPNO (1.+2.+3.+4.+5.+6.+7.)')
        """)
        # TODO: remove once all DBs are updated with last version of data
    
    def button_get_new_data(self, cr, uid, ids, context=None):
        #malo ugly hack ali radi!
        self.check_repair_data(cr) # ovo zakomentirati ako je novo stvorena baza, korisiti samo na prebačenima!
        
        # start colecting data
        pdv_obj = self.browse(cr, uid, ids[0])
        p_start = pdv_obj.period_start.id
        p_end  = pdv_obj.period_end.id
        if not p_start or not p_end:
            raise osv.except_osv(u'Nedostaju podaci!',u'Odaberite period za koji želite sastaviti izvještaj!')
        
        #PDV, PDV-S, ZP - praznim postojeće podatke
        for table in ('l10n_hr_pdv_line','l10n_hr_pdvs_line','l10n_hr_pdvzp_line'):
            cr.execute('delete from %s where obrazac = %s'  % (table, ids[0]))

        EU_codes = ('BE','BG','CZ','DK','DE','EE','IE','EL','ES','FR','IT','CY','LV','LT','LU','HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','UK')
        # Ovo mozda mozemo pokupiti sa fiskalnih pozicija, sad to ima tamo samo treba napraviti grupu EU-Croatia (doslovno eu minus hr)


        pdv_obj.write({'pdv_lines'  :[(0,0,p) for p in self.pdv_fetch_data(cr, p_start, p_end)],
                       'pdvs_lines' :[(0,0,s) for s in self.pdvs_fetch_data(cr, p_start, p_end, EU_codes)],
                       'pdvzp_lines':[(0,0,z) for z in self.zp_fetch_data(cr, p_start, p_end, EU_codes)]})
        self.pdv_summarize(cr, uid, ids, context=None)
        return True
    
    def zp_fetch_data(self, cr, p_start, p_end, EU_codes, context=None):
        #TODO: Dobra 42,63 i dobra trostrano nemam definirana zasada pisem nule!
        cr.execute("""
        SELECT partner_id 
            ,sum(product) dobra
            ,0 dobra_4263
            ,0 dobra_tro
            ,sum(service) usluge
        FROM
            (SELECT rp.id partner_id
                  , rc.code code
                  , SUBSTRING(rp.vat,3) vat 
                  , ml.tax_amount product
                  , 0 service
                FROM account_move_line ml  
                   left join account_move m on m.id=ml.move_id
                   left join account_invoice ai on ai.move_id=m.id
                   left join res_partner rp on rp.id=ml.partner_id
                   left join res_country rc on rc.id=rp.country_id
                   left join product_product pp on pp.id=ml.product_id
                   left join product_template pt on pt.id=pp.product_tmpl_id
                WHERE m.state='posted'
                  and ai.type in ('out_invoice', 'in_refund')
                  and ml.period_id between %(p_start)s and %(p_end)s
                  and rc.code in %(EU)s
                  and pt.type IN ('product','consu')
                
                UNION 
                
            SELECT rp.id partner_id
                  , rc.code code
                  , SUBSTRING(rp.vat,3) vat
                  , 0 product
                  , ml.tax_amount service
                FROM account_move_line ml 
                   left join account_move m on m.id=ml.move_id
                   left join account_invoice ai on ai.move_id=m.id
                   left join res_partner rp on rp.id=ml.partner_id
                   left join res_country rc on rc.id=rp.country_id
                   left join product_product pp on pp.id=ml.product_id
                   left join product_template pt on pt.id=pp.product_tmpl_id
                WHERE m.state='posted'
                  and ai.type in ('out_invoice', 'in_refund')
                  and ml.period_id between %(p_start)s and %(p_end)s
                  and rc.code in %(EU)s
                  and pt.type = 'service'
            ) a
            GROUP BY partner_id, a.code 
            ORDER by a.code 
        """ , {'EU':EU_codes, 'p_start':p_start, 'p_end':p_end})
        res = cr.dictfetchall()
        return res
    
    def pdvs_fetch_data(self, cr, p_start, p_end, EU_codes, context=None):
        cr.execute("""
        SELECT partner_id 
            ,coalesce(sum(product),0) dobra
            ,coalesce(sum(service),0) usluge
        FROM
            (SELECT rp.id partner_id
                  , rc.code code
                  , SUBSTRING(rp.vat,3) vat
                  , ml.tax_amount product
                  , 0 service
                FROM account_move_line ml  
                   left join account_move m on m.id=ml.move_id
                   left join account_invoice ai on ai.move_id=m.id
                   left join res_partner rp on rp.id=ml.partner_id
                   left join res_country rc on rc.id=rp.country_id
                   left join product_product pp on pp.id=ml.product_id
                   left join product_template pt on pt.id=pp.product_tmpl_id
                WHERE m.state='posted'
                  and ai.type in ('in_invoice', 'out_refund')
                  and ml.period_id between %(p_start)s and %(p_end)s
                  and rc.code in %(EU)s
                  and pt.type IN ('product','consu')
                
                UNION 
                
            SELECT rp.id partner_id
                  , rc.code code
                  , SUBSTRING(rp.vat,3) vat
                  , 0 product
                  , ml.tax_amount service
                FROM account_move_line ml 
                   left join account_move m on m.id=ml.move_id
                   left join account_invoice ai on ai.move_id=m.id
                   left join res_partner rp on rp.id=ml.partner_id
                   left join res_country rc on rc.id=rp.country_id
                   left join product_product pp on pp.id=ml.product_id
                   left join product_template pt on pt.id=pp.product_tmpl_id
                WHERE m.state='posted'
                  and ai.type in ('in_invoice', 'out_refund')
                  and ml.period_id between %(p_start)s and %(p_end)s
                  and rc.code in %(EU)s
                  and pt.type = 'service'
            ) a
            GROUP BY partner_id, a.code 
            ORDER by a.code 
        """ , {'EU':EU_codes, 'p_start':p_start, 'p_end':p_end})
        res = cr.dictfetchall()
        return res
     
    def pdv_fetch_data(self, cr, p_start, p_end, context=None):
        cr.execute(""" 
        SELECT rl.id as position
            ,coalesce(sum(a.osnovica),0) osnovica
            ,coalesce(sum(a.porez),0) porez
        FROM (
            SELECT substring(tc.code,2) code, tc.info, ml.tax_amount osnovica, 0 porez
            FROM account_move_line ml 
                left join account_move m on m.id=ml.move_id
                right outer join account_tax_code tc on(ml.tax_code_id = tc.id)
            WHERE m.state='posted'
              AND tc.code like %(osn)s 
              AND ml.period_id between %(p_start)s and %(p_end)s
            UNION
            SELECT substring(tc.code,2) code, tc.info, 0 osnovica, ml.tax_amount porez
            FROM account_move_line ml
                left join account_move m on m.id=ml.move_id
                right outer join account_tax_code tc on(ml.tax_code_id = tc.id)
              AND m.state='posted'
              AND tc.code like %(por)s
              AND ml.period_id between %(p_start)s and %(p_end)s
            ) a
        LEFT JOIN report_base_line rl on rl.description=a.info
        WHERE rl.id is not Null
        GROUP BY a.code, position
        ORDER BY position
        """ , {'p_start':p_start, 'p_end':p_end, 'osn':'o%', 'por':'p%'})
        res = cr.dictfetchall()
        return res 
    
    def pdv_summarize(self, cr, uid, ids, context=None):
        pdv_obj = self.browse(cr, uid, ids[0])
        vals=[]
        code_list = [{'code':'100', 'like':'1%'},
                     {'code':'200', 'like':'2%'},
                     {'code':'300', 'like':'3%'},
                     {'code':'o01',  },
                     {'code':'PDV_4',},
                     {'code':'PDV_5',},
                     {'code':'PDV_6',}]
        total = 0
        for line in code_list:
            line_sum = self.pdv_fetch_sum(cr, ids, line)
            
            if 'like' in line.keys():
                vals.append((1, line_sum['line']['id'], {'osnovica': line_sum['sum']['osnovica'],
                                                         'porez'   : line_sum['sum']['porez']}))
            else:
                if line['code']=='o01': 
                    vals.append((1, line_sum['line']['id'], {'osnovica':vals[0][2]['osnovica']+vals[1][2]['osnovica']}))
                elif line['code']=='PDV_4':
                    porez4 = vals[1][2]['porez']-vals[2][2]['porez']
                    vals.append((1, line_sum['line']['id'], {'porez':porez4}))
                elif line['code']=='PDV_5':
                    porez5 = line_sum['line']['porez']
                    vals.append((1, line_sum['line']['id'], {'porez': porez5}))
                elif line['code']=='PDV_6':
                    total = porez4 + porez5
                    vals.append((1, line_sum['line']['id'], {'porez':total}))
           #TODO: OPCIJE UPLATE
        return pdv_obj.write({'payment_amm':total,
                              'pdv_lines':vals})
    
    def pdv_fetch_sum(self, cr, ids, cond):
        res = {}
        cr.execute("""
        select l.id
            ,coalesce(l.osnovica,0) osnovica
            ,coalesce(l.porez,0) porez 
        from l10n_hr_pdv_line l
            left join report_base_line rl on rl.id=l.position
        where obrazac = %(obrazac)s and rl.code = %(code)s
        """, {'obrazac':ids[0], 'code':cond['code']})
        res['line'] = cr.dictfetchone() #id, osn, por linije za koju dohvaćam sume
        if res['line'] is None:
            pass
        
        sum = False
        if 'like' in cond.keys():
            cr.execute("""
            select sum(l.osnovica) osnovica, sum(l.porez) porez
            from l10n_hr_pdv_line l
              left join report_base_line rl on rl.id=l.position
            where obrazac = %(obrazac)s and rl.code like %(like)s 
            and rl.code != %(exclude)s
            """ ,{'obrazac':ids[0], 'like':cond['like'],'exclude':cond['code']})
            res['sum'] = cr.dictfetchone()
            
        return res
    
            
class l10n_hr_pdv_line(osv.Model):
    _name='l10n.hr.pdv.line'
    _description = "stavke PDV obrasca"
    
    _columns = {
        'obrazac':fields.many2one('l10n.hr.porez','Obrazac'),
        'position':fields.many2one('report.base.line','Pozicija',help="Pozicija PDV obrasca"),
        'osnovica':fields.float('Osnovica', digits_compute=dp.get_precision('Account')),
        'porez':fields.float('Porez', digits_compute=dp.get_precision('Account')),
    } 
    
    
class l10n_hr_pdvs_line(osv.Model):
    _name = 'l10n.hr.pdvs.line'
    _description = "Stavke PDV-S obrasca"  
    
    _columns = {
        'obrazac':fields.many2one('l10n.hr.porez','Obrazac'),
        'partner_id':fields.many2one('res.partner','Partner'),
        'dobra':fields.float('Dobara', digits_compute=dp.get_precision('Account')),
        'usluge':fields.float('Usluge', digits_compute=dp.get_precision('Account'))
    }  
    
    
class l10n_hr_pdvzp_line(osv.Model):
    _name = 'l10n.hr.pdvzp.line'
    _description = "Stavke PDV-ZP obrasca"  
    
    _columns = {
        'obrazac':fields.many2one('l10n.hr.porez','Obrazac'),
        'partner_id':fields.many2one('res.partner','Partner'),
        'dobra':fields.float('Dobra', digits_compute=dp.get_precision('Account'), 
                             help="Vrijednost isporuke dobara u HRK"),
        'dobra_4263':fields.float('Dobra (42,63)', digits_compute=dp.get_precision('Account'),
                             help="Vrijednost isporuke dobara u postupcima 42 i 63 u HRK"),
        'dobra_tro':fields.float('Dobra (trostrano)', digits_compute=dp.get_precision('Account'),
                             help="Vrijednost isporuke dobara u okviru trostranog posla u HRK"),
        'usluge':fields.float('Usluge', digits_compute=dp.get_precision('Account'))
    }  
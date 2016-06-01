# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_fiskal
#    Author: Davor Bojkić
#    mail:   bole@dajmi5.com
#    Copyright (C) 2012- Daj Mi 5, 
#                  http://www.dajmi5.com
#    Contributions: Hrvoje ThePython - Free Code!
#                   Goran Kliska (AT) Slobodni Programi
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
import logging
from openerp.osv import fields, osv, orm
import datetime
import uuid
from fiskal import *
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class res_users(osv.osv):
    _inherit = "res.users"
    _columns = {
        'oib': fields.related('partner_id','vat',type='char', string='OIB osobe',
                              help='OIB osobe koja potvrdjuje racune za potrebe fiskalizacije'),
    }


class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'separator': fields.char('Separator',size=3, help='Use this as separator in invoice number'),
        'fina_certifikat_id': fields.many2one('crypto.certificate', string="Fiskal certifikat",
            domain="[('cert_type', 'in', ('fina_demo','fina_prod') )]", #todo company_id
            help="Aktivni FINA certifikat za fiskalizaciju.",
            ),    
        'fiskal_prostor_ids': fields.one2many('fiskal.prostor','company_id', string="Poslovni prostori",
            help="Poslovni prostori (fiskalizacija).",
            ),    
    }


class fiskal_prostor(osv.Model):
    _name = 'fiskal.prostor'
    _description = 'Podaci o poslovnim prostorima za potrebe fiskalizacije'
    
    _columns = {
        'name': fields.char('Naziv poslovnog prostora', size=128 , select=1),
        'company_id':fields.many2one('res.company','Tvrtka', required="True"),
        'oznaka_prostor': fields.char('Oznaka poslovnog prostora', required="True", size=20),
        'datum_primjene': fields.datetime('Datum', help ="Datum od kojeg vrijede navedeni podaci"),
        'ulica': fields.char('Ulica', size=100),
        'kbr': fields.char('Kucni broj', size=4),
        'kbr_dodatak': fields.char('Dodatak kucnom broju', size=4),
        'posta': fields.char('Posta', size=12),
        'naselje': fields.char('Naselje', size=35),
        'opcina'   :fields.char('Naziv opcine ili grada', size=35, required="True"),
        'prostor_other':fields.char('Ostali tipovi adrese', size=100,
                                    help="Ostali tipovi adresa, npr internet trgovina ili pokretna trgovina"),

        'sustav_pdv':fields.boolean('U sustavu PDV-a'),
        'radno_vrijeme' : fields.char('Radno Vrijeme', required="True", size=1000),
        'sljed_racuna':fields.selection ((('N','Na nivou naplatnog uredjaja'),('P','Na nivou poslovnog prostora')),'Sljed racuna'),
        'spec':fields.char('OIB Informaticke tvrtke', required="True", size=1000),
        'uredjaj_ids': fields.one2many('fiskal.uredjaj','prostor_id','Uredjaji'),
        'fiskal_log_ids':fields.one2many('fiskal.log','fiskal_prostor_id','Logovi poruka', help="Logovi poslanih poruka prema poreznoj upravi"),
        'state':fields.selection (( ('draft','Upis')
                                   ,('active','Aktivan')
                                   ,('closed','Zatvoren')
                                   )
                                  ,'Status zatvaranja'),
                }

    _defaults = {
                 'sustav_pdv':"True",
                 'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'fiskal.prostor', context=c),
                 'sljed_racuna':"P",
                 }

    _constraints={}

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'fiskal_log_ids':False,
            'uredjaj_ids':False,
        })
        return super(fiskal_prostor, self).copy(cr, uid, id, default, context)
    
    
    def validate(self,cr,uid,ids):
        #kbr must be numeric 
        #posta = zip (numeric)
        return True
    
    def get_fiskal_data(self, cr, uid, company_id=False, context=None):
        fina_cert = False
        if not company_id:
            user_obj = self.pool.get('res.users')
            company_id = user_obj.browse(cr, uid, [uid])[0].company_id.id
        company_obj = self.pool.get('res.company')    
        company = company_obj.browse(cr, uid, [company_id])[0]
        fina_cert = company.fina_certifikat_id
        if not fina_cert:
            raise osv.except_osv(_('Error'), _('Neispravne postavke certifikata!'))
            return False
        cert_type = fina_cert.cert_type
        if not cert_type in ('fina_demo','fina_prod'):
            return False
        if cert_type == 'fina_demo':
            file_name = "FiskalizacijaServiceTest.wsdl"
        elif cert_type == 'fina_prod':
            file_name = "FiskalizacijaService.wsdl"
        wsdl_file = 'file://' + os.path.join(os.path.dirname(os.path.abspath(__file__)),'wsdl',file_name)
        
        if not ( fina_cert.state=='confirmed' and fina_cert.csr and fina_cert.crt):
            return False, False, False

        #radi ako je server pokrenut sa -c: path = os.path.join(os.path.dirname(os.path.abspath(config.parser.values.config)),'oe_fiskal')
        path = os.path.join(os.path.dirname(os.path.abspath(config.rcfile)),'oe_fiskal')
        if not os.path.exists(path):
            os.mkdir(path,0777) #TODO 0660 or less

        key_file = os.path.join(path, "{0}_{1}_{2}_key.pem".format(cr.dbname, company_id, fina_cert.id) )         
        cert_file= os.path.join(path, "{0}_{1}_{2}_crt.pem".format(cr.dbname, company_id, fina_cert.id) )

        for file in (key_file, cert_file):
            if not os.path.exists(file):
                with open(file, mode='w') as f:
                    content = file.endswith('_key.pem') and fina_cert.csr or fina_cert.crt
                    f.write(content)
                    f.flush()

        return wsdl_file, key_file, cert_file
        
    def button_test_echo(self, cr, uid, ids, fields, context=None):
        if context is None:
            context ={}
        for prostor in self.browse(cr, uid, ids):
            wsdl, key, cert = self.get_fiskal_data(cr, uid, company_id=prostor.company_id.id)
            a = Fiskalizacija('echo', wsdl, key, cert, cr, uid, oe_obj = prostor)
            odgovor = a.echo()
        return odgovor

    def button_prijavi_prostor(self, cr, uid, ids, fields, context=None):
        if context is None:
            context ={}
        self.posalji_prostor(cr, uid, ids, fields, 'prostor_prijava', context=context)

    def button_odjavi_prostor(self, cr, uid, ids, fields, context=None):
        if context is None:
            context ={}
        self.posalji_prostor(cr, uid, ids, fields, 'prostor_odjava', context=context)


    def posalji_prostor(self, cr, uid, ids, fields, msgtype, context=None):
        prostor=self.browse(cr, uid, ids)[0]
        # Provjera adrese : mora biti jedan tip, ne oba i ne nijedan
        if (prostor.prostor_other and prostor.ulica):
            raise osv.except_osv(_('Greška: Dupla adresa'),
                                 _('Nije moguće prijaviti dva tipa adrese za jedan poslovni prostor!'))
        elif not (prostor.prostor_other or prostor.ulica):
            raise osv.except_osv(_('Greška: Nema adrese'),
                                 _('Unesite adresne podatke ili opisnu adresu prostora!'))

        wsdl, key, cert = self.get_fiskal_data(cr, uid, company_id=prostor.company_id.id)
        if not wsdl:
            return False
        a = Fiskalizacija(msgtype, wsdl, key, cert, cr, uid, oe_obj = prostor)
                
        if not prostor.datum_primjene:
            datum_danas=a.start_time['datum']
        else: 
            #  datum_danas = prostor.datum_primjene
            datum_danas=a.start_time['datum']

        ##prvo punim zaglavlje
        #a.t = start_time['datum']  # mislim da ovdje ide today ako je Zatvaranje !!!
        a.zaglavlje.DatumVrijeme = a.start_time['datum_vrijeme']
        a.zaglavlje.IdPoruke = str(uuid.uuid4())  
        ## podaci o pos prostoru
        #a.pp = a.client2.factory.create('tns:PoslovniProstor') 
        #a.prostor.Oib= prostor.company_id.partner_id.vat[2:] #'57699704120' 
        
        if prostor.company_id.fina_certifikat_id.cert_type == 'fina_prod':
            a.prostor.Oib = prostor.company_id.partner_id.vat[2:]  # pravi OIB company
        elif prostor.company_id.fina_certifikat_id.cert_type == 'fina_demo':
            a.prostor.Oib = prostor.spec[2:]  #OIB IT firme Mora odgovarati OIB-u sa Cert-a
        
        a.prostor.OznPoslProstora=prostor.oznaka_prostor
        a.prostor.RadnoVrijeme=prostor.radno_vrijeme
        a.prostor.DatumPocetkaPrimjene=datum_danas #'08.02.2013' #datum_danas   e ak ovo stavim baci gresku.. treba dodat raise ili nekaj!!!
        a.prostor.SpecNamj =prostor.spec  #57699704120'
        
        #Mogući su i "ostali" tipovi- internet trgovina ili pokretna trgovina..
        adresni_podatak = a.client2.factory.create('tns:AdresniPodatakType')
        if prostor.prostor_other:
            adresa=a.client2.factory.create('tns:OstaliTipoviPP')
            adresni_podatak.OstaliTipoviPP=prostor.prostor_other
            a.prostor.AdresniPodatak = adresni_podatak
        else :
            adresa = a.client2.factory.create('tns:Adresa')
            adresa.Ulica= prostor.ulica
            if prostor.kbr:
                adresa.KucniBroj=prostor.kbr
            if prostor.kbr_dodatak:
                adresa.KucniBrojDodatak=prostor.kbr_dodatak
            adresa.BrojPoste=prostor.posta
            adresa.Naselje=prostor.naselje
            adresa.Opcina= prostor.opcina

            adresni_podatak.Adresa = adresa
            a.prostor.AdresniPodatak = adresni_podatak

        a.prostor.OznakaZatvaranja ='Z'
        if not(msgtype == 'prostor_odjava'): 
            a.prostor.__delattr__('OznakaZatvaranja') 
        
        odgovor = a.posalji_prostor()
        if odgovor[0]==200:
            self.write(cr, uid, prostor.id, {'datum_primjene': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) })
        return True
    

class fiskal_uredjaj(osv.Model):
    _name = 'fiskal.uredjaj'
    _description = 'Podaci o poslovnim prostorima za potrebe fiskalizacije'

    def name_get(self, cr, uid, ids, context=None):
        res = {}
        for u in self.browse(cr, uid, ids, context=context):
            res[u.id] = ' / '.join( (u.prostor_id.name or '', u.name or '') )
        return res.items()
    
    _columns = {
        'name': fields.char('Naziv naplatnog uredjaja', size=128 , select=1),
        'prostor_id':fields.many2one('fiskal.prostor','Prostor',help='Prostor naplatnog uredjaja.'),
        'oznaka_uredjaj': fields.integer('Oznaka naplatnog uredjaja', required="True" ),
                }


class fiskal_log(osv.Model):
    _name='fiskal.log'
    _description='Fiskal log'    
    
    def _get_log_type(self,cursor,user_id, context=None):
        return (('prostor_prijava','Prijava prostora'),
                ('prostor_odjava','Odjava prostora'),
                ('racun','Fiskalizacija racuna'),
                ('racun_ponovo','Ponovljeno slanje racuna'),              
                ('echo','Echo test poruka '),
                ('other','Other types')
               )
        
    _columns ={
        'name': fields.char('Oznaka', size=64, help="Jedinstvena oznaka komunikacije", readonly=True),
        'type': fields.selection (_get_log_type,'Vrsta poruke', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Racun', readonly=True, select=True),
        'fiskal_prostor_id': fields.many2one('fiskal.prostor', 'Prostor', readonly=True),
        'sadrzaj':fields.text('Poslana poruka', readonly=True),
        'odgovor':fields.text('Odgovor', readonly=True),
        'greska':fields.text('Greska', readonly=True),
        'time_stamp':fields.datetime('Vrijeme', readonly=True),
        'time_obr':fields.char('Vrijeme obrade',size=16, help='Vrijeme obrade podataka', readonly=True), #vrijeme obrade prmljeno_vrijeme-poslano_vrijem
        'user_id': fields.many2one('res.users', 'Osoba', readonly=True),
        'company_id':fields.many2one('res.company','Tvrtka', required=False),
        'pos_order_id': fields.integer('MP Racun', readonly=True)
    }

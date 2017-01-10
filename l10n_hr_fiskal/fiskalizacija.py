# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import os
# from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.config import config as odoo_config
from datetime import datetime
from pytz import timezone
from lxml import etree as et
try:
    import fisk
except ImportError:
    fisk = None


class ResUsers(models.Model):
    _inherit = "res.users"

    oib = fields.Char(
        string='OIB osobe',
        related='partner_id.vat',
        help='OIB osobe koja potvrdjuje racune za potrebe fiskalizacije')


class ResCompany(models.Model):
    _inherit = "res.company"

    separator = fields.Char(
        'Separator', size=3,
        help='Use this as separator in invoice number')
    fina_certifikat_id = fields.Many2one(
        'crypto.certificate',
        string="Fiskal certifikat",
        domain="[('cert_type', 'in', ('fina_demo','fina_prod') )]",
        help="Aktivni FINA certifikat za fiskalizaciju.",
        )
    fiskal_prostor_ids = fields.One2many(
        'fiskal.prostor', 'company_id',
        string="Poslovni prostori",
        help="Poslovni prostori (fiskalizacija).",
        )

    @api.multi
    def _get_fiskal_key_cert(self):
        """ returns production, key and cert file for a company"""
        self.ensure_one()
        production = False
        fina_cert = self.fina_certifikat_id
        if not fina_cert:
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
            return False, False, False
        cert_type = fina_cert.cert_type
        if cert_type not in ('fina_demo', 'fina_prod'):
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
            return False, False, False
        if not (fina_cert.state == 'confirmed'
                and fina_cert.csr and fina_cert.crt):
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
            return False, False, False
        if cert_type == 'fina_prod':
            production = True
        # Key and cert files are stored in subfolder 'odoo_fiskal' relative to
        # odoo config file hoping that os user runing odoo have r/w rights.
        path = os.path.join(
            os.path.dirname(os.path.abspath(odoo_config.rcfile)), 'oe_fiskal')
        if not os.path.exists(path):
            os.mkdir(path, 0777)  # TODO 0660 or less

        key_file = os.path.join(
            path, "{0}_{1}_{2}_key.pem".format(
                self.env.cr.dbname, self.id, fina_cert.id))
        cert_file = os.path.join(
            path, "{0}_{1}_{2}_crt.pem".format(
                self.env.cr.dbname, self.id, fina_cert.id))

        for f_file in (key_file, cert_file):
            if not os.path.exists(f_file):
                with open(f_file, mode='w') as f:
                    content = f_file.endswith(
                        '_key.pem') and fina_cert.csr or fina_cert.crt
                    f.write(content)
                    f.flush()
        return production, key_file, cert_file

    def _zagreb_now(self):
        return datetime.now(timezone('Europe/Zagreb'))

    def _fiskal_time_formated(self):
        tstamp = self._zagreb_now()
        v_date='%02d.%02d.%02d' % (tstamp.day, tstamp.month, tstamp.year)
        v_datum_vrijeme='%02d.%02d.%02dT%02d:%02d:%02d' % (
            tstamp.day, tstamp.month, tstamp.year,
            tstamp.hour, tstamp.minute, tstamp.second)
        v_datum_racun='%02d.%02d.%02d %02d:%02d:%02d' % (
            tstamp.day, tstamp.month, tstamp.year,
            tstamp.hour, tstamp.minute, tstamp.second)
        vrijeme={'datum': v_date,                   # vrijeme SAD
                 'datum_vrijeme': v_datum_vrijeme,  # za zaglavlje XML poruke
                 'datum_racun': v_datum_racun,      # za ispis na računu
                 'time_stamp': tstamp}  # timestamp, za zapis i izračun vremena
        return vrijeme

    @api.multi
    def _log_fiskal(self, msg_type, msg, start_time, odoo_id):
        fiskal_prostor_id = invoice_id = pos_order_id = None
        if msg_type in ('echo'):
            fiskal_prostor_id = odoo_id
        elif msg_type in ('prostor_prijava', 'prostor_odjava', 'PoslovniProstor'):
            fiskal_prostor_id = odoo_id
        elif msg_type in ('racun', 'racun_ponovo', 'Racun'):
            invoice_id = odoo_id
        elif msg_type in ('mp_racun', 'mp_racun_ponovo', 'MP Racun'):
            pos_order_id = odoo_id

        stop_time = self._fiskal_time_formated()
        t_obrada = stop_time['time_stamp'] - start_time['time_stamp']
        time_obr='%s.%s s'%(t_obrada.seconds, t_obrada.microseconds)

        poruka_zahtjev = et.tostring(msg.get_last_request())
        poruka_odgovor = et.tostring(msg.get_last_response())
        greska = msg.get_last_error()
        id_poruke = msg.get_id_msg()  # idPoruke Echo does not have it
        # message datetime Echo request does not have it
        msg_datetime = msg.get_datetime_msg() or datetime.now()

        self.env.cr.execute("""
            INSERT INTO fiskal_log(
                     user_id, create_uid, create_date
                    ,name, type, time_stamp
                    ,sadrzaj, odgovor, greska
                    ,fiskal_prostor_id, invoice_id, pos_order_id, time_obr
                    ,company_id )
            VALUES ( %s, %s, %s,  %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s );
            """, (
            self._uid, self._uid, datetime.now(),
            id_poruke, msg_type, msg_datetime,
            str(poruka_zahtjev), str(poruka_odgovor), str(greska),
            fiskal_prostor_id, invoice_id, pos_order_id, time_obr,
            self.id))


class FiskalProstor(models.Model):
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

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default.update({
            'fiskal_log_ids': False,
            'uredjaj_ids': False,
        })
        return super(FiskalProstor, self).copy(default)

    @api.multi
    def validate(self):
        # TODO:
        # kbr must be numeric
        # posta = zip (numeric)
        return True
    
    @api.model
    def button_test_echo(self):
        echo = fisk.EchoRequest("Proba echo poruke")
        # send request and print server reply
        echo_reply = echo.execute()
        if echo_reply != False:
            raise UserError(str(echo_reply))
        else:
            errors = echo.get_last_error()
            raise UserError(str(errors))

    @api.multi
    def button_prijavi_prostor(self):
        self.posalji_prostor('prostor_prijava')

    @api.multi
    def button_odjavi_prostor(self):
        self.posalji_prostor('prostor_odjava')

    @api.multi
    def posalji_prostor(self, msg_type):
        self.ensure_one()
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

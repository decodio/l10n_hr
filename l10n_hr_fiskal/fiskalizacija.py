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
        """ returns key_file, password, cert_file, production for a company"""
        self.ensure_one()
        fina_cert = self.fina_certifikat_id
        if not fina_cert:
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
        cert_type = fina_cert.cert_type
        if cert_type not in ('fina_demo', 'fina_prod'):
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
        if not (fina_cert.state == 'confirmed'
                and fina_cert.csr and fina_cert.crt):
            raise UserError(_('Error'), _('Neispravne postavke certifikata!'))
        production = (cert_type == 'fina_prod')
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
        password = fina_cert.pfx_certificate_password or None
        # TODO handle key file password in separate field
        return key_file, password, cert_file, production

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
    
    name = fields.Char(
        'Naziv poslovnog prostora',
        select=1)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Tvrtka',
        default=lambda self: self.env['res.company']._company_default_get(
            'fiskal.prostor'),
        required=True)
    oznaka_prostor = fields.Char('Oznaka poslovnog prostora', required=True)
    datum_primjene = fields.Datetime(
        'Datum',
        help="Datum od kojeg vrijede navedeni podaci")
    ulica = fields.Char('Ulica')
    kbr = fields.Char('Kucni broj')
    kbr_dodatak = fields.Char('Dodatak kucnom broju')
    posta = fields.Char('Posta')
    naselje = fields.Char('Naselje')
    opcina = fields.Char('Naziv opcine ili grada', required=True)
    prostor_other = fields.Char(
        'Ostali tipovi adrese',
        help="Ostali tipovi adresa, npr. internet ili pokretna trgovina")
    sustav_pdv = fields.Boolean('U sustavu PDV-a', default=True)
    radno_vrijeme = fields.Char('Radno Vrijeme', required=True)
    sljed_racuna = fields.Selection(
        (('N', 'Na nivou naplatnog uredjaja'),
         ('P', 'Na nivou poslovnog prostora')),
        'Sljed racuna',
        default="P", required=True)
    spec = fields.Char('OIB Informaticke tvrtke', required=True)
    uredjaj_ids = fields.One2many(
        'fiskal.uredjaj',
        'prostor_id',
        'Uredjaji')
    fiskal_log_ids = fields.One2many(
        'fiskal.log',
        'fiskal_prostor_id',
        'Logovi poruka',
        help="Logovi poslanih poruka prema poreznoj upravi")
    state = fields.Selection(
        (('draft', 'Upis'),
         ('active', 'Aktivan'),
         ('closed', 'Zatvoren')),
        'Status zatvaranja')

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
        if (self.prostor_other and self.ulica):
            raise UserError(
                _('Greška: Dupla adresa'),
                _('Nije moguće prijaviti dva tipa adrese za jedan poslovni prostor!'))
        elif not (self.prostor_other or self.ulica):
            raise UserError(
                _('Greška: Nema adrese'),
                _('Unesite adresne podatke ili opisnu adresu prostora!'))

        key, password, cert, production = self.company_id._get_fiskal_key_cert()
        if not key:
            return False
        # TODO: test with 2 different companies at the same time
        fisk.FiskInit.init(key, password, cert, production=production)
        adresa = fisk.Adresa(
            data={"Ulica": self.ulica or '',
                  "KucniBroj": self.kbr or '',
                  "Opcina": self.opcina or '',
                  })
        if self.kbr_dodatak:
            adresa.KucniBrojDodatak = self.kbr_dodatak
        if self.naselje:
            adresa.Naselje = self.naselje
        if self.posta:
            adresa.BrojPoste = self.posta
        pp = fisk.PoslovniProstor(
            data={"Oib": self.company_id.partner_id.vat[2:] or False,
                  "OznPoslProstora": self.oznaka_prostor or '',
                  "AdresniPodatak": fisk.AdresniPodatak(
                      self.prostor_other or adresa),
                  "RadnoVrijeme": self.radno_vrijeme or '',
                  "DatumPocetkaPrimjene":
                      self.company_id._fiskal_time_formated().get('datum'),
                  # OIB IT firme Mora odgovarati OIB-u sa Cert-a
                  "SpecNamj": self.spec and self.spec[2:] or False,
                  })
        if msg_type == 'prostor_odjava':
            pp.OznakaZatvaranja = 'Z'
        if self.company_id.fina_certifikat_id.cert_type == 'fina_prod':
            pp.Oib = self.company_id.partner_id.vat[2:]  # pravi OIB company
        elif self.company_id.fina_certifikat_id.cert_type == 'fina_demo':
            # OIB IT firme Mora odgovarati OIB-u sa Cert-a
            pp.Oib = self.spec and self.spec[2:] or False
        ppz = fisk.PoslovniProstorZahtjev(pp)  # poslovni prostor request
        start_time = self.company_id._fiskal_time_formated()
        ppz_reply = ppz.execute()
        if ppz_reply:
            self.write({'datum_primjene': fields.Datetime.now() })
        self.company_id._log_fiskal(msg_type, ppz, start_time, self.id)
        # fiskpy deinit - maybe not needed but good for correct garbage cleaning
        fisk.FiskInit.deinit()
        #fiskal.deinit()
        return ppz_reply


class FiskalUredjaj(models.Model):
    _name = 'fiskal.uredjaj'
    _description = 'Podaci o poslovnim prostorima za potrebe fiskalizacije'

    @api.multi
    def name_get(self):
        result = []
        for u in self:
            result.append(
                (u.id, ' / '.join((u.prostor_id.name or '', u.name or ''))))
        return result

    name = fields.Char(
        'Naziv naplatnog uredjaja',
        select=1)
    prostor_id = fields.Many2one(
        'fiskal.prostor',
        'Prostor',
        help='Prostor naplatnog uredjaja.')
    oznaka_uredjaj = fields.Integer(
        'Oznaka naplatnog uredjaja',
        required=True)


class FiskalLog(models.Model):
    _name = 'fiskal.log'
    _description = 'Fiskal log'
    
    def _get_log_type(self):
        return (('prostor_prijava', 'Prijava prostora'),
                ('prostor_odjava', 'Odjava prostora'),
                ('racun', 'Fiskalizacija racuna'),
                ('racun_ponovo', 'Ponovljeno slanje racuna'),
                ('echo', 'Echo test poruka '),
                ('other', 'Other types'))

    name = fields.Char(
        'Oznaka',
        help="Jedinstvena oznaka komunikacije",
        readonly=True)
    type = fields.Selection(
        _get_log_type,
        'Vrsta poruke',
        readonly=True)
    invoice_id = fields.Many2one(
        'account.invoice',
        'Racun',
        readonly=True,
        select=True)
    fiskal_prostor_id = fields.Many2one(
        'fiskal.prostor',
        'Prostor',
        readonly=True)
    sadrzaj = fields.Text(
        'Poslana poruka',
        readonly=True)
    odgovor = fields.Text(
        'Odgovor',
        readonly=True)
    greska = fields.Text(
        'Greska',
        readonly=True)
    time_stamp = fields.Datetime(
        'Vrijeme',
        readonly=True)
    time_obr = fields.Char(
        'Vrijeme obrade',
        help='Vrijeme obrade podataka',
        readonly=True) #vrijeme obrade prmljeno_vrijeme-poslano_vrijem
    user_id = fields.Many2one(
        'res.users',
        'Osoba',
        readonly=True)
    company_id = fields.Many2one(
        'res.company',
        'Tvrtka',
        required=False)
    pos_order_id = fields.Integer(
        'MP Racun',
        readonly=True)

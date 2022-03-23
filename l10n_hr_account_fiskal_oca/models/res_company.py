# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import os
from ..fiskal.fiskal import Fiskalizacija
from odoo import api, fields, models, _
from odoo.exceptions import MissingError, ValidationError


SCHEMA_HELP = """
verzija: 1.3 Datum verzije: 04.07.2016.
- u WSDL-u dodana nova metoda 'provjera'
- u schemi dodani novi elementi 'ProvjeraZahtjev' i 'ProvjeraOdgovor' 

verzija: 1.4 Datum verzije: 27.04.2017.
- u WSDL-u izbačena metoda 'poslovniProstor'
-u schemi izbačeni elementi 'PoslovniProstorZahtjev', 
   'PoslovniProstorOdgovor'i ostalo vezano za prijavu poslovnih prostora 

verzija: 1.5 Datum verzije: 20.12.2019.
- u WSDL-u dodane dvije metode 'prateciDokumenti' i 'racuniPD'
- u schemi dodani elementi 'PrateciDokumentiZahtjev', 
   'PrateciDokumentiOdgovor', 'RacunPDZahtjev', 
   'RacunPDOdgovor' i ostalo vezano za nove elemente. 

"""


class Company(models.Model):
    _inherit = 'res.company'

    @staticmethod
    def _get_fiskal_path():
        file_path = os.path.dirname(os.path.realpath(__file__))
        fiskal_path = file_path.replace('models', 'fiskal/')
        return fiskal_path

    @api.model
    def _get_schema_selection(self):
        fiskal_path = self._get_fiskal_path()
        fiskal_path += 'schema'
        res = [(s,s) for s in os.listdir(fiskal_path)]
        return res


    fiskal_cert_id = fields.Many2one('crypto.certificate',
        string="Certifikat za fiskalizaciju",
        domain="[('state', '=', 'confirmed')]")

    # TODO : check for OIB in cert, production must match company vat,
    #        demo should match spec or company vat...
    #        no others should be allowed!
    fiskal_spec = fields.Char(
        string='Specijalno', size=1000,
        help="OIB informatičke tvrtke koja održava software, "
             "za demo cert mora odgovarati OIBu sa demo certifikata",
        )
    fiskal_schema = fields.Selection(
        selection=_get_schema_selection,
        string="Fiskalizaction schema",
        help=SCHEMA_HELP
    )

    @api.onchange('fiskal_cert_id')
    def onchange_fiskal_cert(self):
        """
        Maybe put this in field domain later...
        """
        # DB: maybe also:
        # if 'Fiskal' not in self.fiskal_cert_id.usage:
        # but, strict for now...
        if self.fiskal_cert_id.usage not in [
                'Fiskal_DEMO_V1', 'Fiskal_PROD_V1',
                'Fiskal_DEMO_V2', 'Fiskal_PROD_V2',
                'Fiskal_DEMO_V3', 'Fiskal_PROD_V3']:
            self.fiskal_cert_id = False  # DB: just empty value, no raise...
            # raise ValidationError(_('Selected certificate is not intended for fiscalization purposes!'))

    def _get_log_vals(self, msg_type, msg_obj, response, time_start):
        """
        Inherit in other modules with proper super to add values
        """
        time_stop = self.get_l10n_hr_time_formatted()
        t_obrada = time_stop['time_stamp'] - time_start['time_stamp']
        time_obr = '%s.%s s' % (t_obrada.seconds, t_obrada.microseconds)

        values = {
            'user_id': self._uid,
            'name': msg_type != 'echo' and
                    response.Zaglavlje.IdPoruke or 'ECHO',
            'type': msg_type,
            'time_stamp': msg_type != 'echo' and
                          response.Zaglavlje.DatumVrijeme or
                          time_stop['datum_vrijeme'],
            'time_obr': time_obr,
            'sadrzaj': msg_obj.log.sending_log.decode(),
            'odgovor': msg_obj.log.received_log.decode(),
            'greska': msg_type != 'echo' and
                      hasattr(response, 'Greske') and
                      response.Greske[0][0].PorukaGreske or 'OK',
            'fiskal_prostor_id': msg_obj.odoo_object._name == 'account.invoice'
                     and msg_obj.odoo_object.fiskal_uredjaj_id.prostor_id.id or
                     False,
            'invoice_id': msg_obj.odoo_object._name == 'account.invoice' and
                          msg_obj.odoo_object.id or False,
            'company_id': self.id
        }
        return values

    def create_fiskal_log(self, msg_type, msg_obj, response, time_start):
        """
        borrow and SMOP rewrite from decodio
        """
        log_vals = self._get_log_vals(msg_type, msg_obj, response, time_start)
        self.env['fiskal.log'].create(log_vals)

    def button_test_echo(self):
        fd = self.get_fiskal_data()
        fisk = Fiskalizacija(
            fiskal_data=fd, odoo_object=self
        )
        time_start = self.get_l10n_hr_time_formatted()
        msg = 'TEST message'
        echo = fisk.send('echo', msg)
        self.create_fiskal_log('echo', fisk, echo, time_start)
        if echo != msg:
            # i commit created log! then raise!
            self.env.cr.commit()
            raise ValidationError(
                "ECHO failed with : " + fisk.log.received_log
            )


    def get_fiskal_data(self):
        fina_cert = self.fiskal_cert_id
        if not fina_cert:
            raise MissingError('Cerificate not found! Check company setup!')
        key_file, cert_file, production = fina_cert.get_fiskal_ssl_data()

        fiskal_path = self._get_fiskal_path()
        schema = 'file://' + fiskal_path + 'schema/' + self.fiskal_schema
        wsdl_file = schema + '/wsdl/FiskalizacijaService.wsdl'

        ca_path, cis_ca_list = None, []
        cert_path = fiskal_path + '/fina_cert'
        for fcert in os.listdir(cert_path):
            if not production and 'Demo' in fcert or \
                production and 'Demo' not in fcert:
                fpath = os.path.join(cert_path, fcert)
                if 'Chain' in fcert:
                    ca_path = fpath
                else:
                    cis_ca_list.append(fpath)

        res = {
            'wsdl': wsdl_file,
            'key': key_file,
            'cert': cert_file,
            'ca_list': cis_ca_list,
            'ca_path': ca_path,
            'url': 'fiskalcis' if production else 'fiskalcistest',
            'test': not production
        }
        return res
        # return wsdl_file, key_file, cert_file, cis_ca_list, ca_path, production


class FiskalProstor(models.Model):
    _inherit = 'fiskal.prostor'

    fiskal_log_ids = fields.One2many(
        comodel_name='fiskal.log',
        inverse_name='fiskal_prostor_id',
        string='Logovi poruka',
        help="Logovi poslanih poruka prema poreznoj upravi")
    # FIELDS legacy for wsdl 1.0 - 1.2
    # datum_primjene = fields.Datetime(
    #     string='Datum',
    #     help="Datum od kojeg vrijede navedeni podaci")
    # radno_vrijeme = fields.Char(
    #     string='Radno Vrijeme',
    #     required="True",
    #     size=1000, # strictly defined!
    #     default="8-20 pon-pet, 8-14 sub")
    # ulica = fields.Char(string='Ulica', size=100)
    # kbr = fields.Char(string='Kućni broj', size=4)
    # kbr_dodatak = fields.Char(string='Dodatak kućnom broju', size=4)
    # posta = fields.Char(string='Pošta', size=12)
    # naselje = fields.Char(string='Naselje', size=35)
    # opcina = fields.Char(string='Naziv općine ili grada', size=35)
    # prostor_ostalo = fields.Char(
    #     string='Ostali tipovi adrese',
    #     size=100,
    #     help="Ostali tipovi adresa, npr internet trgovina ili pokretna trgovina")


class FiskalLog(models.Model):
    _name = 'fiskal.log'
    _description = 'Fiskal messages log'

    name = fields.Char(
        string='Oznaka',
        size=64, readonly=True,
        help="Unique communication mark")
    type = fields.Selection(
        selection=[
            ('racun', 'Fiskalizacija racuna'),
            ('rac_pon', 'Ponovljeno slanje racuna'),
            ('rac_prov', 'Provjera fiskalizacije računa'),  # NOVO!
            ('pd', 'Fiskalizacija prateceg dokumenta'),
            ('pd_rac', 'Fiskalizacija računa za prateći dokument'),
            ('echo', 'Test poruka '),
            ('other', 'Other types')],
        string='Message type',
        readonly=True)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice', readonly=True)
    fiskal_prostor_id = fields.Many2one(
        comodel_name='fiskal.prostor',
        string='Office', readonly=True)
    sadrzaj = fields.Text(string='Sent message', readonly=True)
    odgovor = fields.Text(string='Reply', readonly=True)
    greska = fields.Text(string='Error', readonly=True)
    time_stamp = fields.Char(string='TimeStamp odgovora', readonly=True)
    time_obr = fields.Char(string='Vrijeme obrade', readonly=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Person',
        readonly=True,
        on_delete='restrict')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True)
#

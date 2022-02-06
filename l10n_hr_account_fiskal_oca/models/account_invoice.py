# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


from ..fiskal import fiskal
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class FiscalPrateciDokumentMixin(models.AbstractModel):
    """
    Basic fields and methods for all fiscal classes
    - inherit for invoice, sale, procurment etc...
    """
    _name = 'fiscal.mixin'
    _description = 'Fiscalisation base mixin'

    zki = fields.Char(
        string='ZKI',
        readonly=True, copy=False)
    jir = fields.Char(
        string='JIR',
        readonly=True, copy=False)


class FiscalInvoiceMixin(models.AbstractModel):
    _inherit = 'fiscal.mixin'
    _name = "fiscal.invoice.mixin"
    _description = 'Mixin for pos or account invoice'

    vrijeme_xml = fields.Char(
        string="XML vrijeme računa",
        help="Value from fiscalization msg stored as string",
        size=19, readonly=True, copy=False)

    # fiskal_user_id = fields.Many2one( # -> moved to l10n-hr_account_oca!!
    #     comodel_name='res.users',
    #     string='Fiskalizirao',
    #     help='Fiskalizacija. Osoba koja je potvrdila racun',
    #     copy=False)
    # zki = fields.Char(
    #     string='ZKI',
    #     readonly=True, copy=False)
    # jir = fields.Char(
    #     string='JIR',
    #     readonly=True, copy=False)
    paragon_br_rac = fields.Char(
        'Paragon br.',
        readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Paragon broj racuna, ako je racun izdan na paragon. "
             "Potrebno upisati prije potvrđivanja računa")

    def _check_fiskal_invoice_data(self):
        """
        Check for all required elements and permissions
        :return: fiskal number parts
        """
        if not self.journal_id.fiscalisation_active:
            raise UserError(
                _('Fiscalization is not active for this document!!'))
        if not self.fiskal_user_id.partner_id.vat:
            raise UserError(
                _('User OIB is not not entered! It is required'))
        if not self.company_id.fiskal_cert_id:
            raise UserError(
                _('No fiscal certificate found, please install one '
                  'activate and select it on company setup!'))
        # assuming we have validated invoice and have fiskal number present!
        #return self.fiskalni_broj.split(self.company_id.fiskal_separator)
        # return True

    def _prepare_fisk_racun_taxes(self, racun, factory):

        tax_data = {
            "Pdv": {},
            "Pnp": {},
            "OstaliPor": [],
            "Naknade": [],
        }
        iznos_oslob_pdv, iznos_ne_podl_opor, iznos_marza = 0.00, 0.00, 0.00
        for tax in self.tax_line_ids:
            # TODO: taxex with 0 percent have no tax line !!!
            # for now, let's assume we have tax lines with amount zero!
            if not tax.tax_id.hr_fiskal_type:
                raise ValidationError(_("Tax '%s' missing fiskal type!" % tax.tax_id.name))

            fiskal_type = tax.tax_id.hr_fiskal_type

            naziv = tax.tax_id.name
            stopa = tax.tax_id.amount
            osnovica = tax.base
            iznos = tax.amount

            if fiskal_type == 'Pdv':
                if tax_data['Pdv'].get(stopa):
                    tax_data['Pdv'][stopa]['Osnovica'] += osnovica
                    tax_data['Pdv'][stopa]['Iznos'] += iznos
                else:
                    tax_data['Pdv'][stopa] = {
                        'Osnovica': osnovica,
                        'Iznos': iznos
                    }
            elif fiskal_type == 'Pnp':
                if tax_data['Pnp'].get(stopa):
                    tax_data['Pnp'][stopa]['Osnovica'] += osnovica
                    tax_data['Pnp'][stopa]['Iznos'] += iznos
                else:
                    tax_data['Pnp'][stopa] = {
                        'Osnovica': osnovica,
                        'Iznos': iznos
                    }

            elif fiskal_type == 'OstaliPor':
                tax_data['OstaliPor'].append({
                    "Naziv": naziv, "Stopa": stopa,
                    "Osnovica": osnovica, "Iznos": iznos})
            elif fiskal_type == 'Naknade':
                tax_data['Naknade'].append({
                    "NazivN": naziv, "IznosN": iznos})

            elif fiskal_type == 'oslobodenje':
                iznos_oslob_pdv += tax.base
            elif fiskal_type == 'ne_podlijeze':
                iznos_ne_podl_opor += tax.base
            elif fiskal_type == 'marza':
                iznos_marza += tax.base

        for pdv in tax_data['Pdv']:
            _pdv = tax_data['Pdv'][pdv]
            porez = factory.create('Porez')
            porez.__delattr__('Naziv')
            porez.Stopa = fiskal.format_decimal(pdv)
            porez.Osnovica = fiskal.format_decimal(_pdv['Osnovica'])
            porez.Iznos = fiskal.format_decimal(_pdv['Iznos'])
            racun.Pdv.Porez.append(porez)

        for pnp in tax_data['Pnp']:
            _pnp = tax_data['Pnp'][pnp]
            porez = factory.create('Porez')
            porez.Stopa = fiskal.format_decimal(pnp)
            porez.Osnovica = fiskal.format_decimal(_pnp['Osnovica'])
            porez.Iznos = fiskal.format_decimal(_pnp['Iznos'])
            racun.Pnp.Porez.append(porez)

        for ost in tax_data['OstaliPor']:
            _ost = tax_data['OstaliPor'][ost]
            porez = factory.create('Porez')
            porez.Naziv = _ost['Naziv']
            porez.Stopa = fiskal.format_decimal(ost)
            porez.Osnovica = fiskal.format_decimal(_ost['Osnovica'])
            porez.Iznos = fiskal.format_decimal(_pnp['Iznos'])
            racun.OstaliPor.Porez.append(porez)

        if iznos_oslob_pdv:
            racun.IznosOslobPdv = fiskal.format_decimal(iznos_oslob_pdv)
        if iznos_ne_podl_opor:
            racun.IznosNePodlOpor = fiskal.format_decimal(iznos_ne_podl_opor)
        if iznos_marza:
            racun.IznosMarza = fiskal.format_decimal(iznos_marza)

        for nak in tax_data['Naknade']:
            naziv, iznos = nak
            naknada = factory.create('Naknada')
            naknada.NazivN = naziv
            naknada.IznosN = fiskal.format_decimal(iznos)
            racun.Naknade.append(naknada)
        return racun

    def _prepare_fisk_racun(self, factory, fiskal_data):
        racun = factory.create('Racun')

        # 1. get company OIB
        if not fiskal_data.get('test', False):
            oib = self.company_id.partner_id.get_oib()  # pravi OIB
        else:
            # TODO: on convert write oib from cert to SPEC field!
            oib = self.company_id.fiskal_spec  # OIB IT firme, tj.. oib iz certa!
            if oib.startswith('HR'):
                oib = oib[2:]

        racun.Oib = oib

        nak_dost = False
        dat_vrijeme = self.vrijeme_izdavanja
        if dat_vrijeme:
            dat_vrijeme = dat_vrijeme.replace(' ', 'T')
            if dat_vrijeme != fiskal_data['time']['datum_vrijeme']:
                # PAŽLJIVO SA OVIM!!! potrebno testirati slučajeve!!!
                nak_dost = True
        else:
            self.vrijeme_izdavanja = fiskal_data['time']['datum_racun']
            dat_vrijeme = fiskal_data['time']['datum_vrijeme']
        racun.DatVrijeme = dat_vrijeme
        racun.OznSlijed = self.fiskal_uredjaj_id.prostor_id.sljed_racuna

        #br_rac = self.fiskalni_broj.split(self.company_id.fiskal_separator)

        racun.IznosUkupno = fiskal.format_decimal(self.amount_total)
        racun.NacinPlac = self.nacin_placanja
        racun.OibOper = self.fiskal_user_id.partner_id.get_oib()
        racun.NakDost = nak_dost
        racun.ZastKod = self.zki

        if self.paragon_br_rac:
            racun.ParagonBrRac = str(self.paragon_br_rac)

        racun.USustPdv = True  # TODO: setup na company! l10n_hr_base
        if racun.USustPdv:
            # LELLEEE ovo nije dobro..
            # mozda nisam u sustavu pdv-a ali imam naknade ili Pnp???
            # treba razmisliti što ćemo sa ovima koji nisu u sustavu pdv-a!!!
            racun = self._prepare_fisk_racun_taxes(racun, factory)
        return racun

    def fiskaliziraj(self, msg_type='racuni'):
        """
        Fiskalizira jedan izlazni racun ili point of sale račun
        msg_type : Racun,

        """
        if self.jir and len(self.jir) > 30:
            if msg_type != 'provjera':
                msg_type = 'provjera'
            # return False  # vec je prosao fiskalizaciju

        time_start = self.company_id.get_l10n_hr_time_formatted()
        if not self.fiskal_user_id:
            # MUST USE CURRENT user for fiscalization!
            # Except in case of paragon račun? or naknadna dostava?
            self.fiskal_user_id = self._uid
        self._check_fiskal_invoice_data()
        fiskal_data = self.company_id.get_fiskal_data()
        fiskal_data['time'] = time_start
        fis_racun = self.fiskalni_broj.split(self.company_id.fiskal_separator)
        assert len(fis_racun) == 3, "Invoice must be assembled using 3 values!"
        if not self.zki:
            # ZKI JE UVJEK ISTI
            # generiram ga samo ako već ne postoji
            # OVO je samo za racun,
            # treba posebna metoda za PrateciDokument
            zki_datalist = [
                self.company_id.partner_id.get_oib(),
                self.vrijeme_izdavanja or time_start['datum_racun'],
                fis_racun[0],
                fis_racun[1],
                fis_racun[2],
                fiskal.format_decimal(self.amount_total)
                ]
            self.zki = fiskal.generate_zki(
                zki_datalist=zki_datalist,
                key_str=self.company_id.fiskal_cert_id.csr
            )
        fisk = fiskal.Fiskalizacija(fiskal_data=fiskal_data, odoo_object=self)
        if msg_type in ['racuni', 'provjera']:
            racun = self._prepare_fisk_racun(
                factory=fisk, fiskal_data=fiskal_data)

            racun.BrRac.BrOznRac = fis_racun[0]
            racun.BrRac.OznPosPr = fis_racun[1]
            racun.BrRac.OznNapUr = fis_racun[2]
            response = fisk.send(msg_type, racun, raw_response=True)

        self.company_id.create_fiskal_log(msg_type, fisk, response, time_start)
        if hasattr(response, 'Jir'):
            if not self.jir:
                self.jir = response.Jir
            else:
                pass

    def check_fiskalizacija(self):
        pass


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = ["account.invoice", "fiscal.invoice.mixin"]

    # FIELDS
    nacin_placanja = fields.Selection(
        selection_add=[
            ('G', 'GOTOVINA'),
            ('K', 'KARTICE'),
            ('C', 'ČEKOVI'),
            ('O', 'OSTALO')])
    fiskal_log_ids = fields.One2many(
        comodel_name='fiskal.log',
        inverse_name='invoice_id',
        string="Fiscal messages log", copy=False)
    fiscalisation_active = fields.Boolean(
        help="Technical field user for show/hide tab in view"
    )
    prateci_doc_ids = fields.One2many(
        comodel_name='account.invoice.fiscal.pd',
        inverse_name='invoice_id',
        string="Related fiscal documents"
    )

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.fiscalisation_active = self.journal_id.fiscalisation_active
        else:
            self.fiscalisation_active = False

    def button_fiskaliziraj(self):
        self.ensure_one()
        if not self.jir:
            self.fiskaliziraj()
        # TODO: nova shema ima metodu provjere da li je racun fiskaliziran!
        elif len(self.jir) >= 32:  # BOLE: JIR je 32+ znaka !
            #res = self.fiskaliziraj('provjera') # samo WSDL 1.4 ovog nema u 1.5 ?!
            raise UserError('Nema potrebe ponavljati postupak fiskalizacije!')

    def button_check_zki(self):
        self.ensure_one()
        zki_obj = self.env['fiskal.zastitni.kod']
        fisk_br = self.fiskalni_broj
        if '/' in fisk_br:
            fisk_br = fisk_br.split('/')[0]
        elif '-' in fisk_br:
            fisk_br = fisk_br.split('-')[0]
        try:
            test = int(fisk_br)
        except Exception as E:
            test = False
            fisk_br = False
        defaults = {
            'company_id': self.company_id.id,
            'cert_id': self.company_id.fiskal_cert_id.id,
            'oib': self.company_id.partner_id.vat,
            'br_racuna': fisk_br,
            'ukupan_iznos': self.amount_total,
            'datum_vrijeme': self.vrijeme_izdavanja and
                        self.vrijeme_izdavanja or
                        self.company_id.get_l10n_hr_time_formatted().get['datum_vrijeme'],
            'oznaka_pp': self.fiskal_uredjaj_id and
                         self.fiskal_uredjaj_id.prostor_id.oznaka_prostor or False,
            'oznaka_nu': self.fiskal_uredjaj_id and
                         self.fiskal_uredjaj_id.oznaka_uredjaj or False,
            'fiskalni_broj_racuna': self.fiskalni_broj,
            'zki_check': self.zki

        }
        res_id = zki_obj.create(defaults)
        view_id = self.env.ref('l10n_hr_account_fiskal_oca.wizard_zastitni_kod')
        return {
            'name': 'ZKI',
            'res_model': 'fiskal.zastitni.kod',
            'res_id': res_id.id,
            'view_id': view_id.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
        }


class AccountInvoicePD(models.Model):
    _inehrit = 'fiscal.mixin'
    _name = 'account.invoice.fiscal.pd'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
    )
    pd_model = fields.Selection(
        selection=[('none', 'None')],
        string="PD Model", help="Model for related document"
    )
    pd_model_id = fields.Integer()

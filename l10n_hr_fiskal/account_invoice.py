# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from datetime import datetime
from pytz import timezone, UTC

try:
    import fisk
except ImportError:
    fisk = None


class FiscalInvoiceMixin(models.AbstractModel):
    _name = "fiscal.invoice.mixin"

    # common fiscal attributes for account.invoice and pos.order
    vrijeme_izdavanja = fields.Datetime("Vrijeme", readonly=True)
    fiskal_user_id = fields.Many2one(
        'res.users',
        'Fiskalizirao',
        help='Fiskalizacija. Osoba koja je potvrdila racun')
    zki = fields.Char('ZKI', readonly=True)
    jir = fields.Char('JIR', readonly=True)
    uredjaj_id = fields.Many2one(
        'fiskal.uredjaj',
        'Naplatni uredjaj',
        help="Naplatni uređaj na kojem se izdaje racun",
        readonly=True,
        states={'draft': [('readonly', False)]})
    fiskal_log_ids = fields.One2many(
        'fiskal.log',
        'invoice_id',
        'Logovi poruka',
        help="Logovi poslanih poruka prema poreznoj upravi")
    nac_plac = fields.Selection(
        (('G', 'GOTOVINA'),
         ('K', 'KARTICE'),
         ('C', 'CEKOVI'),
         ('T', 'TRANSAKCIJSKI RACUN'),
         ('O', 'OSTALO')
         ),
        'Nacin placanja',
        readonly=True,
        # required=True, default='G', # TODO : kaj da bude default!
        states={'draft': [('readonly', False)]})
    paragon_br_rac = fields.Char(
        'Paragon br.',
        help="Paragon broj racuna, ako je racun izdan na paragon.")

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default.update({
            'vrijeme_izdavanja': False,
            'fiskal_user_id': False,
            'zki': False,
            'jir': False,
            'fiskal_log_ids': False,
        })
        return super(FiscalInvoiceMixin, self).copy(default)

    @api.multi
    def _fiskal_invoice_valid(self):
        self.ensure_one()
        if not self.journal_id.fiskal_active:
            raise UserError(_('Error'),
                            _('Za ovaj dokument fiskalizacija nije aktivna!!'))
        if not self.fiskal_user_id.oib:
            raise UserError(_('Error'),
                            _('Neispravan OIB korisnika!'))
        if not self.uredjaj_id.id:
            raise UserError(_('Error'),
                            _('Nije odabran naplatni uredjaj / Dokument !'))
        return True

    @api.multi
    def _prepare_fisk_racun_taxes(self):
        self.ensure_one()

        def fiskal_num2str(num):
            return "{:-.2f}".format(num)

        tax_data = {
            "Pdv": [],
            "Pnp": [],
            "OstaliPor": [],
            "Naknade": [],
        }
        iznos_oslob_pdv = iznos_ne_podl_opor = iznos_marza = 0.00
        for tax in self.tax_line:
            # TODO: special cases without tax code,
            # or with base tax code without tax if found
            if not tax.tax_code_id:
                continue  # or raise exception?
            tax_code = tax.tax_code_id
            fiskal_type = str(tax_code.fiskal_type)
            naziv = str(tax_code.name)
            stopa = str(tax_code.fiskal_percent)
            osnovica = fiskal_num2str(tax.base_amount)
            iznos = fiskal_num2str(tax.tax_amount)
            if fiskal_type == 'pdv':
                tax_data['Pdv'].append(fisk.Porez({
                    "Stopa": stopa, "Osnovica": osnovica, "Iznos": iznos}))
            elif fiskal_type == 'Pnp':
                tax_data['Pnp'].append(fisk.Porez({
                    "Stopa": stopa, "Osnovica": osnovica, "Iznos": iznos}))
            elif fiskal_type == 'ostali':
                tax_data['OstaliPor'].append(fisk.OstPorez({
                    "Naziv": naziv,
                    "Stopa": stopa, "Osnovica": osnovica, "Iznos": iznos}))
            elif fiskal_type == 'naknade':
                tax_data['Naknade'].append(fisk.Naknada({
                    "NazivN": naziv, "IznosN": iznos}))

            elif fiskal_type == 'oslobodenje':
                iznos_oslob_pdv += tax.base_amount
            elif fiskal_type == 'ne_podlijeze':
                iznos_ne_podl_opor += tax.base_amount
            elif fiskal_type == 'marza':
                iznos_marza += tax.base_amount

        for l in ["Pdv", "Pnp", "OstaliPor", "Naknade"]:
            if not tax_data[l]:
                del tax_data[l]
        if iznos_oslob_pdv:
            tax_data['IznosOslobPdv'] = fiskal_num2str(iznos_oslob_pdv)
        if iznos_ne_podl_opor:
            tax_data['IznosNePodlOpor'] = fiskal_num2str(iznos_ne_podl_opor)
        if iznos_marza:
            tax_data['IznosMarza'] = fiskal_num2str(iznos_marza)

        # TODO group and sum by fiskal_type and Stopa hmmm
        # then send 1 by one into factory...
        return tax_data

    @api.multi
    def _prepare_fisk_racun(self):
        self.ensure_one()

        def fiskal_num2str(num):
            return "{:-.2f}".format(num)

        if self.company_id.fina_certifikat_id.cert_type == 'fina_prod':
            oib = self.company_id.partner_id.vat[2:]  # pravi OIB
        else:  # 'fina_demo'
            oib = self.uredjaj_id.prostor_id.spec[2:]  # OIB IT firme
        # dat_vrijeme   invoice.vrijeme_izdavanja
        start_time = self.company_id._fiskal_time_formated()
        dat_vrijeme = self.vrijeme_izdavanja
        if not dat_vrijeme:
            dat_vrijeme = start_time['datum_vrijeme']
            # convert zagreb time to UTC
            utc_time_stamp = start_time['time_stamp'].astimezone(UTC)
            # write UTC time to database bypassing ORM
            doc_table = self._table
            self._cr.execute("""
                update %s set
                       vrijeme_izdavanja = %s where id=%s
                """, (
                doc_table,
                utc_time_stamp.strftime('%Y-%m-%d %H:%M:%S'), self.id))
        else:
            t_stamp = datetime.strptime(dat_vrijeme, '%Y-%m-%d %H:%M:%S')
            t_stamp = timezone('UTC').localize(t_stamp).astimezone(
                timezone('Europe/Zagreb'))
            dat_vrijeme = '%02d.%02d.%02dT%02d:%02d:%02d' % (
                t_stamp.day, t_stamp.month, t_stamp.year,
                t_stamp.hour, t_stamp.minute, t_stamp.second)

        iznos_ukupno = fiskal_num2str(self.amount_total)
        if 'lcy_amount_total' in self._fields:
            iznos_ukupno = fiskal_num2str(self.lcy_amount_total)
        if 'amount_total_company_signed' in self._fields:  # v10
            iznos_ukupno = fiskal_num2str(self.amount_total_company_signed)

        # dijelovi broja racuna
        if self.company_id.separator:
            # ako koristimo drugi separator vratiti broj separiran sa '/'
            # (mijenja zadnja dva separatora)
            separator = str(self.company_id.separator)
            invoice_number = str(self.number)[::-1].replace(
                separator[::-1], "/"[::-1], 2)[::-1]
            b_ozn_rac, ozn_pos_pr, ozn_nap_ur = invoice_number.rsplit('/', 2)
        else:
            b_ozn_rac, ozn_pos_pr, ozn_nap_ur = self.number.rsplit('/', 2)
        br_ozn_rac = ''
        for b in ''.join([x for x in b_ozn_rac[::-1]]):  # reverse
            if b.isdigit():
                br_ozn_rac += b
            else:
                break  # break on 1. non digit
        # reverse again and strip leading zeros
        br_ozn_rac = br_ozn_rac[::-1].lstrip('0')
        br_rac = fisk.BrRac(data={
            "BrOznRac": str(br_ozn_rac),
            "OznPosPr": str(ozn_pos_pr),
            "OznNapUr": str(ozn_nap_ur)}),
        prostor = self.uredjaj_id.prostor_id
        data = {
            "Oib": str(oib),
            "DatVrijeme": dat_vrijeme,
            "OznSlijed": str(prostor.sljed_racuna),  # 'P'/'N'
            "USustPdv": prostor.sustav_pdv and "true" or "false",  # string!
            "NacinPlac": str(self.nac_plac),
            "OibOper": str(self.fiskal_user_id.oib[2:]),  # "12345678901"
            "IznosUkupno": iznos_ukupno,
            "BrRac": br_rac[0],  # get 1. element of tupe
            # ?"SpecNamj": "Tekst specijalne namjene",
            "NakDost": "false",
        }
        if self.paragon_br_rac:
            data['ParagonBrRac'] = str(self.paragon_br_rac)

        if prostor.sustav_pdv:
            tax_data = self._prepare_fisk_racun_taxes()
            data.update(tax_data)  # adds tax_data to data dict

        # TODO rutina koja provjerava jel prvi puta ili ponovljeno slanje!
        # Što ako se promijenio zki, a račun je isprintan i predat kupcu?
        if self.zki:
            data['NakDost'] = "true"
        return fisk.Racun(data=data)

    @api.multi
    def fiskaliziraj(self, msg_type='racun'):
        """ Fiskalizira jedan izlazni racun ili point of sale račun
        """
        self.ensure_one()
        if self.jir and len(self.jir) > 30:
            return False  # vec je prosao fiskalizaciju
        if not self.fiskal_user_id:  # tko pokusava fiskalizirati?
            self.fiskal_user_id = self._uid
        self._fiskal_invoice_valid()  # provjeri sve podatke
        key, password, cert, production = self.company_id._get_fiskal_key_cert()
        if not key:
            return False
        fisk.FiskInit.init(key, password, cert, production=production)
        racun = self._prepare_fisk_racun()  # TODO try/except
        # TODO rutina koja provjerava jel prvi puta ili ponovljeno slanje!
        # Što ako se promijenio zki, a račun je isprintan i predat kupcu?
        self.zki = racun.ZastKod  # Zastitni kod is calculated so write it
        racun_zahtjev = fisk.RacunZahtjev(racun)  # create Request
        start_time = self.company_id._fiskal_time_formated()
        racun_reply = racun_zahtjev.execute()  # send Request # TODO try/except
        if racun_reply:
            self.jir = racun_reply  # write JIR
        else:
            cert_type = self.company_id.fina_certifikat_id.cert_type
            self.jir = 'PONOVITI SLANJE! ' + cert_type
        self.company_id._log_fiskal(
            msg_type, racun_zahtjev, start_time, self.id)
        # fiskpy deinit - maybe not needed but good for garbage cleaning
        fisk.FiskInit.deinit()
        return True


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = ["account.invoice", "fiscal.invoice.mixin"]

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default.update({
            'vrijeme_izdavanja': False,
            'fiskal_user_id': False,
            'zki': False,
            'jir': False,
            'fiskal_log_ids': False,
        })
        return super(AccountInvoice, self).copy(default)

    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        result = super(AccountInvoice, self).onchange_journal_id(
            cr, uid, ids, journal_id=journal_id, context=context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(
                cr, uid, journal_id, context=context)
            prostor_id = journal.prostor_id and journal.prostor_id.id or False
            nac_plac = journal.nac_plac or False
            uredjaj_id = (journal.fiskal_uredjaj_ids and
                          journal.fiskal_uredjaj_ids[0].id or False)
            result['value'].update({'nac_plac': nac_plac,
                                    'uredjaj_id': uredjaj_id, })
            result['domain'] = result.get('domain', {})
            result['domain'].update(
                {'uredjaj_id': [('prostor_id', '=', prostor_id)]})
        return result

    def prepare_fiskal_racun(self):
        """ Validate invoice, write min. data
        """
        return True

    @api.multi
    def button_fiscalize(self):
        for invoice in self:
            if not invoice.jir:
                invoice.fiskaliziraj()
            elif len(invoice.jir) > 30:  # BOLE: JIR je 32 znaka
                raise UserError(
                    _('FISKALIZIRANO!'),
                    _('Nema potrebe ponavljati postupak fiskalizacije!.'))
            elif invoice.jir == 'PONOVITI SLANJE!':
                raise UserError(_('Ovo nije doradjeno!'),
                                _('Ukoliko vidite ovu poruku u problemu ste!.'))
                # TODO: uzeti ispravno vrijem od računa za ponovljeno slanje..

    def refund(self, cr, uid, ids, date=None, period_id=None,
               description=None, journal_id=None, context=None):
        # Where is the context, per invoice method?
        # This approach is slow, updating after creating,
        # but maybe better than copy-paste whole method
        res = super(AccountInvoice, self).refund(cr, uid, ids, date=date,
                                                 period_id=period_id,
                                                 description=description,
                                                 journal_id=journal_id,
                                                 context=context)
        # what if we get more then one?
        source_invoice = self.browse(cr, uid, ids)[0]
        self.write(cr, uid, res,
                   {'uredjaj_id': (source_invoice.uredjaj_id
                                   and source_invoice.uredjaj_id.id or False),
                    })
        return res

# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from datetime import date, datetime

import uuid
#import openerp.pooler
from fiskal import *
import pytz

class FiscalInvoiceMixin(models.AbstractModel):
    _name = "fiscal.invoice.mixin"
    def fiskaliziraj(self, cr, uid, id, context=None):
        """ Fiskalizira jedan izlazni racun ili point of sale račun
        """
        if context is None:
            context = {}

        prostor_obj = self.pool.get('fiskal.prostor')
        # TB +
        if context.get('pos', False):
            invoice = self.pool.get('pos.order').browse(cr, uid, [id])[0]
        else:
            # TB-
            invoice = self.browse(cr, uid, [id])[0]

        if invoice.jir:
            if len(invoice.jir) > 30:
                return False  # vec je prosao fiskalizaciju

        # tko pokusava fiskalizirati?
        if not invoice.fiskal_user_id:
            self.write(cr, uid, [id], {'fiskal_user_id': uid})

        invoice = self.browse(cr, uid, [id])[0]  # refresh
        self.invoice_valid(cr, uid, invoice)  # provjeri sve podatke

        # TODO - posebna funkcija za provjeru npr. invoice_fiskal_valid()
        if not invoice.fiskal_user_id.oib:
            raise osv.except_osv(_('Error'), _('Neispravan OIB korisnika!'))

        wsdl, key, cert = prostor_obj.get_fiskal_data(cr, uid, company_id=invoice.company_id.id)
        if not wsdl:
            return False
        a = Fiskalizacija('racun', wsdl, key, cert, cr, uid, oe_obj=invoice)

        start_time = a.time_formated()
        a.t = start_time['datum']
        a.zaglavlje.DatumVrijeme = start_time['datum_vrijeme']  # TODO UTC -> Europe/Zagreb
        a.zaglavlje.IdPoruke = str(uuid.uuid4())

        dat_vrijeme = invoice.vrijeme_izdavanja
        if not dat_vrijeme:
            dat_vrijeme = start_time['datum_vrijeme']
            utc_time_stamp = start_time['time_stamp'].astimezone(pytz.UTC)  # convert zagreb time to UTC
            # write UTC time to database bypassing ORM
            doc_table = invoice._table
            cr.execute(""" update %(doc_table)s set vrijeme_izdavanja = %s where id=%s
                       """, (utc_time_stamp.strftime('%Y-%m-%d %H:%M:%S'), id))
            # self.write(cr, uid, [id], {'vrijeme_izdavanja': utc_time_stamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT) })
            # update AccountInvoice set vrijeme_izdavanja = '2013-07-17 12:10:10' where id=112
        else:
            tstamp = datetime.strptime(dat_vrijeme, '%Y-%m-%d %H:%M:%S')
            tstamp = timezone('UTC').localize(tstamp).astimezone(timezone('Europe/Zagreb'))
            dat_vrijeme = '%02d.%02d.%02dT%02d:%02d:%02d' % (
            tstamp.day, tstamp.month, tstamp.year, tstamp.hour, tstamp.minute, tstamp.second)

        if not invoice.company_id.fina_certifikat_id:
            raise osv.except_osv(_('No certificate!'),
                                 _('No valid certificate found for fiscalization usage, Please provide one.'))
        if invoice.company_id.fina_certifikat_id.cert_type == 'fina_prod':
            a.racun.Oib = invoice.company_id.partner_id.vat[2:]  # pravi OIB company
        elif invoice.company_id.fina_certifikat_id.cert_type == 'fina_demo':
            a.racun.Oib = invoice.uredjaj_id.prostor_id.spec[2:]  # OIB IT firme
        else:
            pass  # TODO Error

        a.racun.DatVrijeme = dat_vrijeme  # invoice.vrijeme_izdavanja
        a.racun.OznSlijed = invoice.uredjaj_id.prostor_id.sljed_racuna  # 'P' ## sljed_racuna

        # dijelovi broja racuna
        if invoice.company_id.separator:
            # ako koristimo drugi separator vratiti broj separiran sa '/'(mjenja zadnja dva eparatora)
            separator = str(invoice.company_id.separator)
            invoice_number = str(invoice.number)[::-1].replace(separator[::-1], "/"[::-1], 2)[::-1]
            BrojOznRac, OznPosPr, OznNapUr = invoice_number.rsplit('/', 2)
        else:
            BrojOznRac, OznPosPr, OznNapUr = invoice.number.rsplit('/', 2)
        BrOznRac = ''
        for b in ''.join([x for x in BrojOznRac[::-1]]):  # reverse
            if b.isdigit():
                BrOznRac += b
            else:
                break  # break on 1. non digit
        BrOznRac = BrOznRac[::-1].lstrip('0')  # reverse again and strip leading zeros

        a.racun.BrRac.BrOznRac = BrOznRac
        a.racun.BrRac.OznPosPr = OznPosPr
        a.racun.BrRac.OznNapUr = OznNapUr
        a.racun.USustPdv = invoice.uredjaj_id.prostor_id.sustav_pdv and "true" or "false"
        if invoice.uredjaj_id.prostor_id.sustav_pdv:
            self.get_fiskal_taxes(cr, uid, invoice, a, context=context)
        a.racun.IznosUkupno = fiskal_num2str(invoice.amount_total)
        a.racun.NacinPlac = invoice.nac_plac
        a.racun.OibOper = invoice.fiskal_user_id.oib[2:]  # "57699704120"
        if not invoice.zki:
            a.racun.NakDost = "false"  # TODO rutina koja provjerava jel prvi puta ili ponovljeno sranje!
            a.izracunaj_zastitni_kod()  # start_time['datum_racun'])
            self.write(cr, uid, id, {'zki': a.racun.ZastKod})
        else:
            a.racun.NakDost = "true"
            a.racun.ZastKod = invoice.zki
        fiskaliziran = a.posalji_racun()
        if fiskaliziran:
            jir = a.poruka_odgovor[1].Jir
            self.write(cr, uid, id, {'jir': jir})
        else:
            cert_type = invoice.company_id.fina_certifikat_id.cert_type
            self.write(cr, uid, id, {'jir': 'PONOVITI SLANJE! ' + cert_type})
        return True


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = ["account.invoice", "fiscal.invoice.mixin"]

    #debug vrijeme_izdavanja = fields.Datetime("Vrijeme", readonly=True)

    fiskal_user_id = fields.Many2one(
        'res.users',
        'Fiskalizirao',
        help='Fiskalizacija. Osoba koja je potvrdila racun')
    zki = fields.Char(
        'ZKI',
        readonly=True)
    jir = fields.Char(
        'JIR',
        readonly=True)
    uredjaj_id = fields.Many2one(
        'fiskal.uredjaj',
        'Naplatni uredjaj',
        help ="Naplatni uređaj na kojem se izdaje racun",
        readonly=True,
        states={'draft':[('readonly',False)]})
    fiskal_log_ids = fields.One2many(
        'fiskal.log',
        'invoice_id',
        'Logovi poruka',
        help="Logovi poslanih poruka prema poreznoj upravi")
    nac_plac = fields.Selection(
        (('G','GOTOVINA'),
         ('K','KARTICE'),
         ('C','CEKOVI'),
         ('T','TRANSAKCIJSKI RACUN'),
         ('O','OSTALO')
         ),
        'Nacin placanja',
        required=True,
        readonly=True,
        default='G', # TODO : postaviti u bazi pitanje kaj da bude default!
        states={'draft':[('readonly',False)]})
    #create_date = fields.Datetime('Creation Date' , readonly=True),
    #write_date = fields.Datetime('Update Date' , readonly=True),

    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        result = super(AccountInvoice,self).onchange_journal_id(cr, uid, ids, journal_id=journal_id, context=context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            prostor_id = journal.prostor_id and journal.prostor_id.id or False
            nac_plac = journal.nac_plac or False
            uredjaj_id = journal.fiskal_uredjaj_ids and journal.fiskal_uredjaj_ids[0].id or False
            result['value'].update({'nac_plac': nac_plac,
                                    'uredjaj_id': uredjaj_id,
                                   })
            result['domain'] = result.get('domain', {})
            result['domain'].update({'uredjaj_id': [('prostor_id', '=', prostor_id)]})
        return result

    def copy(self, id, default=None):
        default = default or {}
        default.update({
            'vrijeme_izdavanja':False,
            'fiskal_user_id':False,
            'zki':False,
            'jir': False,
            'fiskal_log_ids': False,
            #'prostor_id': False,
            #'nac_plac': False,
        })
        return super(AccountInvoice, self).copy(id, default)

    def prepare_fiskal_racun(self, id):
        """ Validate invoice, write min. data 
        """
        return True

    @api.multi
    def button_fiscalize(self):
        for invoice in self:
            if not(invoice.jir):
                self.fiskaliziraj(invoice.id)
            elif len(invoice.jir) > 30: #BOLE: JIR je 32 znaka
                raise osv.except_osv(_('FISKALIZIRANO!'), _('Nema potrebe ponavljati postupak fiskalizacije!.'))
            elif invoice.jir=='PONOVITI SLANJE!':
                raise osv.except_osv(_('Ovo nije doradjeno!'), _('Ukoliko vidite ovu poruku u problemu ste!.'))
                #TODO: uzeti ispravno vrijem od računa za ponovljeno slanje..


    def get_fiskal_taxes(self, invoice, a):
        res = []

        def get_factory(val):
            fiskal_type = val.get('fiskal_type', False)

            if   fiskal_type == 'pdv':    tns = {'tns': (a.racun.Pdv.Porez , 'tns:Porez')     , 'fields': ('Stopa' , 'Osnovica', 'Iznos') }
            elif fiskal_type == 'pnp':    tns = {'tns': (a.racun.Pnp.Porez , 'tns:Porez')     , 'fields': ('Stopa' , 'Osnovica', 'Iznos') }
            elif fiskal_type == 'ostali': tns = {'tns': (a.racun.OstaliPor.Porez, 'tns:Porez'), 'fields': ('Naziv', 'Stopa' , 'Osnovica', 'Iznos') }
            elif fiskal_type == 'naknade':tns = {'tns': (a.racun.Naknade, 'tns:Naknada'), 'fields': ('NazivN', 'IznosN') }

            elif fiskal_type == 'oslobodenje':  tns = {'tns': (a.racun.IznosOslobPdv), 'value': 'Osnovica' }
            elif fiskal_type == 'ne_podlijeze': tns = {'tns': (a.racun.IznosNePodlOpor), 'value': 'Osnovica' }
            elif fiskal_type == 'marza':        tns = {'tns': (a.racun.IznosMarza), 'value': 'Osnovica' }
            else: tns = {}
            place = tns.get('tns', False)
            if not place:
                return False
            if len(place) > 1:
                porez = a.client2.factory.create(place[1])
                place[0].append(porez)
            else:
                porez = place[0]

            if tns.get('fields', False):
                for field in tns['fields']:
                    porez[field] = val[field]

            if tns.get('value', False):
                tns['tns'][0] = val[field]

            return tns

        for tax in invoice.tax_line:
            if not tax.tax_code_id:
                continue #TODO special cases without tax code, or with base tax code without tax if found
            val = {'tax_code': tax.tax_code_id.id,
                  'fiskal_type': tax.tax_code_id.fiskal_type,
                  'Naziv': tax.tax_code_id.name,
                  'Stopa': tax.tax_code_id.fiskal_percent,
                  'Osnovica': fiskal_num2str(tax.base_amount),
                  'Iznos': fiskal_num2str(tax.tax_amount),
                  'NazivN': tax.tax_code_id.name,
                 }
            res.append(val)
            #TODO group and sum by fiskal_type and Stopa hmmm then send 1 by one into factory... 
            get_factory(val)
        return res

    def invoice_valid(self, invoice):
        if not invoice.journal_id.fiskal_active:
            raise UserError(_('Error'), _('Za ovaj dokument fiskalizacija nije aktivna!!'))
        if not invoice.fiskal_user_id.oib:
            raise UserError(_('Error'), _('Neispravan OIB korisnika!'))
        if not invoice.uredjaj_id.id:
            raise UserError(_('Error'), _('Nije odabran naplatni uredjaj / Dokument !'))
        return True

    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None):
        # Where is the context, per invoice method?
        # This approach is slow, updating after creating, but maybe better than copy-paste whole method
        res = super(AccountInvoice, self).refund(cr, uid, ids, date=date, period_id=period_id, description=description, journal_id=journal_id)
        source_invoice = self.browse(cr, uid, ids)[0]  # what if we get more then one?
        self.write(cr, uid, res,
                   {'uredjaj_id': source_invoice.uredjaj_id
                                    and source_invoice.uredjaj_id.id or False,
                    })
        return res

# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fiskal_active = fields.Boolean(
        'Fiskalizacija aktivna',
        default=False,
        help="Fiskalizacija aktivna")
    prostor_id = fields.Many2one(
        'fiskal.prostor',
        'Prostor',
        select=True,
        help='Prostor naplatnog uredjaja.')
    nac_plac = fields.Selection(
        (('G', 'GOTOVINA'),
         ('K', 'KARTICE'),
         ('C', 'CEKOVI'),
         ('T', 'TRANSAKCIJSKI RACUN'),
         ('O', 'OSTALO')
         ),
        'Nacin placanja'),
    fiskal_uredjaj_ids = fields.Many2many(
        'fiskal.uredjaj',
        string='Dopusteni naplatni uredjaji')


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    def _get_fiskal_type(self):
        return [('pdv', 'Pdv'),
                ('pnp', 'Porez na potrosnju'),
                ('ostali', 'Ostali porezi'),
                ('oslobodenje', 'Oslobodjenje'),
                ('marza', 'Oporezivanje marze'),
                ('ne_podlijeze', 'Ne podlijeze oporezivanju'),
                ('naknade', 'Naknade (npr. ambalaza)'),
                ]
    fiskal_percent = fields.Char(
        'Porezna stopa',
        help='Porezna stopa za potrebe fiskalizacije. Primjer: 25.00')
    fiskal_type = fields.Selection(
        _get_fiskal_type,
        'Vrsta poreza',
        help='Vrsta porezne grupe za potrebe fiskalizacije.')


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        if res:
            invoice = self._context.get('invoice', False)
            if not invoice or not invoice.journal_id.fiskal_active: #orinvoice.nac_plac != 'T':
                return res
            if not invoice.type in ('out_invoice', 'out_refund'):  # samo izlazne racune  
                return res
            if not (invoice.company_id.country_id and invoice.company_id.country_id.code == 'HR' or False):
                return res
            if not invoice.uredjaj_id:
                raise UserError(_('Greška'), _('Nije odabran naplatni uredjaj!'))
            if not invoice.journal_id.fiskal_active and invoice.nac_plac != 'T':
                raise UserError(_('Greška'), _('Nije aktivna fiskalizacija, moguci nacin placanje je samo Transakcijski racun!'))
            if not invoice.uredjaj_id.prostor_id.oznaka_prostor:
                raise UserError(_('Nije odabran prodajni prostor!'), _('Odaberite iz kojeg prostora vršite prodaju'))

            fiskalni_sufiks = '/'.join((invoice.uredjaj_id.prostor_id.oznaka_prostor, str(invoice.uredjaj_id.oznaka_uredjaj)))
            for move in self:
                new_name = '/'.join((move.name, fiskalni_sufiks))
                self.write([move.id], {'name': new_name})
                if not invoice.company_id.fina_certifikat_id:
                    return res
                if invoice.journal_id.fiskal_active:  # samo oznacene journale
                    self.env['account.invoice'].fiskaliziraj(invoice.id)
                if invoice.company_id.separator:
                    separator = str(invoice.company_id.separator)
                    new_name = new_name.replace('/', separator)
                self.write([move.id], {'name': new_name})
        return res


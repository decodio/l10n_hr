# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_base
#    Author: Goran Kliska
#    mail:   gkliskaATgmail.com
#    Copyright (C) 2011- Slobodni programi d.o.o., Zagreb
#               http://www.slobodni-programi.hr
#    Contributions: 
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
from openerp import models, fields, api


class Bank(models.Model):
    _inherit = 'res.bank'

    vbb_code = fields.Char('VBB', size=24, help='Vodeći broj banke')


class l10n_hr_base_nkd(models.Model):
    _name = 'l10n_hr_base.nkd'
    _description = 'NKD - Nacionalna klasifikacija djelatnosti'

    code = fields.Char('Code', required=True, size=16, select=1)
    name = fields.Char('Name', required=True)


class res_company(models.Model):
    _inherit = 'res.company'

    l10n_hr_base_nkd_id = fields.Many2one('l10n_hr_base.nkd', 'NKD',
                           help='Nacionalna klasifikacija djelatnosti')
    porezna_uprava = fields.Char('Porezna uprava')
    porezna_ispostava = fields.Char('Porezna ispostava')
    br_obveze_mirovinsko = fields.Char('Br. obveze mirovinsko')
    br_obveze_zdravstveno = fields.Char('Br. obveze zdravstveno')
    maticni_broj = fields.Char('Maticni broj', size=16)
    temeljni_kapital = fields.Float('Temeljni kapital', digits=(16, 2))
    clanovi_uprave = fields.Char('Clanovi uprave')
    trg_sud = fields.Char('Trgovacki sud u', size=32)
    podnozje_ispisa = fields.Text('Podnozje ispisa', default='')
    zaglavlje_ispisa = fields.Char('Zaglavlje ispisa')
    responsible_fname = fields.Char('Ime', size=64)
    responsible_lname = fields.Char('Prezime', size=64)
    responsible_tel = fields.Char('Telefon', size=64)
    responsible_email = fields.Char('E-mail', size=64)
    ispostava = fields.Char('Ispostava', size=64)
    #deprec
    racun_obrazac = fields.Char('Vrsta racuna', size=32,
                                help='Oznaka na ispisu računa. Bivši "R-1"/"R-2"')
    #BOLE: dodana polja za URA u xml:
    ulica = fields.Char('Ulica')
    kbr = fields.Char('Kucni broj')
    kbr_dodatak = fields.Char('Dodatak kucnom broju')
    podrucje_djelatnosti = fields.Selection(
        selection=[
            ('A', 'A-POLJOPRIVREDA, ŠUMARSTVO I RIBARSTVO'),
            ('B', 'B-RUDARSTVO I VAĐENJE'),
            ('C', 'C-PRERAĐIVAČKA INDUSTRIJA'),
            ('D', 'D-OPSKRBA ELEKTRIČNOM ENERGIJOM, PLINOM, PAROM I KLIMATIZACIJA'),
            ('E', 'E-OPSKRBA VODOM, UKLANJANJE OTPADNIH VODA, GOSPODARENJE OTPADOM TE DJELATNOSTI SANACIJE OKOLIŠA'),
            ('F', 'F-GRAĐEVINARSTVO'),
            ('G', 'G-TRGOVINA NA VELIKO I NA MALO; POPRAVAK MOTORNIH VOZILA I MOTOCIKALA'),
            ('H', 'H-PRIJEVOZ I SKLADIŠTENJE'),
            ('I', 'I-DJELATNOSTI PRUŽANJA SMJEŠTAJA TE PRIPREME I USLUŽIVANJA HRANE'),
            ('J', 'J-INFORMACIJE I KOMUNIKACIJE'),
            ('K', 'K-FINANCIJSKE DJELATNOSTI I DJELATNOSTI OSIGURANJA'),
            ('L', 'L-POSLOVANJE NEKRETNINAMA'),
            ('M', 'M-STRUČNE, ZNANSTVENE I TEHNIČKE DJELATNOSTI'),
            ('N', 'N-ADMINISTRATIVNE I POMOĆNE USLUŽNE DJELATNOSTI'),
            ('O', 'O-JAVNA UPRAVA I OBRANA; OBVEZNO SOCIJALNO OSIGURANJE'),
            ('P', 'P-OBRAZOVANJE'),
            ('Q', 'Q-DJELATNOSTI ZDRAVSTVENE ZAŠTITE I SOCIJALNE SKRBI'),
            ('R', 'R-UMJETNOST, ZABAVA I REKREACIJA'),
            ('S', 'S-OSTALE USLUŽNE DJELATNOSTI'),
            ('T', 'T-DJELATNOSTI KUĆANSTAVA KAO POSLODAVACA'),
            ('U', 'U-DJELATNOSTI IZVANTERITORIJALNIH ORGANIZACIJA I TIJELA'),
        ], string='Područje djelatnosti',
    )


    @api.onchange('maticni_broj')
    def update_podnozje(self):
        val = []
        if self.name:
            val.append(self.name+' ') + (self.l10n_hr_base_nkd_id and
                        self.l10n_hr_base_nkd_id.name)
        if self.trg_sud:
            val.append(' upisano je u registarski uložak Trgovačkog suda u '
                       + self.trg_sud)
        if self.company_registry:
            val.append(' pod brojem\nMBS: ' + self.company_registry)
        if self.maticni_broj:
            val.append(' | MB: ' + self.maticni_broj)
        if self.vat:
            val.append(' | VAT: ' + self.vat)
        if self.temeljni_kapital:
            val.append('\nTemeljni kapital društva ' + '{:,.2f}'.format(self.temeljni_kapital)
                       + ' HRK uplaćen je u cijelosti u novcu')
        if self.clanovi_uprave:
            val.append(' Članovi uprave: ' + self.clanovi_uprave)
        self.podnozje_ispisa = ''.join(val)


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('vat', 'country_id')
    def _get_vat_type(self):
        for partner in self:
            if not partner.vat:
                partner.vat_id_type = '0'
                continue
            pc = partner.vat[:2]
            cc = partner.country_id and partner.country_id.code or False
            if pc != 'HR':
                partner.vat_id_type = '3'
                continue
            if cc and cc != pc:
                partner.vat_id_type = '2'
                continue
            # DB: ali ako nema drzavu a vat ne pocinje sa HR??
            #     ili ima krivo upisanu drzavu??
            partner.vat_id_type = '1'


    vat_ext = fields.Char('VAT Extension', size=3, default='')
    vat_id_type = fields.Selection(
        selection=[
            ('0', '0 - NO VAT'),
            ('1', '1 - OIB'),
            ('2', '2 - VAT ID'),
            ('3', '3 - VAT (Foreign)')
        ], string="VAT Type",
        compute=_get_vat_type,
        store=True,
        help="0 - partners without VAT number entered,"
             "1 - OIB - partners from croatia with Croatia VAT number"
             "2 - VAT ID - partners with Croatia VAT, without residence in Croatia"
             "3 - Foreign partners"
    )



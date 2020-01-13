# -*- encoding: utf-8 -*-

import pytz
from tzlocal import get_localzone
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Company(models.Model):
    _inherit = "res.company"

    @api.depends('country_id')
    def _check_origin_croatia(self):
        for company in self:
            company.croatia = company.country_id and company.country_id.code == 'HR'

    croatia = fields.Boolean(
        string="Croatia",
        compute="_check_origin_croatia",
        # technical field for show/hide croatia settings, multi-localziation environment
        # never to be exposed to UI, always invisible!
        # todo: move to l10n_hr_base_multilocalization module
    )
    # Fields, DB: NAMJERNO SU SVI NAZIVI NA HRVATSKOM!

    nkd = fields.Char(
        string="NKD",
        help="Šifra glavne djelatnosti prema NKD-2007"
    )
    mirovinsko = fields.Char(
        string='Mirovinsko',
        help='Broj obveznika uplaćivanja mirovinskog osiguranja')
    zdravstveno = fields.Char(
        string='Zdravstveno',
        help='Broj obveze uplaćivanja zdravstvenog osiguranja')
    maticni_broj = fields.Char(string='Matični broj')
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

    # pravni_oblik = fields.Selection([#TODO: Dopuniti sa ostalim opcijama?
    #     ('obrt', 'Obrt'),
    #     ('jdoo', 'J.D.O.O.'),
    #     ('doo', 'D.O.O.'),
    #     ('dd', 'D.D'),
    #     ('jtd', 'J.T.D'), # Javno trgovačko društvo
    #     ('kd', 'K.D'),    # Komanditno društvo
    #     ('pred', 'Predstavništvo'),
    # ], 'Pravni oblik')
    #     #default='doo', required=True)

    def get_l10n_hr_time_formatted(self):
        # OLD WAY: tstamp = datetime.now(pytz.timezone('Europe/Zagreb'))
        # DB: Server bi morao biti na UTC time...
        # ali ovo vraća točan local time za any given server timezone setup
        # even if server is on Sidney local time, fiscal time is still in Zagreb :)
        zg = pytz.timezone('Europe/Zagreb')
        server_tz = get_localzone()
        time_now = pytz.utc.localize(datetime.utcnow()).astimezone(server_tz)
        tstamp = zg.normalize(time_now)
        return {
            'datum': tstamp.strftime('%d.%m.%Y'),                   # datum_regular SAD
            'datum_vrijeme': tstamp.strftime('%d.%m.%YT%H:%M:%S'),  # format za zaglavlje FISKAL XML poruke
            'datum_meta': tstamp.strftime('%Y-%m-%dT%H:%M:%S'),    # format za metapodatke xml-a ( JOPPD...)
            'datum_racun': tstamp.strftime('%d.%m.%Y %H:%M:%S'),    # format za ispis na računu
            'time_stamp': tstamp,                                   # timestamp, za zapis i izračun vremena obrade
            'odoo_datetime': time_now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }


# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from ..fiskal import fiskal


class FiskalZastitniKod(models.TransientModel):
    _name = 'fiskal.zastitni.kod'
    _description = 'Calculator/Check for ZKI'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env['res.company']._company_default_get(
            'fiskal.zastitni.kod')
    )
    cert_id = fields.Many2one(
        comodel_name='crypto.certificate'
    )
    oib = fields.Char(
        string='OIB Izdavatelja', required=True)
    datum_vrijeme = fields.Char(
        string="Datum i vrijeme izdavanja", # required=True,
        help="Prepišite za računa u obliku DD.MM.GGGG HH:MM:SS"
    )
    fiskalni_broj_racuna = fields.Char(
        string="Fiskalni broj", # required=True,
        help="Prepišite TOČAN FISKALNI broj računa"
    )
    br_racuna = fields.Char(readonly=1)
    oznaka_pp = fields.Char(readonly=1)
    oznaka_nu = fields.Char(readonly=1)
    ukupan_iznos = fields.Float(
        string="Ukupan iznos", required=1,
    )
    zki = fields.Char()
    zki_check = fields.Char()

    @api.multi
    def button_generate_zki(self):
        self.ensure_one()
        zki_datalist = [
            self.company_id.partner_id.get_oib(),
            self.datum_vrijeme,
            self.br_racuna,
            self.oznaka_pp,
            self.oznaka_nu,
            fiskal.format_decimal(self.ukupan_iznos)
        ]
        zki = fiskal.generate_zki(
            zki_datalist=zki_datalist,
            key_str=self.cert_id.csr
        )
        self.zki = zki
        view_id = self.env.ref('l10n_hr_account_fiskal_oca.wizard_zastitni_kod')
        return {
            'name': 'ZKI',
            'res_model': 'fiskal.zastitni.kod',
            'res_id': self.id,
            'view_id': view_id.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
        }


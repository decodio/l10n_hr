# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class CryptoGeneratePairkey(models.TransientModel):
    _name = 'crypto.generate.pairkey'
    _description = 'Crypto Pairkey generator'


    name = fields.Char('Pair key name')
    key_length = fields.Integer('Key lenght', default=2048)
    update = fields.Boolean('Update key')

    @api.multi
    def button_generate(self):
        self.ensure_one()
        active_id = self._context['active_id']
        pairkey_obj = self.env['crypto.pairkey'].browse(active_id)

        pairkey_obj.generate_keys(key_length=self.key_length)
        pairkey_obj.action_validate()
        return {'type': 'ir.actions.act_window_close'}





from odoo import api, fields, models, _


class ResBank(models.Model):
    _inherit = 'res.bank'

    vbb_code = fields.Char('VBB', size=24, help='Vodeći broj banke')

from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_hr_kpd_id = fields.Many2one(comodel_name='l10n.hr.kpd', string="KPD Code", readonly=True,
                                     domain=[('type', '=', '6')])


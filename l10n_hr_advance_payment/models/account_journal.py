from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    advance_payment = fields.Boolean('Advance Payment', default=False, copy=False)

# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.exceptions import except_orm

class Users(models.Model):
    _inherit = 'res.users'

    journal_ids = fields.Many2many(comodel_name='account.journal',
        relation='user_account_journal_rel', column1='journal_id', column2='user_id',
        #domain="[('type', '=', 'sale')]",
                                   string='Dozvoljeni dnevnici')

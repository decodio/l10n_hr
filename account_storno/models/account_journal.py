# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    posting_policy = fields.Selection(
        selection=[
            ('contra', 'Contra (Standard Odoo)'),
            ('storno', 'Storno (-)')
        ], default='contra', string='Storno or Contra', required=True,
        help="Storno allows minus postings, Refunds are posted on the "
             "same journal with negative sign.\n"
             "Contra doesn't allow negative posting. "
             "Refunds are posted by swapping credit and debit side.")
    refund_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Refund journal',
        help="Journal for refunds/returns from this journal. Leave empty to "
             "use same journal for normal and refund/return postings.",
    )

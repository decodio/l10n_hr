

from odoo import api, fields, models, _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Invoicing journal",
        help="Default invoicing journal for this team",
        domain=[('type', '=', 'sale')]
    )

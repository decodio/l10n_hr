from odoo import models, fields, api
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS


class L10nHrBusinessProcessType(models.Model):
    _name = "l10n.hr.business.process.type"
    _description = "Defines business process type."
    _inherit = ['mail.thread']

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'The business process type code has to be unique!')
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for bpt in self:
            if bpt.code and bpt.name:
                bpt.display_name = bpt.code + ' - ' + bpt.name

    @api.multi
    def name_get(self):
        result = []
        for bpt in self:
            name = '%s - %s' % (bpt.code, bpt.name)
            result.append((bpt.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            if operator in NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        types = self.search(domain + args, limit=limit)
        return [(t.id, t.display_name) for t in types.sudo()]

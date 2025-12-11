from odoo import models, fields, api
from odoo.osv import expression


class L10nHrVatexTaxExempt(models.Model):
    _name = "l10n.hr.vatex.tax.exempt"
    _description = "Defines VATEX tax category."
    _inherit = ['mail.thread']

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True, translate=True)
    # not multi-lang
    # display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    description = fields.Text(string="Description", translate=True)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'The VATEX tax exempt code has to be unique!')
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for exempt in self:
            if exempt.code and exempt.name:
                exempt.display_name = exempt.code + ' - ' + exempt.name

    @api.multi
    def name_get(self):
        res = []
        for vatex in self:
            rec_name = '%s - %s' % (vatex.code, vatex.name)
            res.append((vatex.id, rec_name))
        return res

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        vatexs = self.search(domain + args, limit=limit)
        return vatexs.name_get()

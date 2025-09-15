from odoo import fields, models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    l10n_hr_kpd_id = fields.Many2one(comodel_name='l10n.hr.kpd', string="KPD Code", compute='_compute_l10n_hr_kpd_id',
                                     store=True, readonly=False, precompute=True,
                                     domain=[('type', '=', '6')])

    @api.depends('product_id')
    def _compute_l10n_hr_kpd_id(self):
        for line in self:
            kpd = line.product_id.with_context(force_company=line.company_id.id).l10n_hr_property_kpd_id
            if not kpd:
                kpd = line.product_id.categ_id.l10n_hr_kpd_id
                if not kpd:
                    parent_categories = self.env['product.category'].search(
                        [('id', 'parent_of', line.product_id.categ_id.id),
                         ('l10n_hr_kpd_id', '!=', False)],
                        order='parent_id ASC'
                    )
                    kpd = fields.first(parent_categories).l10n_hr_kpd_id
            line.l10n_hr_kpd_id = kpd.id

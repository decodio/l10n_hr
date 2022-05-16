from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    advance_payment_count = fields.Integer(compute='_get_invoice_count', string='Advance Payments count',
                                           readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoice_count', readonly=True)

    @api.multi
    def _get_invoice_count(self):
        for order in self:
            invoices = order.invoice_ids
            order.advance_payment_count = len(invoices.filtered(lambda i: i.advance_payment))
            order.invoice_count = len(invoices.filtered(lambda i: not i.advance_payment))

    @api.multi
    def action_view_advance_payment_invoice(self):
        invoices = self.mapped('invoice_ids').filtered('advance_payment')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids').filtered(lambda i: not i.advance_payment)
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super().action_invoice_create(grouped=grouped, final=final)
        advance_payments = self.invoice_ids.filtered('advance_payment')
        sale_invoices = self.invoice_ids - advance_payments
        if len(sale_invoices) == 1:
            sale_invoices.advance_invoice_ids = [(6, 0, advance_payments.ids)]
        return res

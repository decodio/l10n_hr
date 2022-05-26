from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    advance_payment_ids = fields.Many2many(comodel_name='account.invoice',
                                           compute='_get_advance_payments', string='Advance Payments', readonly=True)
    advance_payment_count = fields.Integer(compute='_get_advance_payments', string='Advance Payments count',
                                           readonly=True)

    @api.multi
    def _get_advance_payments(self):
        invoice_obj = self.env.get('account.invoice')
        for order in self:
            advance_payments = invoice_obj.search([('purchase_id', '=', order.id),
                                                   ('advance_payment', '=', True)])
            order.advance_payment_ids = advance_payments.ids
            order.advance_payment_count = len(advance_payments)

    @api.multi
    def action_view_invoice(self):
        result = super().action_view_invoice()
        if result.get('context'):
            result['context']['default_advance_invoice_ids'] = self.advance_payment_ids.ids
        return result

    @api.multi
    def action_view_advance_payment_invoice(self):
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        result['display_name'] = 'Supplier Advance Payments'
        # override the context to get rid of the default filtering
        result['context'] = {
            'type': 'in_invoice',
            'default_purchase_id': self.id,
            'default_currency_id': self.currency_id.id,
            'default_company_id': self.company_id.id,
            'company_id': self.company_id.id
        }
        # choose the view_mode accordingly
        if len(self.advance_payment_ids) > 1:
            result['domain'] = "[('id', 'in', " + str(self.advance_payment_ids.ids) + ")]"
        else:
            res = self.env.ref('account.invoice_supplier_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.advance_payment_ids.id or False
        result['context']['default_origin'] = self.name
        result['context']['default_reference'] = self.partner_ref
        return result

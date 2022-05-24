from odoo import fields, models, api


class PurchaseAdvancePaymentInv(models.TransientModel):
    _inherit = 'purchase.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, po_line, amount):
        created_invoice = super()._create_invoice(order, po_line, amount)
        # delete Purchase Order deposit/down payment line
        # 1.1. delete relation with Invoice line
        # 1.2. delete Purchase Order line
        po_line.invoice_lines = [(5,)]
        # TODO: do not toggle order states to unlink down payment line
        old_state = order.state
        order.state = 'draft'
        po_line and po_line.sudo().unlink()
        created_invoice.advance_payment = True
        order.state = old_state
        created_invoice.purchase_id = order.id
        return created_invoice

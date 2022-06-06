from odoo import fields, models, api


class PurchaseAdvancePaymentInv(models.TransientModel):
    _inherit = 'purchase.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, po_line, amount):
        created_invoice = super()._create_invoice(order, po_line, amount)
        # delete Purchase Order deposit/down payment line
        # 1.1. delete relation with Invoice line
        # 1.2. delete Purchase Order line
        self.env.cr.execute("DELETE FROM purchase_order_line WHERE id = %s", (po_line.id,))
        created_invoice.advance_payment = True
        created_invoice.purchase_id = order.id
        return created_invoice

from odoo import fields, models, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        created_invoice = super()._create_invoice(order, so_line, amount)
        # delete Sale Order down payment line
        # 1.1. delete relation with Invoice line
        # 1.2. delete Sale Order line
        so_line.invoice_lines = [(5,)]
        so_line and so_line.sudo().unlink()
        created_invoice.advance_payment = True
        return created_invoice

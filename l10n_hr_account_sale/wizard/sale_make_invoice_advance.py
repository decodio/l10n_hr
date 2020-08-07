from odoo import api, fields, models, _
#from odoo.addons import decimal_precision as dp
#from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"



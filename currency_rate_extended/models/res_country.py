from odoo import models, fields


class Country(models.Model):
    _inherit = "res.country"

    inverse_currency_rate = fields.Boolean(
        string="Inverse Currency Rate",
        help="Use inverse rate when converting from/to currency "
             "(0.140381 <--> 7,123456)",
    )

from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = 'res.partner'

    def get_oib(self):
        self.ensure_one()
        vat = self.vat.upper()  # in case someone entered in owercase?
        res = 'HR' in vat and vat.replace('HR', '') or False
        # if it does not start with HR it is not OIB!
        return res

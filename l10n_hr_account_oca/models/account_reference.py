from odoo import fields, models, api
from odoo.addons.account_reference.models import poziv_na_broj as pnbr


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_P1_P4_selection(self):
        res = super()._get_P1_P4_selection()
        res.extend([('fiscal_number', 'Fiscal Number')])
        return res


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def getP1_P4data(self, what):
        if what == 'fiscal_number':
            res = self.fiskalni_broj
            return pnbr.get_only_numeric_chars(res, exclude_characters=['-'])
        else:
            return super().getP1_P4data(what)

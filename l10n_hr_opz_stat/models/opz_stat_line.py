
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from dateutil.relativedelta import relativedelta
PARTNER_VAT_TYPES = [
            ("vat", "1"),
            ("vatid", "2"),
            ("other", "3"),
        ]


class OpzStatLine(models.Model):
    _name = "opz.stat.line"
    _description = "OPZ STAT report lines"
    _order = "invoice_date"

    opz_id = fields.Many2one("opz.stat", "OPZ STAT", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", "Partner", domain="[('customer', '=', True)]")
    partner_name = fields.Char("Partner Name", required=True)
    partner_vat_type = fields.Selection(PARTNER_VAT_TYPES, string="VAT Type", required=True, index=True,
                                        default=PARTNER_VAT_TYPES[0][0])
    partner_vat_number = fields.Char("VAT Number", required=True)
    invoice_id = fields.Many2one(
        "account.invoice",
        "Invoice",
        copy=True,
        domain="[('partner_id', '=', partner_id), ('account_id.internal_type', '=', 'receivable')]",
    )
    invoice_number = fields.Char("Invoice Number", required=True)
    invoice_date = fields.Date("Invoice Date", required=True)
    due_date = fields.Date("Due Date", required=True)
    amount = fields.Float("Amount", required=True, defaults=0.0, digits=dp.get_precision('Account'))
    amount_tax = fields.Float("Amount Tax", required=True, defaults=0.0, digits=dp.get_precision('Account'))
    amount_total = fields.Float("Amount with Tax", required=True, defaults=0.0, digits=dp.get_precision('Account'))
    paid = fields.Float("Paid Amount", required=True, defaults=0.0, digits=dp.get_precision('Account'))
    unpaid = fields.Float("Unpaid Amount", required=True, defaults=0.0, digits=dp.get_precision('Account'))
    overdue_days = fields.Integer("Overdue Days", required=True, defaults=0, digits=dp.get_precision('Account'))

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            if self.partner_vat_type == "vat":
                self.partner_vat_number = (
                    self.partner_id.vat and self.partner_id.vat[2:]
                )
            else:
                self.partner_vat_number = self.partner_id.vat
        else:
            self.partner_name = False
            self.partner_vat_number = False

    @api.onchange("invoice_id")
    def onchange_invoice_id(self):
        if self.invoice_id:
            overdue = (
                (
                    # datetime.strptime(self.opz_id.date_to, "%Y-%m-%d")
                    self.opz_id.date_to + relativedelta(months=1)
                )
                + relativedelta(day=1, months=+1, days=-1)
            ) - self.invoice_id.date_due  # - datetime.strptime(self.invoice_id.date_due, "%Y-%m-%d").date()
            self.invoice_number = self.invoice_id.number
            self.invoice_date = self.invoice_id.date_invoice
            self.due_date = self.invoice_id.date_due
            self.amount = self.invoice_id.amount_untaxed
            self.amount_tax = self.invoice_id.amount_tax
            self.amount_total = self.invoice_id.amount_total
            self.overdue_days = overdue.days
            # TODO residual must be computed
            self.paid = self.invoice_id.amount_total - self.invoice_id.residual
            self.unpaid = self.invoice_id.residual

    @api.onchange("due_date")
    def onchange_due_date(self):
        if self.due_date:
            overdue = (
                (
                    #  datetime.strptime(self.opz_id.date_to, "%Y-%m-%d")
                    self.opz_id.date_to + relativedelta(months=1)
                )
                + relativedelta(day=1, months=+1, days=-1)
            ) - self.due_date  # .date() - datetime.strptime(self.due_date,"%Y-%m-%d").date()
            self.overdue_days = overdue.days
        else:
            self.overdue_days = False

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    fiskalni_broj = fields.Char(
        string="Fiskalni broj", copy=False,
        help="Fiskalni broj računa u knjigama URA/IRA.",
        readonly=True, states={'draft': [('readonly', False)]})
    croatia = fields.Boolean(related="company_id.croatia")

    def _gen_fiskal_number(self, invoice, move):
        prostor = invoice.fiskal_uredjaj_id.prostor_id.oznaka_prostor
        uredjaj = str(invoice.fiskal_uredjaj_id.oznaka_uredjaj)
        # DB: Refund sequence je isti kao i main seq osim ako nije drugačije zadano!
        separator = invoice.company_id.fiskal_separator
        sequence = move.journal_id.sequence_id.with_context(
            ir_sequence_date=invoice.date or invoice.date_invoice,
            # ir_sequence_date_range=invoice.date or invoice.date_invoice,
        )
        prefix, suffix = sequence._get_prefix_suffix()
        invoice_name = move.name.replace(prefix, '', 1)
        if suffix and invoice_name.endswith(suffix):
            invoice_name = invoice_name[:-len(suffix)]
        if not invoice_name.isdigit():
            raise Warning(_("Invalid fiscal invoice number! %s is not integer.")
                          % invoice_name)
        fiskalni_broj = separator.join((str(int(invoice_name)), prostor, uredjaj))
        # user can change/force invoice.fiskalni_broj
        invoice.fiskalni_broj = fiskalni_broj

    @api.multi
    def post(self, invoice=False):
        res = super(AccountMove, self).post(invoice=invoice)

        # This constraint is valid for manually entered moves.
        # Commented out for performance concerns
        # if (not invoice) and self.company_id.croatia:
        #     for move in self:
        #         if move.journal_id.type in ('sale', 'purchase') and not move.fiskalni_broj:
        #             raise UserWarning(_("Fiscal Invoice number is mandatory!" ))

        if (not invoice) or (not self.company_id.croatia):
            return res

        # only for croatia out invoices check active premise and gen fiscal inv. number
        if invoice.type in ('out_invoice', 'out_refund'):
            if invoice.fiskal_uredjaj_id.prostor_id.state != 'active':
                raise Warning(_(
                    "Invoice posting not possible, business premise %s is not active!")
                    % invoice.fiskal_uredjaj_id.prostor_id.name)
            self._gen_fiskal_number(invoice, self)
            # after first posting journal is locked for changes
            if not invoice.fiskal_uredjaj_id.lock:
                invoice.fiskal_uredjaj_id.lock = True
            if not invoice.fiskal_uredjaj_id.prostor_id.lock:
                invoice.fiskal_uredjaj_id.prostor_id.lock = True

        # For tax books name *must* be fiscal or supplier invoice number
        if invoice.type in ('out_invoice', 'out_refund'):
            if not invoice.name:
                invoice.name = invoice.fiskalni_broj
        if invoice.type in ('in_invoice', 'in_refund'):
            if not invoice.name:
                if 'supplier_invoice_number' in invoice._fields:
                    invoice.name = invoice.supplier_invoice_number
            if not invoice.fiskalni_broj:
                raise UserError(_("Fiscal Invoice number is missing!"))

        self.fiskalni_broj = invoice.fiskalni_broj
        return res

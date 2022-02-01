# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class AccountMove(models.Model):
    _inherit = "account.move"

    def _gen_fiskal_number(self, invoice, move):
        prostor = invoice.fiskal_uredjaj_id.prostor_id.oznaka_prostor
        uredjaj = str(invoice.fiskal_uredjaj_id.oznaka_uredjaj)
        # DB: Refund sequence je isti kao i main seq
        #     osim ako nije drugačije zadano!
        separator = invoice.company_id.fiskal_separator
        sequence = move.journal_id.sequence_id.with_context(
            ir_sequence_date=invoice.date or invoice.date_invoice,
            ir_sequence_date_range=invoice.date or invoice.date_invoice,
        )
        prefix, suffix = sequence._get_prefix_suffix()
        invoice_name = move.name.replace(prefix, '', 1)
        if suffix and invoice_name.endswith(suffix):
            invoice_name = invoice_name[:-len(suffix)]
        fiskalni_broj = separator.join((str(int(invoice_name)), prostor, uredjaj))
        if not invoice.fiskalni_broj:
            invoice.fiskalni_broj = fiskalni_broj

    @api.multi
    def post(self, invoice=False):
        res = super(AccountMove, self).post(invoice=invoice)
        if invoice and invoice.type in ('out_invoice', 'out_refund'):
            for move in self:
                if not move.company_id.croatia:
                    continue
                # only for croatia invoices i check active premise
                if invoice.fiskal_uredjaj_id.prostor_id.state != 'active':
                    raise Warning(_(
                        "Invoice posting not possible, "
                        "business premise %s is not active!" %
                        invoice.fiskal_uredjaj_id.prostor_id.name
                    ))
                self._gen_fiskal_number(invoice, move)
                # now and set lock on journals,
                # after first posting journal is locked for changes
                if not invoice.fiskal_uredjaj_id.lock:
                    invoice.fiskal_uredjaj_id.lock = True
                if not invoice.fiskal_uredjaj_id.prostor_id.lock:
                    invoice.fiskal_uredjaj_id.prostor_id.lock = True
        if invoice and not invoice.number_sequence:
            for move in self:
                if move.journal_id.sequence_id:
                    sequence = move.journal_id.sequence_id
                    if invoice.type in ['out_refund', 'in_refund'] and move.journal_id.refund_sequence:
                        sequence = move.journal_id.refund_sequence_id
                    sequence_date = self.date or self.date_invoice
                    invoice.number_sequence = sequence._get_current_sequence(sequence_date=sequence_date).number_next_actual
        return res

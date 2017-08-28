# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    @api.multi
    def _prepare_payment_line(self, payment, line):
        """This function is designed to be inherited
        The resulting dict is passed to the create method of payment.line"""
        self.ensure_one()
        _today = fields.Date.context_today(self)
        date_to_pay = False  # no payment date => immediate payment
        if payment.date_prefered == 'due':
            # -- account_banking
            # date_to_pay = line.date_maturity
            date_to_pay = (
                line.date_maturity
                if line.date_maturity and line.date_maturity > _today
                else False)
            # -- end account banking
        elif payment.date_prefered == 'fixed':
            # -- account_banking
            # date_to_pay = payment.date_scheduled
            date_to_pay = (
                payment.date_scheduled
                if payment.date_scheduled and payment.date_scheduled > _today
                else False)
            # -- end account banking
        # -- account_banking
        state = 'structured'
        communication = line.ref or '-'
        if line.invoice:
            if line.invoice.reference_type == 'structured':
                state = 'structured'
                # Fallback to invoice number to keep previous behaviour
                communication = line.invoice.reference or line.invoice.number
            else:
                if line.invoice.type in ('in_invoice', 'in_refund'):
                    communication = (
                        line.invoice.reference or
                        line.invoice.supplier_invoice_number or line.ref)
                else:
                    # Make sure that the communication includes the
                    # customer invoice number (in the case of debit order)
                    communication = line.invoice.number
        # support debit orders when enabled
        if line.debit > 0:
            amount_currency = line.amount_residual_currency * -1
        else:
            amount_currency = line.amount_residual_currency
        if payment.payment_order_type == 'debit':
            amount_currency *= -1
        line2bank = line.line2bank(payment.mode.id)
        # -- end account banking
        res = {'move_line_id': line.id,
               'amount_currency': amount_currency,
               'bank_id': line2bank.get(line.id),
               'order_id': payment.id,
               'partner_id': line.partner_id and line.partner_id.id or False,
               # account banking
               'communication': communication,
               'state': state,
               # end account banking
               'date': date_to_pay,
               'currency': (line.invoice and line.invoice.currency_id.id or
                            line.journal_id.currency.id or
                            line.journal_id.company_id.currency_id.id)}
        return res

    @api.multi
    def create_payment(self):
        """This method is a slightly modified version of the existing method on
        this model in account_payment.
        - pass the payment mode to line2bank()
        - allow invoices to create influence on the payment process: not only
          'Free' references are allowed, but others as well
        - check date_to_pay is not in the past.
        """
        if not self.entries:
            return {'type': 'ir.actions.act_window_close'}
        context = self.env.context
        payment_line_obj = self.env['payment.line']
        payment = self.env['payment.order'].browse(context['active_id'])
        # Populate the current payment with new lines:
        for line in self.entries:
            vals = self._prepare_payment_line(payment, line)
            payment_line_obj.create(vals)
        # Force reload of payment order view as a workaround for lp:1155525
        return {'name': _('Payment Orders'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'payment.order',
                'res_id': context['active_id'],
                'type': 'ir.actions.act_window'}

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Slobodni programi d.o.o. (<http://www.slobodni-programi.com>).
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
import poziv_na_broj as pnbr

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import time


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.cr_uid_context
    def _get_reference_type(self, cursor, user, context=None):
        res = super(account_invoice, self)._get_reference_type(cursor, user, context=context)
        res.append(('pnbr_hr', 'Poziv na br.(HR)'))
        return res

    def _get_default_reference_type(self):
        inv_type = self.type or self._context.get('type', 'in_invoice')
        company_id = self.company_id or self._context.get('company_id', self.env.user.company_id)
        if inv_type in ('out_invoice'):
            if company_id.country_id and company_id.country_id.code in ('HR'):
                return 'pnbr_hr'
        return 'none'

    reference_type = fields.Selection('_get_reference_type',
                                      default=_get_default_reference_type)
    date_delivery = fields.Date('Delivery Date', readonly=True,
                                states={'draft': [('readonly', False)]},
                                copy=False, select=True,
                                help="Keep empty to use the current date")
    fiscalyear_id = fields.Many2one(comodel_name='account.fiscalyear',
                                    related='period_id.fiscalyear_id',
                                    readonly=True, store=True, string='Fiscal Year')
    # ex supplier_number is now supplier_invoice_number
    _sql_constraints = [
        # Original:
        # ('number_uniq', 'unique(number, company_id, journal_id, type)', 'Invoice Number must be unique per Company!'),
        ('number_uniq', 'unique(number, company_id, type, fiscalyear_id)',
         'Invoice Number must be unique per Company!'),
    ]

    @api.multi
    def pnbr_get(self):
        invoice = self
        res = self.reference or self.number or ''

        def getP1_P4data(what):
            res = ""
            if what == 'partner_code':
                res = invoice.partner_id.code or invoice.partner_id.id
            if what == 'partner_id':
                res = str(invoice.partner_id.id)
            if what == 'invoice_no':
                res = invoice.number
            if what == 'invoice_ym':
                res = invoice.date_invoice[2:4] + invoice.date_invoice[5:7]
            if what == 'delivery_ym':
                res = invoice.date_delivery[2:4] + invoice.date_delivery[5:7]
            return self._convert_ref(res)

        if invoice.journal_id.model_pnbr > 'HR':
            model = invoice.journal_id.model_pnbr
            P1 = getP1_P4data(invoice.journal_id.P1_pnbr or '')
            P2 = getP1_P4data(invoice.journal_id.P2_pnbr or '')
            P3 = getP1_P4data(invoice.journal_id.P3_pnbr or '')
            P4 = getP1_P4data(invoice.journal_id.P4_pnbr or '')
            res = pnbr.reference_number_get(model, P1, P2, P3, P4)
            res = model + ' ' + res
        return res

    @api.multi
    def _convert_ref(self, ref):
        #ref = super(account_invoice, self)._convert_ref( ref)
        res = ''
        if ref:
            for ch in ref:
                res = res + (ch.isdigit() and ch or '')
        return res

    @api.multi
    def action_number(self):
        #TODO: not correct fix but required a fresh values before reading it.
        self.write({})

        for inv in self:
            # TODO: propose PR for BUG
            # self.write({'internal_number': inv.number}) reason for copy-pase method
            inv.write({'internal_number': inv.number})

            if inv.type in ('in_invoice', 'in_refund'):
                if not inv.reference:
                    ref = inv.number
                else:
                    ref = inv.reference
            else:
                ref = inv.number
                #DECODIO - start
                if not inv.date_invoice:
                    self.write({'date_invoice': time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
                if not inv.date_delivery:  # mandatory in Croatia for services
                    self.write( {'date_delivery': inv.date_invoice})
                ref = inv.pnbr_get()
                self.write({'reference': ref})
                #DECODIO - end

            self._cr.execute(""" UPDATE account_move SET ref=%s
                           WHERE id=%s AND (ref IS NULL OR ref = '')""",
                        (ref, inv.move_id.id))
            self._cr.execute(""" UPDATE account_move_line SET ref=%s
                           WHERE move_id=%s AND (ref IS NULL OR ref = '')""",
                        (ref, inv.move_id.id))
            self._cr.execute(""" UPDATE account_analytic_line SET ref=%s
                           FROM account_move_line
                           WHERE account_move_line.move_id = %s AND
                                 account_analytic_line.move_id = account_move_line.id""",
                        (ref, inv.move_id.id))
            self.invalidate_cache()

        return True

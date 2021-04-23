# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: account_storno
#    Author: Goran Kliska
#    mail:   gkliskaATgmail.com
#    Copyright (C) 2013- Slobodni programi d.o.o., Zagreb
#    Contributions: 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def line_get_convert(self, line, part):
        res = super(account_invoice, self).line_get_convert(line, part)

        def convert_reverse_vat(line):
            credit = debit = 0.0
            if self.type in ('out_invoice', 'out_refund'):
                if line.get('type','src') in ('dest'):
                    credit = line['price'] * (-1)
                else:
                    debit = line['price']
            else:
                if line.get('type','src') in ('dest'):
                    debit = line['price'] * (-1)
                else:
                    credit = line['price'] * (-1)
            return credit, debit

        if self.journal_id.posting_policy == 'storno':
            credit = debit = 0.0
            reverse = False
            if self.journal_id.reverse_posting == True and \
               line.get('account_id', False) == self.account_id.id:
                reverse = True
            if line.get('reverse_vat', False) or reverse == True:
                credit, debit = convert_reverse_vat(line)
            else:
                if self.type in ('out_invoice', 'out_refund'):
                    if line.get('type','src') in ('dest'):
                        debit = line['price']
                    else:
                        credit = line['price'] * (-1)
                else:
                    if line.get('type','src') in ('dest'):
                        credit = line['price'] * (-1)
                    else:
                        debit = line['price']

            res['debit'] = debit
            res['credit'] = credit
            if res.get('tax_amount',False) and abs(res['tax_amount']) > 0.00:  # KGB tired, alternative implementation with pg trigger
                res['tax_amount'] = res['debit'] + res['credit']
        return res

    @api.model
    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if self.journal_id.group_invoice_lines:
            if self.journal_id.posting_policy == 'contra':
                return super(account_invoice, self).group_lines(iml, line)
            if self.journal_id.posting_policy == 'storno':
                line2 = {}
                for x, y, l in line:
                    hash = self.inv_line_characteristic_hashcode(l)
                    side = abs(l['credit']) > 0.0 and 'credit' or 'debit'
                    if l['credit'] == 0.00 and l['debit'] == 0:
                        tmp_c = '-'.join((hash, 'credit'))
                        side = (tmp_c in line2) and 'credit' or side
                    tmp = '-'.join((hash, side))
                    if tmp in line2:
                        line2[tmp]['debit'] += l['debit'] or 0.0
                        line2[tmp]['credit'] += l['credit'] or 0.00
                        line2[tmp]['tax_amount'] += l['tax_amount']
                        line2[tmp]['analytic_lines'] += l['analytic_lines']
                        line2[tmp]['amount_currency'] += l['amount_currency']
                        line2[tmp]['quantity'] += l['quantity']
                    else:
                        line2[tmp] = l
                line = []
                for key, val in line2.items():
                    line.append((0, 0, val))
        return line

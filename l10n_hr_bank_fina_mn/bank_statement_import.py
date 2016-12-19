# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014- Slobodni programi (<http://www.slobodni-programi.hr>).
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsability of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs
#    End users who are looking for a ready-to-use solution with commercial
#    garantees and support are strongly adviced to contract a Free Software
#    Service Company
#
#    This program is Free Software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_bank_statement_imports(orm.Model):
    """
    Account bank Statements files for import.
    """
    _name = 'account.bank.statement.imports'
    _description = "Account bank Statement imports"

    _columns = {
        'name': fields.char('File Name', size=128, readonly=True),
        'date_create': fields.date('Create Date', readonly=True, select=True),
        'import_date': fields.date('Import Date', required=True, select=True),
        'statement_file': fields.binary('File', readonly=True),
        'bank_code': fields.char('Bank Code', size=7, readonly=True),
        'bank_name': fields.char('Bank Name', size=50, readonly=True),
        'bank_vat_number': fields.char('Source VAT no.', size=11, readonly=True),
        'statement_ids': fields.one2many('account.bank.statement', 'statement_file_id',
                                          'Imported Bank Statements', readonly=True),
        'import_log': fields.text('Import Log', readonly=True),
        'user_id': fields.many2one('res.users', 'User', readonly=True, select=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'import_date': fields.date.context_today,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr,
                        uid, 'account.bank.statement.imports', context=c),
    }

    _order = 'date_create desc'

    _sql_constraints = [
        ('file_uniq', 'unique (name, date_create)', 'Another file with same name and date already exists!')
    ]

    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.statement_ids:
                raise orm.except_orm(_('Error!'),
                     _('You cannot delete bank statement file "%s" becouse \n'
                     ' bank statemnt lines exist for this line!') % (rec.name,))
        return super(account_bank_statement_imports, self).unlink(cr, uid, ids, context=context)

#account_bank_statement_imports()


class account_bank_statement(orm.Model):
    _inherit = "account.bank.statement"

    _columns = {
        'statement_file_id': fields.many2one('account.bank.statement.imports',
                                             'Bank Statement File', readonly=True),
    }

    def update_partners_payments(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        for statement in self.browse(cr, uid, ids, context=context):
            if statement.state != 'draft':
                continue
            line_ids = []
            for line in statement.line_ids:
                if line.type == 'general' and line.account_id:
                    continue
                line_ids.append(line.id)
                partner_id = line.partner_id and line.partner_id.id or False
                if not partner_id:
                    vals = bank_st_line_obj.search_partner(cr, uid, ids, {
                        'name': line.name,
                        'ref': line.ref,
                        'bank_acc_number': line.bank_acc_number,
                        'fina_branch_code': line.fina_branch_code,
                        'type': line.type,
                        'amount': line.debit_amount or line.credit_amount or 0.0,
                    }, context=context).get('value')
                    partner_id = vals.get('partner_id')
                    if partner_id:
                        bank_st_line_obj.write(cr, uid, [line.id], vals, context=context)
                    elif vals.get('account_id') and vals.get('type') == 'general':
                        bank_st_line_obj.write(cr, uid, [line.id], vals, context=context)
                        continue
                    else:
                        continue
                if line.bank_acc_number:
                    line_ids2 = bank_st_line_obj.search(cr, uid, [
                        ('statement_id', '=', line.statement_id.id),
                        ('partner_id','=',False),
                        ('bank_acc_number','=',line.bank_acc_number),
                    ], context=context)
                    for line2 in bank_st_line_obj.browse(cr, uid, line_ids2, context=context):
                        line_id = line2.id
                        partner = partner_obj.browse(cr, uid, partner_id, context=context)
                        if line2.debit_amount == 0.0:
                            type = 'supplier'
                            account_id = partner.property_account_payable and partner.property_account_payable.id or False
                        else:
                            type = 'customer'
                            account_id = partner.property_account_receivable and partner.property_account_receivable.id or False
                        if partner_id and account_id:
                            bank_st_line_obj.write(cr, uid, [line_id], {'partner_id': partner_id, 'type': type, 'account_id': account_id}, context=context)

            #bank_st_line_obj.create_voucher(cr, uid, line_ids, context=context)

        return True

    def add_bank_accounts_from_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        partner_bank_obj = self.pool.get('res.partner.bank')
        bank_obj = self.pool.get('res.bank')
        message = ''

        for statement in self.browse(cr, uid, ids, context=context):
            for line in statement.line_ids:
                if not (line.bank_acc_number and line.partner_id):
                    continue
                partner_bank_ids = partner_bank_obj.search(cr, uid, [
                    ('acc_number', '=', line.bank_acc_number),
                    ('partner_id.active', '=', True),
                ], context=context)
                if not partner_bank_ids:
                    partner_bank_ids = partner_bank_obj.search(cr, uid, [
                        ('acc_number', '=', _format_data(line.bank_acc_number)),
                        ('partner_id.active', '=', True),
                    ], context=context)
                if not partner_bank_ids and len(line.bank_acc_number) == 17:
                    partner_bank_ids = partner_bank_obj.search(cr, uid, [
                        ('acc_number', '=', line.bank_acc_number[:7] + '-' + line.bank_acc_number[7:]),
                        ('partner_id.active', '=', True),
                    ], context=context)
                if partner_bank_ids:
                    for partner_bank in partner_bank_obj.browse(cr, uid, partner_bank_ids, context=context):
                        if partner_bank.partner_id and partner_bank.partner_id.id != line.partner_id.id:
                            message += _('Nonconformity. The bank account number "%s" is entered in the bank statement line "%s" for the partner "%s". This is the same bank account number already registered for the partner "%s".\n') % \
                                (line.bank_acc_number, line.name, line.partner_id.name, partner_bank.partner_id.name)
                    continue
                if line.bank_acc_number[:2] == 'HR':
                    vbb_code = line.bank_acc_number[4:11]
                else:
                    vbb_code = line.bank_acc_number[:7]
                bank = False
                bank_ids = bank_obj.search(cr, uid, [('vbb_code', '=', vbb_code)], context=context)
                if bank_ids:
                    bank = bank_obj.browse(cr, uid, bank_ids[0], context=context)
                vals = {
                    'state': line.bank_acc_number[:1] > '9' and 'iban' or 'bank',
                    'acc_number': line.bank_acc_number,
                    'partner_id': line.partner_id.id,
                    'owner_name': line.partner_id.name,
                    'bank': bank and bank.id or False,
                    'bank_name': bank and bank.name or False,
                    'bank_bic': bank and bank.bic or False,
                }
                partner_bank_obj.create(cr, uid, vals, context=context)
                message += _('Added bank account number "%s" for the partner "%s".\n') % (line.bank_acc_number, line.partner_id.name)

        if not message:
            message = _('There are no updates. All partners already have bank accounts.')
            warning = {
                'title': _('Warning!'),
                'message': message
            }
            return {'value': {}, 'warning': warning}
        #res = self.pool.get('message.interface').create_message_interface(cr, uid,
                           #_('Add partner bank accounts'), message, context=context)

        return False


class account_bank_statement_line(orm.Model):
    _inherit = "account.bank.statement.line"

    _columns = {
        'bank_acc_number': fields.char('Bank Account Number', size=64),
        'fina_branch_code': fields.char('FINA Branch Code', size=5),
    }

    def _search_by_ref_exact_amount(self, cr, uid, line, move_line_obj, field_map={}, context=None):
        ref_field = field_map.get('ref', False)
        if not ref_field:
            return []
        if line.get('type') == 'customer':
            move_line_ids = move_line_obj.search(cr, uid,
                   [(ref_field, '=', line.get('ref')),
                    ('reconcile_id', '=', False),
                    ('account_id.reconcile', '=', True),
                    ('debit', '=', line.get('amount', 0.0))],
                context=context)
        elif line.get('type') == 'supplier':
            move_line_ids = move_line_obj.search(cr, uid,
                   [(ref_field, '=', line.get('ref')),
                    ('reconcile_id', '=', False),
                    ('account_id.reconcile', '=', True),
                    ('credit', '=', line.get('amount', 0.0))],
                context=context)
        return move_line_ids

    def _search_by_ref_amount(self, cr, line, move_line_ids, field_map={}, context=None):
        ref_field = field_map.get('ref', False)
        if not ref_field:
            return []
        line_obj = self.pool.get('account.move.line')
        ref_field_var = 'm.' + ref_field
        move_line_ids = []
        cr.execute("""
        SELECT m.id
        FROM account_move_line m
        WHERE %s = %s AND
            m.reconcile_id IS NULL AND
            m.account_id in (SELECT a.id FROM account_account a WHERE a.reconcile IS TRUE) AND
            ABS(m.debit - m.credit) = %s
    """, (ref_field_var, line.get('ref'), line.get('amount', 0.0)))
        for ml_id in cr.fetchall():
            move_line_ids.append[ml_id]
        return move_line_ids

    def _search_by_ref(self, cr, uid, line, move_line_obj, field_map={}, context=None):
        ref_field = field_map.get('ref', False)
        if not ref_field:
            return []
        move_line_ids = move_line_obj.search(cr, uid,
               [(ref_field, '=', line.get('ref')),
                ('reconcile_id', '=', False),
                ('account_id.reconcile', '=', True)],
            context=context)
        return move_line_ids

    def _get_open_move_line_ids(self, cr, uid, line, context=None):
        if line is None:
            return []
        move_line_obj = self.pool.get('account.move.line')
        move_line_ids = []
        field_map = {'ref': 'payment_ref'}
        if line.get('ref') and line.get('amount'):
            # search by payment reference and exact amount
            move_line_ids = self._search_by_ref_exact_amount(cr, uid, line, move_line_obj, field_map, context=context)

            if not move_line_ids:
                # search by payment reference and amount
                move_line_ids = self._search_by_ref_amount(cr, line, move_line_ids, field_map, context=context)

            if not move_line_ids:
                # search only by payment reference
                move_line_ids = self._search_by_ref(cr, uid, line, move_line_obj, field_map, context=context)

            if not move_line_ids:
                field_map = {'ref': 'ref'}
                # search by ref and exact amount
                move_line_ids = self._search_by_ref_exact_amount(cr, uid, line, move_line_obj, field_map, context=context)

            if not move_line_ids:
                # search by ref and amount
                move_line_ids = self._search_by_ref_amount(cr, line, move_line_ids, field_map, context=context)

            if not move_line_ids:
                # search by ref
                move_line_ids = self._search_by_ref(cr, uid, line, move_line_obj, field_map, context=context)

        return move_line_ids

    def search_partner(self, cr, uid, ids, line, context=None):
        if line is None:
            line = {}
        if context is None:
            context = {}

        partner_obj = self.pool.get('res.partner')
        partner_bank_obj = self.pool.get('res.partner.bank')
        move_line_obj = self.pool.get('account.move.line')

        warning = False
        partner_id = False
        account_id = False
        bank_acc_number = line.get('bank_acc_number')

        move_line_ids = self._get_open_move_line_ids(cr, uid, line, context=context)   # search by ref and amount
        if move_line_ids and len(move_line_ids) == 1:
            partner = move_line_obj.read(cr, uid, move_line_ids[0], ['partner_id'], context=context).get('partner_id')
            partner_id = partner and partner[0] or False
        elif move_line_ids and len(move_line_ids) > 1:
            partner_ids = []
            for move_line in move_line_obj.read(cr, uid, move_line_ids, ['partner_id'], context=context):
                partner = move_line.get('partner_id')
                if not partner:
                    partner_ids = []
                    break
                elif partner[0] not in partner_ids:
                    partner_ids.append(partner[0])
            partner_id = partner_ids and len(partner_ids) == 1 and partner_ids[0] or False

        if bank_acc_number:   # search by bank account number
            partner_bank_ids = []

            pb_ids = partner_bank_obj.search(cr, uid, [
                ('acc_number', '=', bank_acc_number),
                ('partner_id.active', '=', True),
            ], context=context)
            partner_bank_ids.extend(pb_ids)

            pb_ids = partner_bank_obj.search(cr, uid, [
                ('acc_number', '=', _format_data(bank_acc_number)),
                ('partner_id.active', '=', True),
            ], context=context)
            partner_bank_ids.extend(pb_ids)

            if len(bank_acc_number) == 17:
                pb_ids = partner_bank_obj.search(cr, uid, [
                    ('acc_number', '=', bank_acc_number[:7] + '-' + bank_acc_number[7:]),
                    ('partner_id.active', '=', True),
                ], context=context)
                partner_bank_ids.extend(pb_ids)

            partner_ids = []
            for partner_bank in partner_bank_obj.browse(cr, uid, partner_bank_ids, context=context):
                if partner_bank.partner_id and partner_bank.partner_id.active and partner_bank.partner_id.id not in partner_ids:
                    partner_ids.append(partner_bank.partner_id.id)

            if len(partner_ids) == 1:
                if not partner_id:
                    partner_id = partner_ids[0]
                elif partner_id and partner_id != partner_ids[0]:
                    partner_id = False   # ambiguous - better
            elif len(partner_ids) > 1:
                partner_id = False
                warning = _('\nNonconformity! This bank account is registered on more than one partner:')
                for partner in partner_obj.read(cr, uid, partner_ids, ['name'], context=context):
                    warning += '\n    ' + partner.get('name', '')

        if partner_id:
            if move_line_ids and len(move_line_ids) == 1:   # take the account from move line
                account_id = move_line_obj.browse(cr, uid, move_line_ids[0], context=context).account_id.id
            else:   # take the force account from journal or from partner
                account_id = line.get('force_account_id', False) or False
                if not account_id:
                    partner = partner_obj.browse(cr, uid, partner_id, context=context)
                    if line.get('type') == 'customer':
                        account_id = partner.property_account_receivable.id
                    elif line.get('type') == 'supplier':
                        account_id = partner.property_account_payable.id
                    else:
                        partner_id = False

        result = {'value': {'partner_id': partner_id, 'account_id': account_id}}
        if warning:
            result.update({'warning': warning})
        return result

    def create_voucher(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_line_obj = self.pool.get('account.move.line')
        voucher_obj = self.pool.get('account.voucher')

        for st_line in self.browse(cr, uid, ids, context=context):
            if not st_line.partner_id:
                continue
            if st_line.voucher_id:
                continue

            line = {
                'ref': st_line.ref,
                'type': st_line.type,
                #'amount': (not st_line.correction and abs(st_line.amount)) or (st_line.correction and abs(st_line.amount) * -1.0),
                'amount': abs(st_line.amount),
            }
            move_line_ids = self._get_open_move_line_ids(cr, uid, line, context=context)   # search by ref and amount

            if move_line_ids and len(move_line_ids) > 1:
                partner_ids = []
                invoice_ids = []
                for move_line in move_line_obj.read(cr, uid, move_line_ids, ['partner_id', 'invoice'], context=context):
                    partner = move_line.get('partner_id')
                    if not partner:
                        partner_ids = []
                        invoice_ids = []
                        break
                    elif partner[0] not in partner_ids:
                        partner_ids.append(partner[0])

                    invoice = move_line.get('invoice')
                    if not invoice:
                        partner_ids = []
                        invoice_ids = []
                        break
                    elif invoice[0] not in invoice_ids:
                        invoice_ids.append(invoice[0])

                partner_id = partner_ids and len(partner_ids) == 1 and partner_ids[0] or False
                invoice_id = invoice_ids and len(invoice_ids) == 1 and invoice_ids[0] or False
                if not partner_id and not invoice_id:
                    move_line_ids = []

            if move_line_ids:
                context.update({'move_line_ids': move_line_ids})   # voucher_obj.onchange_partner_id will search only this ids
                voucher_partner = voucher_obj.onchange_partner_id(
                    cr, uid, [],
                    partner_id=st_line.partner_id.id,
                    journal_id=st_line.statement_id.journal_id.id,
                    amount=abs(st_line.amount),
                    currency_id=st_line.statement_id.journal_id.company_id.currency_id.id,
                    ttype=st_line.type == 'supplier' and 'payment' or 'receipt',
                    date=st_line.date,
                    context=context
                )
                if st_line.type == 'customer' and voucher_partner['value']['line_cr_ids']:
                    voucher_partner_lines = voucher_partner['value']['line_cr_ids']
                elif st_line.type == 'supplier' and voucher_partner['value']['line_dr_ids']:
                    voucher_partner_lines = voucher_partner['value']['line_dr_ids']
                else:
                    voucher_partner_lines = False

                if voucher_partner_lines:
                    voucher_line_vals = []
                    closing_entry_names = []
                    open_amount = abs(st_line.amount)

                    for voucher_partner_line in voucher_partner_lines:
                        if not open_amount:
                            break
                        if voucher_partner_line['move_line_id'] not in move_line_ids:
                            continue
                        if open_amount > abs(voucher_partner_line.get('amount_unreconciled', 0.0)):
                            amount = abs(voucher_partner_line.get('amount_unreconciled', 0.0))
                        else:
                            amount = open_amount
                        voucher_partner_line.update({'amount': amount, 'reconcile': True})
                        open_amount -= amount
                        closing_entry_name = voucher_partner_line.get('name')
                        if closing_entry_name and closing_entry_name not in closing_entry_names:
                            closing_entry_names.append(closing_entry_name)
                        voucher_line_vals.append((0, 0, voucher_partner_line))

                    if voucher_line_vals:
                        voucher_vals = {
                            'type': st_line.type == 'supplier' and 'payment' or 'receipt',
                            'name': st_line.name,
                            'reference': st_line.ref,
                            'partner_id': st_line.partner_id.id,
                            'journal_id': st_line.statement_id.journal_id.id,
                            'account_id': voucher_partner.get('value', {}).get('account_id', False),
                            'company_id': st_line.statement_id.journal_id.company_id.id,
                            'currency_id': st_line.statement_id.journal_id.company_id.currency_id.id,
                            'date': st_line.date,
                            'period_id': st_line.statement_id.period_id.id,
                            'amount': abs(st_line.amount),
                            'is_multi_currency': False,
                            'pre_line': voucher_partner.get('value', {}).get('pre_line', False),
                            'line_ids': voucher_line_vals,
                        }
                        voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=context)

                        st_line_vals = {
                            'voucher_id': voucher_id,
                            'closing_entry_name': ','.join(closing_entry_names),
                        }
                        self.write(cr, uid, [st_line.id], st_line_vals, context=context)

        return True


def _format_data(string):
    '''returns string grouped by four characters separated by a single space.
    Used for IBAN numbers, Payment reference code, etc.
    '''
    result = []
    while string:
        result.append(string[:4])
        string = string[4:]
    return ' '.join(result)

# Copyright 2020 Decodio Applications
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import tools, models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    check_side = fields.selection(
        [('credit', 'Credit'),
         ('debit', 'Debit'), ],
        'Check/force side',
        required=False,
        help="Check that all postings on this account are done "
             "on credit or debit side only.\n"
             "This rule is not applied on year closing/opening periods.\n"
    )


class AccountJournal(models.Model):
    _inherit = "account.journal"

    posting_policy = fields.selection(
        [('contra', 'Contra (debit<->credit)'),
         ('storno', 'Storno (-)'), ],
        'Storno or Contra', size=16, required=True, default='storno',
        help="Storno allows minus postings, "
             "Refunds are posted on the same joural/account * (-1).\n"
             "Contra doesn't allow negative posting. "
             "Refunds are posted by swapping credit and debit side."
    )
    refund_journal_id = fields.many2one(
        'account.journal', 'Refund journal',
        help="Journal for refunds/returns from this journal. Leave empty to "
             "use same journal for normal and refund/return postings.",
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #Original constraints
    # _sql_constraints = [
    #     ('credit_debit1', 'CHECK (credit*debit=0)', 'Wrong credit or debit value in accounting entry! Credit or debit should be zero.'),
    #     ('credit_debit2', 'CHECK (credit+debit>=0)', 'Wrong credit or debit value in accounting entry! Credit and debit should be positive.'),
    # ]
    # credit_debit1 is valid constraint. Clear message
    # credit_debit2 is replaced with dummy constraint that is always true.

    _sql_constraints = [
        ('credit_debit1', 'CHECK (credit*debit=0)', 'Wrong credit or debit value in accounting entry! Either credit or debit must be 0.00.'),
       #('credit_debit2', 'CHECK (abs(credit+debit)>=0)', 'Wrong credit or debit value in accounting entry !'),  # Does nothing, maybe one day (abs(credit+debit)>0.0)
    ]

    def _auto_init(self, cr, context=None):
        result = super(account_move_line, self)._auto_init(cr, context=context)
        # Remove constrains for credit_debit1, credit_debit2
        cr.execute("""
            ALTER TABLE account_move_line DROP CONSTRAINT IF EXISTS account_move_line_credit_debit2;
        """)
        return result


    def X_auto_init(self, cr, context=None):
        res = super(account_move_line, self)._auto_init(cr, context=context)
        cr.execute('''
                CREATE OR REPLACE FUNCTION debit_credit2tax_amount() RETURNS trigger AS
                $debit_credit2tax_amount$
                BEGIN
                   NEW.tax_amount := CASE when NEW.tax_code_id is not null
                                           then coalesce(NEW.credit, 0.00)+coalesce(NEW.debit, 0.00)
                                           else 0.00
                                      END;
                   RETURN NEW;
                END;
                $debit_credit2tax_amount$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS move_line_tax_amount ON account_move_line;
                CREATE TRIGGER move_line_tax_amount BEFORE INSERT OR UPDATE ON account_move_line
                    FOR EACH ROW EXECUTE PROCEDURE debit_credit2tax_amount();
        ''')
        return res


    def _check_contra_minus(self, cr, uid, ids, context=None):
        """ This is to restore credit_debit2 check functionality, for contra journals 
        """ #  TODO rewrite in SQL #
        for l in self.browse(cr, uid, ids, context=context):
            if l.journal_id.posting_policy == 'contra':
                if l.debit + l.credit < 0.0:
                    return False
        return True

    def _check_storno_tax(self, cr, uid, ids, context=None):
        """For Storno accounting Tax/Base amount is always == (debit + credit)
           Still trying to find the case where it is not.
           Maybe for contra check is abs(tax_amount) = abs(debit + credit) ???
        """
        return True #  TODO rewrite in SQL #
        for l in self.browse(cr, uid, ids, context=context):
            if l.tax_code_id and l.journal_id.posting_policy == 'storno':
                if float_compare((l.debit + l.credit), l.tax_amount, precision_digits=2) != 0:  # precision_digits=dp.get_precision('Account')[1])
                    return False
        return True

    def _check_side(self, cr, uid, ids, context=None):
        """For Storno accounting some account are using only one side during FY
        """
        return True #  TODO rewrite in SQL #
        for l in self.browse(cr, uid, ids, context=context):
            check_side = l.account_id.check_side
            if (check_side and
                check_side == 'debit' and abs(l.credit) > 0.0 or
                check_side == 'credit' and abs(l.debit) > 0.0):
                    return False
        return True

    _constraints = [
        #  TODO rewrite in SQL # (_check_contra_minus, _('Negative credit or debit amount is not allowed for "contra" journal policy.'), ['journal_id']),
        (_check_storno_tax, _('Invalid tax amount. Tax amount can be 0.00 or equal to (Credit + Debit).'), ['tax_amount']),
        (_check_side, _('Invalid side for account.'), ['account_id']),
    ]

    @api.multi
    @api.constrains('amount_currency', 'debit', 'credit')
    def _check_currency_amount(self):
        for line in self:
            if line.amount_currency:
                if (line.amount_currency > 0.0 and line.credit > 0.0) or (line.amount_currency < 0.0 and line.debit > 0.0):
                    raise ValidationError(_('The amount expressed in the secondary currency must be positive when account is debited and negative when account is credited.'))



class account_model_line(orm.Model):
    _inherit = "account.model.line"
    _sql_constraints = [
        ('credit_debit1', 'CHECK (credit*debit=0)', 'Wrong credit or debit value in model! Either credit or debit must be 0.00.'),
        ('credit_debit2', 'CHECK (abs(credit+debit)>=0)', 'Wrong credit or debit value in accounting entry !'),
    ]

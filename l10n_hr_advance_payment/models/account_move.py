from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def reverse_moves_insert_into_existing(self, date=None, journal_id=None, auto=False, existing_move=None):
        date = date or fields.Date.today()
        reversed_moves = self.env['account.move']
        for ac_move in self:
            # unreconcile all lines reversed
            aml = ac_move.line_ids.filtered(
                lambda x: x.account_id.reconcile or x.account_id.internal_type == 'liquidity')
            aml.remove_move_reconcile()
            reversed_move = ac_move._reverse_move(date=date,
                                                  journal_id=journal_id,
                                                  auto=auto)
            if existing_move:
                reversed_move.line_ids.write({'move_id': existing_move.id})
                reversed_move.unlink()
            reversed_moves |= existing_move or reversed_move
            # reconcile together the reconcilable (or the liquidity aml) and their newly created counterpart
            for account in set([x.account_id for x in aml]):
                to_rec = aml.filtered(lambda y: y.account_id == account)
                to_rec |= existing_move.line_ids.filtered(lambda y: y.account_id == account)
                # reconciliation will be full, so speed up the computation by using skip_full_reconcile_check in the context
                to_rec.reconcile()
        if reversed_moves:
            reversed_moves._post_validate()
            reversed_moves.post()
            return [x.id for x in reversed_moves]
        return []

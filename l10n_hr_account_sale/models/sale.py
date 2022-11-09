from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Sale(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _prepare_invoice(self):
        """
        gereate invoice vasl form super call,
        then check if journal is correct, and according to journal settings,
        update fiskal data
        :return:
        """
        self.ensure_one()
        invoice_vals = super(Sale, self)._prepare_invoice()
        if self.company_id.croatia:
            invoice_vals['fiskal_user_id'] = self.env.user.id
            team_journal = self.team_id.journal_id
            user_default_uredjaj = self.env.user.default_uredjaj
            user_uredjaj_ids = set(self.env.user.uredjaj_ids)
            fiskal_uredjaj_id = user_default_uredjaj
            sj_uredjaj_ids = None
            if team_journal:
                sj_uredjaj_ids = set(team_journal.fiskal_uredjaj_ids)
            if sj_uredjaj_ids is not None and \
                    user_default_uredjaj not in sj_uredjaj_ids:
                uj_uredaji = user_uredjaj_ids & sj_uredjaj_ids
                fiskal_uredjaj_id = uj_uredaji[0]
            if team_journal and team_journal.id != invoice_vals.get('journal_id'):
                invoice_vals['journal_id'] = team_journal.id
            invoice_vals['fiskal_uredjaj_id'] = fiskal_uredjaj_id.id
        return invoice_vals


    # def _finalize_invoices(self, invoices, references):
    #     """
    #     need to check for original method because it is not aware of
    #     account_storno existance and turnsa negative amounts to positive refunds
    #     :return:
    #     """
    #     if self.team_id.journal_id and self.team_id.journal_id.posting_policy == 'storno':
    #         pass

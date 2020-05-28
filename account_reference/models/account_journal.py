# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"


    def _get_P1_P4_selection(self):
        return ([
            ('null', 'Nothing'),
            ('partner_code', 'Partner code'),
            ('partner_id', 'Partner ID'),
            ('invoice_no', 'Invoice Number'),
            ('delivery_ym', 'Delivery year and month'),
            ('invoice_ym', 'Invoice year and month')])

    _P1_P4_selection = lambda self: self._get_P1_P4_selection()

    country_prefix = fields.Boolean(
        string='Add country code as prefix', default='True')
    # FIELDS
    model_pnbr = fields.Selection(
        selection=[
            ('00', '00 - No controll'),
            ('01', '01 - P1-P2-P3  [k(P1,P2,P3)]'),
            ('02', '02 - P1-P2-P3  [k(P2), k(P3)]'),
            ('03', '03 - P1-P2-P3  [k(P1), k(P2), k(P3)]'),
            ('06', '06 - P1-P2-P3  [k(P2,P3)]'),
            ('99', '99 - No controll')],
        string='Model', help='Reference type model')
    P1_pnbr = fields.Selection(
        selection=_P1_P4_selection,
        string='P1', help='1. polje poziva na broj.')
    P2_pnbr = fields.Selection(
        selection=_P1_P4_selection,
        string='P2', help='2. polje poziva na broj.')
    P3_pnbr = fields.Selection(
        selection=_P1_P4_selection,
        string='P3', help='3. polje poziva na broj.')
    P4_pnbr = fields.Selection(
        selection=_P1_P4_selection,
        string='P4', help='4. polje poziva na broj.')


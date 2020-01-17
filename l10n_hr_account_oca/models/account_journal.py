# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # original fields modification
    code = fields.Char(size=16)   # DB: default size 5 mi se cini premalecki...

    # new fields needed for localization
    prostor_id = fields.Many2one(
        comodel_name='fiskal.prostor',
        string='Prostor',
        help='Business premise')
    fiskal_uredjaj_ids = fields.Many2many(
        comodel_name='fiskal.uredjaj',
        relation='fiskal_uredjaj_account_journal_rel',
        column1='journal_id', column2='uredjaj_id',
        string='Dopusteni naplatni uredjaji')
    default_nacin_placanja = fields.Selection(
        selection=[('T', 'TRANSAKCIJSKI RAČUN')],
        string="Default fiskal payment method",
        default="T")
    croatia = fields.Boolean(related="company_id.croatia")

    # BOLE: ovo mozda kao config opciju?
    # @api.multi
    # @api.depends('name', 'currency_id', 'company_id', 'company_id.currency_id', 'prostor_id')
    # def name_get(self):
    #     """
    #     dodajem i naziv poslovnog prostora u name get
    #     :return:
    #     """
    #     res = []
    #     for journal in self:
    #         currency = journal.currency_id or journal.company_id.currency_id
    #         name = "%s (%s)" % (journal.name, currency.name)
    #         if journal.prostor_id:
    #             name += " - %s" % journal.prostor_id.oznaka_prostor
    #             uredjaj_sifre = [x.oznaka_uredjaj for x in journal.fiskal_uredjaj_ids
    #                              if journal.fiskal_uredjaj_ids]
    #             if uredjaj_sifre:
    #                 name += " %s" % str(uredjaj_sifre)
    #         res += [(journal.id, name)]
    #     return res



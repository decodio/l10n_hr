
from odoo import api, fields, models, _
from odoo.exceptions import Warning


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
    fiskal_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string="Responsible person",
        help="Default fiskal responsible person for this journal",
        # default=lambda self: self.env.company.fiskal_resbonsible_id or False
    )
    default_nacin_placanja = fields.Selection(
        selection=[('T', 'TRANSAKCIJSKI RAČUN')],
        string="Default fiskal payment method",
        default="T")
    croatia = fields.Boolean(related="company_id.croatia")



    # BOLE: ovo mozda kao config opciju?
    # @api.multi
    # @api.depends('name', 'currency_id', 'company_id',
    #              'company_id.currency_id', 'prostor_id')
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

    @api.multi
    def write(self, vals):
        """
        TODO: provjere validnosti
            1 - prostor: izdavanje računa na nivou uređaja:
                - samo jedan dozvoljeni uređaj
            2 - prostor: izdavanje računa na nivou prostora:
                - svi uređaji moraju biti iz istog prostora, i aktivni!
                - provjeri da li ima sequence id, ako nema dodaj!
            3. Sekvenca: Smije imati prefix,
                trenutno jedino podržano od dinamickih: %(year)s i %(y)s
                drugi prefiksi trebaju dopunu

            -> preferirati : Koristi sekvence po razdobljima ali netreba kontrola!
        """

        if vals.get('prostor_id') or vals.get('fiskal_uredjaj_ids'):
            self._check_write_vals(vals)
        return super(AccountJournal, self).write(vals)

    def _check_write_vals(self, vals):
        prostor_id = vals.get('prostor_id', False)
        if prostor_id:
            prostor = prostor_id and \
                      self.env['fiskal.prostor'].browse(prostor_id)
            msg = "Prostor: %s, " % prostor.name
            if prostor.sljed_racuna == 'P':
                if not prostor.sequence_id:
                    prostor.sequence_id = self.sequence_id
                elif prostor.sequence_id != self.sequence_id:
                    msg += "seqvenca: %s" % prostor.sequence_id.name
                    msg += " razlikuje se od sekvence na dnevniku!"
                    raise Warning(msg)

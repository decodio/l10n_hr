# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = 'res.users'

    prostor_ids = fields.Many2many(
        comodel_name='fiskal.prostor',
        relation='fiskal_prostor_res_users_rel',
        column1='user_id', column2='prostor_id',
        string='Dozvoljeni prostori',
        help="Dozvoljeni prostori za izdavanje računa")
    default_uredjaj = fields.Many2one(
        comodel_name='fiskal.uredjaj',
        string='Zadani nap. uređaj',)

    # DB: moved to account_journal_user_control
    # default_journal = fields.Many2one(
    #     comodel_name='account.journal',
    #     string='Zadani dnevnik prodaje',
    #     domain="[('type', '=', 'sale')]")
    # journal_ids = fields.Many2many(
    #     comodel_name='account.journal',
    #     relation='user_account_journal_rel',
    #     column1='user_id', column2='journal_id',
    #     #domain="[('type', '=', 'sale')]",  # DB: bez domene, sugestija TB & GKB
    #     string='Dozvoljeni dnevnici prodaje')
    uredjaj_ids = fields.Many2many(
        comodel_name='fiskal.uredjaj',
        relation='fiskal_uredjaj_res_users_rel',
        column1='user_id', column2='uredjaj_id',
        string='Dozvoljeni naplatni uređaji')

    # @api.onchange('default_journal')
    # def _onchange_default_journal(self):
    #     # This only adds selected record, remove manualy
    #     if self.default_journal:
    #         self.journal_ids = [(4, self.default_journal.id)]

    @api.onchange('default_uredjaj')
    def _onchange_default_uredjaj(self):
        if self.default_uredjaj:
            allowed_premises = [ p.id for p in self.prostor_ids]
            if not self.uredjaj_ids:
                raise UserError(_('You have no allowed devices, setting defualt it not possible!'))
            allowed_devices = [d.id for d in self.uredjaj_ids]
            uredjaj = self.default_uredjaj.id
            if uredjaj not in allowed_devices:
                raise UserError(_("Selected device '%s' is not in allowed list!" %
                                  self.default_uredjaj.name_get()[0][1]))
            #self.uredjaj_ids = [(4, self.default_uredjaj.id)]  NE NEEEEE--- prvo dozvoli pa postavi default!!!

    # @api.onchange('uredjaj_ids')
    # def _onchange_uredjaj_ids(self):
    #     res = {}
    #     for user in self:
    #         res[user.id] = {'default_uredjaj':[('id', 'in', [u.id for u in user.uredjaj_ids])]}
    #     #print "TODO: stavi domenu na default uredjaj i dodaj dnevnike!"
    #     return {'domain': res}

    @api.one
    def get_all_uredjaj(self):
        if not self.prostor_ids:
            self.uredjaj_ids = [(5)]
            self.default_uredjaj = False
        else:
            uredjaji = []
            for prostor in self.prostor_ids:
                for uredjaj in prostor.uredjaj_ids:
                    uredjaji.append(uredjaj.id)
            if uredjaji:
                self.uredjaj_ids = [(6, 0, uredjaji)]
                self.default_uredjaj = uredjaji[0]


    # @api.multi
    # def write(self, vals):
    #     # if 'default_uredjaj' in vals.keys():
    #     #     def_ur = vals['default_uredjaj']
    #     #     for user in self:
    #     #         if def_ur not in [u.id for u in user.uredjaj_ids]:
    #     #             raise UserError(_("Selected device '%s' is not in allowed list!" %
    #     #                               self.env['fiskal.uredjaj'].browse(def_ur).name_get()))
    #     res = super(Users, self).write(vals)
    #     if 'journal_ids' in vals.keys():
    #         pass
    #     return res


# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    porezna_id = fields.Many2one(
        comodel_name='l10n.hr.porezna.uprava',
        string='Porezna uprava'
    )


class PoreznaUprava(models.Model):
    _name = 'l10n.hr.porezna.uprava'
    _description = "Popis poreznih uprava i ispostava u RH"

    name = fields.Char('Porezna ispostava', required=True)
    code = fields.Char('Code', size=4, required=True)
    porezna_uprava = fields.Char('Porezna uprava', required=True)

    @api.multi
    def name_get(self):
        res = []
        for c in self:
            res.append((c.id, "%s - %s, PU %s" % (c.code, c.name, c.porezna_uprava)))
        return res


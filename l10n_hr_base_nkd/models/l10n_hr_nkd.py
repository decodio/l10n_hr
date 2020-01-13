# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Nkd(models.Model):
    _name = 'l10n.hr.nkd'
    _description = 'HR NKD - Nacionalna klasifikacija djelatnosti'


    code = fields.Char('Code', size=16, required=True)
    name = fields.Char('Name', required=True)

    @api.multi
    def name_get(self):
        res = []
        for c in self:
            res.append((c.id, "%s - %s" % (c.code, c.name)))
        return res


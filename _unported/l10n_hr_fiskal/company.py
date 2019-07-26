# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    fina_certifikat = fields.Many2one(
        'crypto.certificate',
        string="Fiskal certifikat",
        domain="[('cert_type', 'in', ('fina_demo','fina_prod'))]", #todo company_id
        help="Aktivni FINA certifikat za fiskalizaciju.",
        )
    fiskal_prostor = fields.One2many(
        'fiskal.prostor',
        'company_id',
        string="Poslovni prostori",
        help="Poslovni prostori (fiskalizacija).",
        )


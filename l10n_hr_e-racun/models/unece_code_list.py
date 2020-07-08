# -*- coding: utf-8 -*-
# © 2019 Decodio (http://www.decod.io)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models, fields


class UneceCodeList(models.Model):
    _inherit = 'unece.code.list'

    type = fields.Selection(selection_add=[
        ('doc_type', 'Document Types (UNCL 1001)'),
        ])

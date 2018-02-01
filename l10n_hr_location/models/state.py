# -*- coding: utf-8 -*-
#
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
#

from openerp import models, fields


class ResCountryState(models.Model):

    _inherit = 'res.country.state'

    better_zip_ids = fields.One2many('res.better.zip', 'state_id', 'Cities')

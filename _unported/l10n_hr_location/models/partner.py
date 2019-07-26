# -*- coding: utf-8 -*-
#
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
#

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    zip_id = fields.Many2one('res.better.zip', 'City/Location')

    @api.one
    @api.onchange('zip_id')
    def onchange_zip_id(self):
        if self.zip_id:
            self.zip = self.zip_id.name
            self.city = self.zip_id.city
            self.state_id = self.zip_id.state_id
            self.country_id = self.zip_id.country_id

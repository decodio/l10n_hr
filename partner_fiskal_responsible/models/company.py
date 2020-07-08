# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    partner_name_order = fields.Selection(
        selection=[
            ('first-last', 'Firstname Lastname'),
            ('last-first', 'Lastname Firstname'),
            ('lastcfirst', 'Lastname, Firstname')
        ], string="Partner name display",
        default="first-last"
    )



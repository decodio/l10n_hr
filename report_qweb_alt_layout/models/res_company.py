# -*- coding: utf-8 -*-
# © 2018 DAJ MI 5 <https://www.dajmi5.hr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = "res.company"


    apply_alt_layout = fields.Boolean(
        string="Apply alt layout for this company",
        default=True
    )
    tax_no_print = fields.Boolean(
        string="Do not print taxes",
        help="if not in taxation system and do not want taxes printed"
    )
    address_space_side = fields.Selection(
        selection=[
            ('left', 'Left'),
            ('right', 'Right')],
        string='Address space side',
        default="left", required=True,
        help='Side where address will be printed')

    always_print_discount = fields.Boolean(
        string='Always print discount on invoice or sale order lines',
        default=True,
        help="If turned off, by default, discount column on sale order or invoice lines " \
             "will be printed only if applied on at least one line")

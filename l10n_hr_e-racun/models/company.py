# -*- encoding: utf-8 -*-
# © 2019 Decodio Applications d.o.o. (davor.bojkic@decod.io)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html).


from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    eracun_memorandum = fields.Text(
        string="UBL Company data",
        help="Input extra legal info for seller,\n"
             " For Croatia required elements are: \n"
             " Chamber of commerce, Initial capital,"
             " Owner and/or board members"
    )
    eracun_mail = fields.Char(
        related='partner_id.e_racun_mail',
        string='Accounting email',
        help='Email used for sending for e-invoices, '
             'required for e-invoice if different from main email,\n'
             'Plese set it on company related partner!'
    )


# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Decodio
# Copyright (C) 2012- Daj Mi 5 Davor Bojkić bole@dajmi5.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from OpenSSL import crypto
from openerp.exceptions import Warning as UserError
import base64


class Certificate(models.Model):
    _inherit = "crypto.certificate"

    def _get_cert_selection(self):
        return (('fina_demo', 'Fina Demo Certifiacte'),
                ('fina_prod', 'Fina Production Certificate'),
                ('personal', 'Personal Certificate'),
                ('other', 'Other types')
                )

    company_id = fields.Many2one(
        'res.company',
        'Tvrtka',
        default=lambda self: self.env['res.company']._company_default_get('crypto.certificate'),
        help='Cerificate is used for this company only.')
    group_id = fields.Many2one(
        'res.groups',
        'User group',
        select=True,
        help='Users who use the certificate.')
    cert_type = fields.Selection(
        _get_cert_selection,
        'Certificate Use')
    pfx_certificate = fields.Binary(
        'Certificate',
        help='Original Pfx File.')
    pfx_certificate_password = fields.Char(
        'Certificate password',
        help='Password for the Pfx File.')

    _defaults = {
         'state': 'draft',
         'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'crypto.certificate', context=c),
    }
    



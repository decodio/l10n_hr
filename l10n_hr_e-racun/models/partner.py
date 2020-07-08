# -*- encoding: utf-8 -*-
# © 2019 Decodio Applications d.o.o. (davor.bojkic@decod.io)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html).


import logging
from odoo import tools, models, fields, api, _
from odoo.exceptions import Warning

logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    e_racun_schema = fields.Selection(
        selection=[
            ('EN19631', 'UBL-2.1-EN19631-B2G'),
            ('HRINVOICE1', 'UBL-2.1-HRINVOICE1-B2B'),

        ], string="UBL Schema",
        help="Prefered UBL shema for generating e-invoice for this partner"
    )
    e_racun_mail = fields.Char(
        string='Accounting email',
        help='Email for sending e-invoices, '
             'required for e-invoice if different from main email'
    )
    ubl_doctype_ids = fields.Many2many(
        comodel_name='res.partner.ubl.doctype',
        relation='res_partner_ubldoctype_rel',
        column1='partner_id', column2='doctype_id',
        string='Available doctypes'
    )


class ResPartnerUblDocument(models.Model):
    """
    NO EDIT VIEWS! only tags on partner,
    """
    _name = 'res.partner.ubl.doctype'
    _descritpion = 'UBL doctypes that partner can process'

    @api.multi
    @api.depends('doc_type', 'schema')
    def _name_compute(self):
        for dt in self:
            schema = dt.schema == 'HRINVOICE1' and 'UBL-2.1-HR' or dt.schema
            dt.name = ' - '.join((schema, dt.doc_type.upper()))

    name = fields.Char(
        compute='_name_compute',
        store=True,
    )
    doc_type = fields.Selection(
        selection=[
            ('invoice', 'Invoice'),
            ('credit_note', 'Credit note'),
            ('reminder', 'Reminder')
        ], stirng="Document type", required=True
    )
    schema = fields.Selection(
        selection=[
            ('EN19631', 'EN19631-B2G'),
            ('HRINVOICE1', 'HRINVOICE1-B2B'),
        ], string="Schema", required=True
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='res_partner_ubldoctype_rel',
        column1='doctype_id', column2='partner_id',
        string='Assigned to partners'
    )

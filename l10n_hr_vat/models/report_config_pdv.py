# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ConfigReportPdv(models.Model):
    _name = 'l10n.hr.config.report.pdv'
    _inherit = 'report.config.croatia'

    xml_schema = fields.Selection(
        selection_add=[
            ('7.0', '7.0'),
            ('8.0', '8.0'),
            ('9.0', '9.0'),
        ]
    )
    line_ids = fields.One2many(
        comodel_name='l10n.hr.config.report.pdv.line',
        inverse_name='report_id',
        string='Report items'
    )


class ConfigReportPdvLine(models.Model):
    _name = 'l10n.hr.config.report.pdv.line'
    _inherit = 'report.config.croatia.line'

    company_id = fields.Many2one(
        comodel_name="res.company",
        string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get()
    )
    report_id = fields.Many2one(
        comodel_name='l10n.hr.config.report.pdv',
        string='Report'
    )
    parent_id = fields.Many2one(
        comodel_name='l10n.hr.config.report.pdv.line',
        string='Parent line',
    )
    child_ids = fields.One2many(
        comodel_name='l10n.hr.config.report.pdv.line',
        inverse_name='parent_id',
        string='Child lines'
    )
    xml_vals = fields.Selection(
        selection=[
            ('o', 'Osnovica'),
            ('op', 'Osnovica + Porez'),
            ('p', 'Porez'),
            ('ob', 'Osnovica + Broj'),
            ('s', 'Specijalno')
        ], string="XML Values"
    )
    config_ids = fields.One2many(
        comodel_name='l10n.hr.config.report.pdv.line.config',
        inverse_name='line_id',
        string='Setup',
        help='Porezi ili konta za ovu stavku'
    )
    parent_coef = fields.Float(
        string="Koeficijent", default=1,
        help="Koeficijent za zbrajanje u nadređenu stavku"
    )


class ConfigReportPdvLineConfig(models.Model):
    _name = 'l10n.hr.config.report.pdv.line.config'
    _description = "PDV Line taxes/accounts and coeficients"

    line_id = fields.Many2one(
        comodel_name='l10n.hr.config.report.pdv.line',
        string="Redak obrasca", required=True
    )
    name = fields.Char(
        related='line_id.name',
        string='Position',
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax'
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account'
    )
    coeficient = fields.Float(
        string="Koeficijent", default=1.0,
        help="Debit - Credit coeficient for this item"
    )
    position = fields.Selection(
        selection=[
            ('base', 'Osnovica'),
            ('tax', 'Porez'),
            ('basetax', 'Osnovica i porez')
        ],
        string='Pozicija u koloni', required=True,
        help='Primjena poreza ili konta za sumiranje u koloni'
    )



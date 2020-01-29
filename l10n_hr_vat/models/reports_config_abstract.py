# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportConfigCroatia(models.AbstractModel):
    _name = 'report.config.croatia'
    _description = "Abstract report config Croatia"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get()
    )
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('canceled', 'Canceled')
        ],
        string="State", default='draft', required=True
    )
    date_start = fields.Date()
    date_end = fields.Date()
    define = fields.Selection(
        selection=[
            ('row', 'Rows'),
            ('col', 'Columns')
        ],
        string='Struktura podataka', required=True
    )
    name_construct = fields.Selection(
        selection=[
            ('name', 'Name'),
            ('code', 'Code'),
            ('cdes', 'Code - Name'),
        ],
        string="Construct name", required=True, default='name'
    )
    xml_schema = fields.Selection(
        selection=[],  # Extend selection in other classes
        string='XML Shema')

    def button_confirm(self):
        self.state = 'confirm'

    def button_cancel(self):
        self.state = 'cancel'

    def button_set_draft(self):
        self.state = 'draft'


class ConfigReportCroatiaLine(models.AbstractModel):
    _name = 'report.config.croatia.line'
    _description = "Abstract report config line Croatia"


    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', required=True)

class ConfigReportCroatiaLineConfig(models.AbstractModel):
    _name = 'report.config.croatia.line.config'
    _description = "Abstract report config line config Croatia"


    filter_tax = fields.Boolean()
    filter_account = fields.Boolean()
    filter_journal = fields.Boolean()

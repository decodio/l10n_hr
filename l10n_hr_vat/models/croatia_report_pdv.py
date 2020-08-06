# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PdvObrazac(models.Model):
    _name = 'l10n.hr.pdv.obrazac'
    _description = 'Prijava PDV-a'

    company_id = fields.Many2one(
        comodel_name="res.company",
        string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(),
        readonly=True, states={'draft': [('readonly', False)]},
    )
    name = fields.Char(string="Name", readonly=1)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('cancel', 'Cancel')
        ], string="State", default='draft'
    )
    xml_schema = fields.Selection(
        selection=[
            ('7.0', '7.0'),
            ('8.0', '8.0'),
            ('9.0', '9.0'),
        ], string="Verzija",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    date_from = fields.Date(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    date_to = fields.Date(
        readonly=True, states={'draft': [('readonly', False)]},
    )

    # PDV data
    pdv_template_id = fields.Many2one(
        comodel_name='l10n.hr.config.report.pdv',
        string='PDV Template',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    pdv_line_ids = fields.One2many(
        comodel_name='l10n.hr.pdv.report.pdv',
        inverse_name='report_id',
        readonly=True, states={'draft': [('readonly', False)]},
        string='PDV')
    pdv_xml_file = fields.Binary('XML File', attachment=True)
    pdv_xml_file_name = fields.Char(string="PDV XML file")
    # PDV-S data
    pdvs_line_ids = fields.One2many(
        comodel_name='l10n.hr.pdv.report.pdvs',
        inverse_name='report_id',
        string='PDV-S')
    pdvs_xml_file = fields.Binary('XML File', attachment=True)
    pdvs_xml_file_name = fields.Char(string="PDV-S XML file")
    # PDV-ZP data
    pdvzp_line_ids = fields.One2many(
        comodel_name='l10n.hr.pdv.report.zp',
        inverse_name='report_id',
        string='ZP')
    pdvzp_xml_file = fields.Binary('XML File', attachment=True)
    pdvzp_xml_file_name = fields.Char(string="ZP XML file")

    # PDV-PPO DATA
    pdvppo_line_ids = fields.One2many(
        comodel_name='l10n.hr.pdv.report.ppo',
        inverse_name='report_id',
        string='PPO'
    )

    def _get_version(self):
        if self.date_to < '2013-07-01':
            res = '6.0'  # ObrazacPDV-v6-0
        elif '2013-07-01' <= self.date_to < '2014-01-01':
            res = '7.0'  # ObrazacPDV-v7-0
        elif '2014-01-01' <= self.date_to < '2015-01-01':
            res = '8.0'  # ObrazacPDV-v8-0
        elif '2015-01-01' <= self.date_to:
            res = '9.0'  # ObrazacPDV-v9-0
        return res

    @api.onchange('date_to')
    def onchange_date_to(self):
        if not self.date_to:
            return
        pdv_line_ids = [(2, p.id) for p in self.pdv_line_ids]

    @api.onchange('pdv_template_id')
    def _onchange_pdv_template_id(self):
        existing = [(2, p.id) for p in self.pdv_line_ids]
        new_lines = [(0, 0, {'stavka_id': tl.id})
                     for tl in self.pdv_template_id.line_ids.sorted('sequence')]
        self.pdv_line_ids = existing + new_lines


    def button_get_data(self):
        # 1. dohvat PDV stavaka
        self._get_pdv_data()
        # 2. dohvat PDVS
        # 3. dohvat ZP
        # 4. dohvat PPO
        return

    def _get_pdv_data(self):
        for pdv in self.pdv_line_ids:
            pass



class PdvObrazacStavka(models.AbstractModel):
    _name = 'l10n.hr.pdv.obrazac.line'
    _description = "Common abstrac report line model"
    _order = 'sequence, id'


    sequence = fields.Integer(
        string="R.br.", required=1
    )
    report_id = fields.Many2one(
        comodel_name='l10n.hr.pdv.obrazac',
        string='Report'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Partner"
    )
    state = fields.Selection(
        related='report_id.state', readonly=True
    )

class PdvReportPdv(models.Model):
    _name = 'l10n.hr.pdv.report.pdv'
    _inherit = 'l10n.hr.pdv.obrazac.line'

    state = fields.Selection(
        related='report_id.state', readonly=True
    )
    stavka_id = fields.Many2one(
        comodel_name='l10n.hr.config.report.pdv.line',
        string='Definicija stavke',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    sequence=fields.Integer(
        related='stavka_id.sequence',
    )
    code = fields.Char(
        string="Code", related='stavka_id.code',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    name = fields.Char(
        string="Name", related='stavka_id.name',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    amount_base = fields.Float(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    amount_tax = fields.Float(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='l10n_hr_report_pdv_move_line_rel',
        column1='pdv_line_id', column2='move_line_id',
        string='Stavke temeljnica',
        help="Stavke temeljnice zbrojene u ovu stavku",
        readonly=True, states={'draft': [('readonly', False)]},
    )

class PdvReportPDVS(models.Model):
    _name = 'l10n.hr.pdv.report.pdvs'
    _inherit = 'l10n.hr.pdv.obrazac.line'
    _description = 'Stavke PDV-S izvjestaja'

    state = fields.Selection(
        related='report_id.state', readonly=True
    )
    partner_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]},
        required=1)
    partner_vat = fields.Char(
        related='partner_id.vat'
    )
    dobra = fields.Float(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    usluge = fields.Float(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='l10n_hr_report_pdvs_move_line_rel',
        column1='pdvs_line_id', column2='move_line_id',
        string='Stavke temeljnica',
        help="Stavke temeljnice zbrojene u ovu stavku",
        readonly=True, states={'draft': [('readonly', False)]},
    )

class PdvReportZP(models.Model):
    _name = 'l10n.hr.pdv.report.zp'
    _inherit = 'l10n.hr.pdv.obrazac.line'
    _description = 'Stavke PDV - ZP izvjestaja'

    state = fields.Selection(
        related='report_id.state', readonly=True
    )
    partner_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]},
        required=1)
    partner_vat = fields.Char(
        related='partner_id.vat'
    )
    dobra = fields.Float(
        string="Dobra",
        help="Vrijednost isporuke dobara u HRK",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    dobra_4263 = fields.Float(
        string="Dobra 42, 63",
        readonly=True, states={'draft': [('readonly', False)]},
        help="Vrijednost isporuke dobara u postupcima 42 i 63 u HRK")
    dobra_tro = fields.Float(
        string="Dobra - Trostrano",
        readonly=True, states={'draft': [('readonly', False)]},
        help="Vrijednost isporuke dobara u okviru trostranog posla u HRK")
    usluge = fields.Float(
        string="Usluge",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='l10n_hr_report_pdvzp_move_line_rel',
        column1='zp_line_id', column2='move_line_id',
        string='Stavke temeljnica',
        help="Stavke temeljnice zbrojene u ovu stavku",
        readonly=True, states={'draft': [('readonly', False)]},
    )

class PdvReportPPO(models.Model):
    _name = 'l10n.hr.pdv.report.ppo'
    _inherit = 'l10n.hr.pdv.obrazac.line'
    _description = 'Stavke PDV - PPO izvjestaja'

    # TODO: posebni model, predaje se isključivo tromjesečno!
    # https://www.rrif.hr/Uputa_o_postupanju_Obrazac_PPO-3063-misljenje.html
    state = fields.Selection(
        related='report_id.state', readonly=True
    )
    partner_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]},
        required=1)
    partner_vat = fields.Char(
        related='partner_id.vat'
    )
    amount = fields.Float(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    mjesec_tro = fields.Selection(
        selection=[
            (1, 'Prvi mjesec tromjesečja'),
            (2, 'Drugi mjesec tromjesečja'),
            (3, 'Treći mjesec tromjesečja')
        ], string='Mjesec u kojem je obavljena isporuka',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='l10n_hr_report_ppo_move_line_rel',
        column1='ppo_line_id', column2='move_line_id',
        string='Stavke temeljnica',
        help="Stavke temeljnice zbrojene u ovu stavku",
        readonly=True, states={'draft': [('readonly', False)]},
    )




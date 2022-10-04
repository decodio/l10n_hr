from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from io import BytesIO
import openpyxl
from openpyxl.cell.cell import Cell
import base64
REPORT_POSITION_CELL = 'G'
PREVIOUS_YEAR_CELL = 'I'
CURRENT_YEAR_CELL = 'J'
PROFIT_LOSS_SHEET_NAME = 'RDG'
BALANCE_SHEET_NAME = 'Bilanca'
SHEET_ROW_START = 8


class MisReportGFIPODWizard(models.TransientModel):
    _name = 'mis.report.gfi.pod.wizard'
    _description = 'GFI-POD Report Wizard'

    profit_loss_mis_report_id = fields.Many2one('mis.report.instance', string='Profit/Loss Report', required=1)
    balance_sheet_mis_report_id = fields.Many2one('mis.report.instance', string='Balance Sheet Report', required=1)
    out_xls = fields.Binary('Excel file', readonly=True)
    name = fields.Char(string='File name', readonly=True)

    @api.multi
    def _inject_mis_report_data(self, mis_report, xlsx_template_sheet):
        kpi_report_position_data = dict(
            mis_report.report_id.kpi_ids.filtered('report_position').mapped(lambda l: (l.name, l.report_position)))
        kpi_data = mis_report.compute()
        data = dict()
        for line in kpi_data.get('body'):
            if kpi_report_position_data.get(line['row_id']):
                previous_year, current_year = line.get('cells', ({}, {}))
                data[kpi_report_position_data[line['row_id']]] = {
                    'previous': previous_year.get('val', 0.0) or 0.0,
                    'current': current_year.get('val', 0.0) or 0.0}
        for line in xlsx_template_sheet.iter_rows(min_row=SHEET_ROW_START):
            aop_position_cell = list(
                filter(lambda c: isinstance(c, Cell) and c.column_letter == REPORT_POSITION_CELL, line))
            previous_year_cell = list(
                filter(lambda c: isinstance(c, Cell) and c.column_letter == PREVIOUS_YEAR_CELL, line))
            current_year_cell = list(
                filter(lambda c: isinstance(c, Cell) and c.column_letter == CURRENT_YEAR_CELL, line))
            aop_position_cell = aop_position_cell and aop_position_cell[0] or None
            previous_year_cell = previous_year_cell and previous_year_cell[0] or None
            current_year_cell = current_year_cell and current_year_cell[0] or None
            if aop_position_cell:
                report_position_data = data.get(aop_position_cell.value)
                if report_position_data:
                    previous_year_cell.value = int(float_round(report_position_data.get('previous'), precision_digits=0))
                    current_year_cell.value = int(float_round(report_position_data.get('current'), precision_digits=0))

    @api.multi
    def _create_xls_report(self, company):
        infile = BytesIO()
        infile.write(base64.decodebytes(company.gfi_pod_xlsx_template_file))
        infile.seek(0)
        xlsx_template = openpyxl.load_workbook(infile)
        balance_sheet = xlsx_template[BALANCE_SHEET_NAME]
        profit_loss_sheet = xlsx_template[PROFIT_LOSS_SHEET_NAME]
        # RDG
        self._inject_mis_report_data(self.profit_loss_mis_report_id, profit_loss_sheet)
        # Bilanca
        self._inject_mis_report_data(self.balance_sheet_mis_report_id, balance_sheet)
        buffer = BytesIO()
        xlsx_template.save(buffer)
        buffer.seek(0)
        out = base64.encodebytes(buffer.read())
        buffer.close()
        return out

    @api.multi
    def create_xls_report(self):
        company = self.profit_loss_mis_report_id.company_id
        if not company.gfi_pod_xlsx_template_file:
            raise ValidationError(_('Company GFI-POD XLSX template is missing!'))
        out = self._create_xls_report(company)
        current_time_string = fields.Datetime.to_string(fields.Datetime.context_timestamp(self,fields.Datetime.now()))
        self.write({
            'out_xls': out,
            'name': 'GFI-POD(%s).xlsx' % current_time_string,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('l10n_hr_mis_reports',
                                                              'mis_report_gfi_pod_wizard_view_action')
        action['res_id'] = self.id
        return action

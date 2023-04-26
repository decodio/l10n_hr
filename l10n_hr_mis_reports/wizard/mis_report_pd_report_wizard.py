from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from io import BytesIO
import openpyxl
import base64
FIRST_SHEET_PERIOD_FROM_CELL = 'E11'
FIRST_SHEET_PERIOD_TO_CELL = 'G11'
SHEET_AMOUNT_CELL = 'G'


class MisReportPDReportWizard(models.TransientModel):
    _name = 'mis.report.pd.report.wizard'
    _description = 'PD Report Wizard'

    mis_report_id = fields.Many2one('mis.report.instance', string='PD Report', required=1,
                                    default=lambda self: self._get_default_mis_report_id())
    out_xlsx = fields.Binary('Excel file', readonly=True)
    name = fields.Char(string='File name', readonly=True)

    def _get_default_mis_report_id(self):
        return self.env['mis.report.instance'].search([('l10n_hr_report_type', '=', 'pd')])

    @api.multi
    def _update_first_sheet_company_data(self, mis_report, sheet):
        sheet[FIRST_SHEET_PERIOD_FROM_CELL] = mis_report.period_ids[0].manual_date_from
        sheet[FIRST_SHEET_PERIOD_TO_CELL] = mis_report.period_ids[0].manual_date_to

    @api.multi
    def _inject_mis_report_data(self, mis_report, sheet_no, sheet):
        kpi_report_position_data = dict(
            mis_report.report_id.kpi_ids.
            filtered(lambda x: x.report_sheet == sheet_no and x.report_position).
            mapped(lambda l: (l.name, l.report_position)))
        kpi_data = mis_report.compute()
        data = dict()
        for line in kpi_data.get('body'):
            if kpi_report_position_data.get(line['row_id']):
                data[kpi_report_position_data[line['row_id']]] = line['cells'] and line['cells'][0]['val'] or 0.0
        # write MIS generated data in Sheet
        for index, value in data.items():
            cell_index = '%s%s' % (SHEET_AMOUNT_CELL, index)
            sheet[cell_index] = float_round(value, precision_digits=2)

    @api.multi
    def _create_xlsx_report(self, company):
        infile = BytesIO()
        infile.write(base64.decodebytes(company.pd_report_xlsx_template_file))
        infile.seek(0)
        xlsx_template = openpyxl.load_workbook(infile)
        # Company Data, first sheet
        self._update_first_sheet_company_data(self.mis_report_id, xlsx_template.worksheets[0])
        # MIS Report Mapping
        # Sheet 2
        self._inject_mis_report_data(self.mis_report_id, 2, xlsx_template.worksheets[1])
        # Sheet 3
        self._inject_mis_report_data(self.mis_report_id, 3, xlsx_template.worksheets[2])
        # Sheet 4
        self._inject_mis_report_data(self.mis_report_id, 4, xlsx_template.worksheets[3])
        buffer = BytesIO()
        xlsx_template.save(buffer)
        buffer.seek(0)
        out = base64.encodebytes(buffer.read())
        buffer.close()
        return out

    @api.multi
    def create_report(self):
        company = self.mis_report_id.company_id
        if not company.pd_report_xlsx_template_file:
            raise ValidationError(_('Company PD Report XLSX template is missing!'))
        out = self._create_xlsx_report(company)
        current_time_string = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.now()))
        self.write({
            'out_xlsx': out,
            'name': _('PD_Report(%s).xlsx') % current_time_string,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('l10n_hr_mis_reports',
                                                              'mis_report_pd_report_wizard_view_action')
        action['res_id'] = self.id
        return action

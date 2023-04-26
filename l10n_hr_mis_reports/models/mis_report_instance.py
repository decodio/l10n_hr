from odoo import fields, models, api, tools
L10N_HR_REPORT_TYPES = [('gfi_pod', 'GFI-POD'),
                        ('pd', 'PD'),
                        ]


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'

    l10n_hr_report_type = fields.Selection(L10N_HR_REPORT_TYPES, string='Report Type')

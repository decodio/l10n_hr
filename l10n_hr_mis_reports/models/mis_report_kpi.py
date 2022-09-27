from odoo import fields, models, api, tools


class MisReportKPI(models.Model):
    _inherit = 'mis.report.kpi'

    report_position = fields.Integer('Report Position', index=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        if not tools.index_exists(self._cr, 'mis_report_kpi_report_position_unique'):
            self._cr.execute(
                """CREATE UNIQUE INDEX mis_report_kpi_report_position_unique 
                    ON mis_report_kpi (report_id, report_position) WHERE report_position != 0""")
        return res

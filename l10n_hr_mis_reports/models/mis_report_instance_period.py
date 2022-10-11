from odoo import fields, models, api, tools


class MisReportInstancePeriod(models.Model):
    _inherit = 'mis.report.instance.period'

    @api.model
    def _get_filter_domain_from_context(self):
        res = super()._get_filter_domain_from_context()
        analytic_tag_filters = list(filter(lambda a: a[0] == 'analytic_tag_ids', res))
        analytic_account_filter = list(filter(lambda a: a[0] == 'analytic_account_id', res))
        if analytic_tag_filters:
            or_operator_counter = len(analytic_tag_filters)
            if not analytic_account_filter:
                or_operator_counter -= 1
            analytic_tags_start_index = res.index(analytic_tag_filters[0])
            res[analytic_tags_start_index:analytic_tags_start_index] = ['|'] * or_operator_counter
        if analytic_account_filter:
            analytic_account_id = analytic_account_filter[0][2]
            analytic_tags = self.env['account.analytic.tag'].search(
                [('analytic_distribution_ids.account_id', '=', analytic_account_id)])
            if analytic_tags:
                analytic_account_start_index = res.index(analytic_account_filter[0])
                res[analytic_account_start_index:analytic_account_start_index] = ['|', (
                    'analytic_tag_ids', 'in', analytic_tags.ids)]
        return res

from odoo import fields, models, api, tools


class ResCompany(models.Model):
    _inherit = 'res.company'

    gfi_pod_xlsx_template_file = fields.Binary('GFI-POD XLSX template file')
    gfi_pod_xlsx_template_file_name = fields.Char('GFI-POD XLSX template filename')


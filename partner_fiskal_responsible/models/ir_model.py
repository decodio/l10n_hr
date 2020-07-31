
from odoo import api, fields, models, _


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    fiskal_tag_ids = fields.Many2many(
        comodel_name='res.partner.fiskal.tag',
        relation="res_partner_fiskal_tag_model_field_rel",
        column1="field_id", column2="tag_id",
        string="Required for fiskal tags",
    )

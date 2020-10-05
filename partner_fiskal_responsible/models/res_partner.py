# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PartnerFiskalTag(models.Model):
    _name = 'res.partner.fiskal.tag'
    _description = "Partner fiscal tags"

    """
    To be used for domain to select on documents, (INVOICE, PDV, JOPPD...)
    """

    name = fields.Char(string='Name')
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='res_partner_fiskal_tag_rel',
        column1='tag_id', column2='partner_id',
        string='Persons'
    )
    required_field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        relation="res_partner_fiskal_tag_model_field_rel",
        column1="tag_id", column2="field_id",
        string="Required fields",
        domain=[('model', '=', 'res.partner')]
    )


class Partner(models.Model):
    _inherit = 'res.partner'

    fiskal_responsible = fields.Boolean(
        string='Fiscal responsible', default=False,
        help="Check if person is fiscal responsible, "
             "and can be used as such on documents"
    )
    tag_ids = fields.Many2many(
        comodel_name='res.partner.fiskal.tag',
        relation='res_partner_fiskal_tag_rel',
        column1='partner_id', column2='tag_id',
        string='Responsible for reports',
        help="Responsibility for selected reports"
    )

    @api.onchange('company_type')
    def onchange_company_type(self):
        super(Partner, self).onchange_company_type()
        if self.is_company:
            self.fiskal_responsible = False

    def _get_fiskal_important_fields(self):
        """
        list of important fields, to check for changes,
        inherit in other modules with proper super calls,
        and fields if needed (phone, e-mail, ...)
        :return:
        """
        self.ensure_one()
        fields = []
        for tag in self.tag_ids:
            for fri in tag.required_field_ids:
                if fri.name not in fields:
                    fields.append(fri.name)
        return fields

    @api.multi
    def write(self, vals):
        f_manager = self.user_has_groups(
            'partner_fiskal_responsible.group_fiskal_responsible_manager')
        for partner in self:
            check = partner.fiskal_responsible and \
                    'fiskal_responsible' not in vals.keys() or \
                    not partner.fiskal_responsible and \
                    vals.get('fiskal_responsible', False)

            if check:

                fiskal_important_fields = partner._get_fiskal_important_fields()
                protect, missing = [], []
                for field in fiskal_important_fields:
                    if field in vals.keys() and not f_manager:
                        protect.append(field)
                    fc = eval('partner.'+field)
                    if field not in vals.keys() and not fc:
                        #TODO: provjeri dali vrijednost već postoji pa ju ne upisuje!
                        missing.append(field)
                error = False
                if protect:
                    error = "Protected fields for fiskal responsible person: "
                    error += str(fiskal_important_fields)
                if missing:
                    error = "Missing required fields for fiskal responsible: "
                    error += str(missing)
                if error:
                    raise UserError(error)
        return super(Partner, self).write(vals)




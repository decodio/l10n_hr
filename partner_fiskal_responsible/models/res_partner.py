# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FiskalResponsibleMixIn(models.AbstractModel):
    """
    Abstract class holding data fields for responsible person,
    Inherit in any report that need XML creation, and responsible person usage
    """
    _name = 'fiskal.responsible.mixin'
    #_table = False

    partner_id = fields.Many2one(comodel_name='res.partner')
    first_name = fields.Char('First name')
    last_name = fields.Char('Last name')
    email = fields.Char('Email')
    phone = fields.Char('Phone')

class PartnerFiskalTag(models.Model):
    _name = 'res.partner.fiskal.tag'

    """
    To be used for domain to select on documents, (INVOICE, PDV, JOPPD...)
    """

    name = fields.Char(string='Name')
    partner_ids = fields.Many2many(
        comodel_name='res.partner.fiskal.tag',
        relation='res_partner_fiskal_tag_rel',
        column1='tag_id', column2='partner_id',
        string='Persons'
    )
    required_field_ids = fields.One2many(
        comodel_name='ir.model_fields'
    )


class Partner(models.Model):
    _inherit = 'res.partner'

    # OCA/partner_firstname_ uses same fieldsnames- excluded in manifest
    firstname = fields.Char('First name')
    lastname = fields.Char('Last name')
    fiskal_responsible_user_id = fields.Boolean(
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

    @api.onchange('firstname', 'lastname')
    def _onchange_names(self):
        ime = self.firstname or ''
        prezime = self.lastname or ''
        name = ' '.join((ime, prezime))
        if self.name != name and self.fiskal_responsible:
            self.name = name

    @api.onchange('fiskal_responsible')
    def _onchange_fiskal_responsible(self):
        if self.fiskal_responsible:
            if self.name and not self.firstname:
                name = self.name.split(' ')
                if len(name) == 2:
                    # lako ako je ovo
                    self.firstname = name[0]
                    self.lastname = name[1]
                else:
                    #ako nije.. nek popravi tko unosi...
                    self.firstname = name[0]
                    self.lastname = ' '.join(name[1:])

    def fiskal_important_fields(self):
        """
        list of important fields, to check for changes,
        inherit in other modules with proper super calls,
        and fields if needed (phone, e-mail, ...)
        :return:
        """
        fields = ['tag_ids']  #  'firstname', 'lastname',
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

                fiskal_important_fields = partner.fiskal_important_fields()
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




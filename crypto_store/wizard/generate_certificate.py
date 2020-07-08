# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


# from M2Crypto import X509
from datetime import datetime, timedelta
from odoo import api, fields, models, _


class CryptoGenerateCertificate(models.TransientModel):
    _name = 'crypto.generate.certificate'
    _description = 'Certificate generator'

    def _get_date(self, offset=0):
        return (datetime.today() + timedelta(days=(offset))).strftime('%Y-%m-%d')

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('crypto.generate.certificate'))
    serial_number = fields.Integer('Serial number', default=1)
    version = fields.Integer('Version', default=2)
    #TODO: valid days ? and calc date expire...
    date_begin = fields.Date('Begin date', default=lambda self: self._get_date())
    date_end = fields.Date('Expiration date', default=lambda self: self._get_date(offset=365))
    name_c = fields.Char('Country (C)', size=2)
    name_sp = fields.Char('State or Province Name (ST/SP)', size=64)
    name_l = fields.Char('Locality Name (L)', size=64)
    name_o = fields.Char('Organization Name (O)', size=64)
    name_ou = fields.Char('Organization Unit Name (OU)', size=64)
    name_cn = fields.Char('Common name (CN)', size=64)
    name_gn = fields.Char('Given Name (GN)', size=64)
    name_sn = fields.Char('Surname (SN)', size=64)
    name_email = fields.Char('E-mail Addres (EMail)', size=64)
    name_serialnumber = fields.Char('Serial Number (serialNumber)', size=64)

    @api.onchange('company_id')
    def onchange_company_id(self):
        company_addr = self.company_id.partner_id
        try:
            self.name_c = company_addr.country_id.code
            self.name_sp = company_addr.state_id.name
            self.name_l = company_addr.city
            self.name_o = company_addr.name
            self.name_cn = company_addr.name
            self.name_email = company_addr.email
        except:
            pass


    def button_generate(self):
        return True
    #     assert len(self._context['active_ids']) == 1, 'Only one certificate can be generated!'
    #     certificate_obj = self.env[self._context['active_model']].browse(self._context['active_id'])
    #
    #     name = X509.X509_Name()
    #
    #     if self.name_c:      name.C = self.name_c
    #     if self.name_sp:     name.SP = self.name_sp
    #     if self.name_l:      name.L = self.name_l
    #     if self.name_o:      name.O = self.name_o
    #     if self.name_ou:     name.OU = self.name_ou
    #     if self.name_cn:     name.CN = self.name_cn
    #     if self.name_gn:     name.GN = self.name_gn
    #     if self.name_sn:     name.SN = self.name_sn
    #     if self.name_email:  name.Email = self.name_email
    #     if self.name_serialnumber: name.serialNumber = self.name_serialnumber
    #
    #     certificate_obj.generate_certificate(name, ext=None,
    #                 serial_number=self.serial_number, version=self.version,
    #                 date_begin=self.date_begin, date_end=self.date_end)
    #     #certificate_obj.action_validate()
    #     return {'type': 'ir.actions.act_window_close'}

    # def on_cancel(self, cr, uid, ids, context):
    #     return {}


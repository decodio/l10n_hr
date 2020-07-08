# -*- encoding: utf-8 -*-
# © 2019 Decodio Applications d.o.o. (davor.bojkic@decod.io)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html).


from odoo import models, fields, api, _
# from odoo.exceptions import Warning


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # TODO: posebni search view prilagoditi za traženje dokumenata!
    ubl_invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='invoice_ubl_attachment_rel',
        column1='att_id', column2='invoice_id',
        string="Attached to invoices",
    )


    # @api.model
    # def default_get(self, fields_list):
    #     res = super(IrAttachment, self).default_get(fields_list=fields_list)
    #     model_ref = self._context.get('model')
    #     if model_ref:
    #         model = self.env.ref(model_ref)
    #         res['res_model'] = 'account.invoice'
    #     return res

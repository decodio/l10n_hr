# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    state = fields.Selection(default='structured')

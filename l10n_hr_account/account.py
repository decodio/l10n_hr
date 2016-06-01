# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr....
#    Author: Goran Kliska
#    mail:   gkliskaATgmail.com
#    Copyright (C) 2011- Slobodni programi d.o.o., Zagreb
#    Contributions: 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, ValidationError, Warning, RedirectWarning

#from openerp.osv import fields, osv


class account_journal(models.Model):
    _inherit = "account.journal"

    def _P1_P4_selection():
        return ([('', 'Nothing'),
                 ('partner_code', 'Partner code'),
                 ('partner_id',   'Partner ID'),
                 ('invoice_no',   'Invoice Number'),
                 ('delivery_ym',  'Delivery year and month'),
                 ('invoice_ym',   'Invoice year and month'),
                ])

    model_pnbr = fields.Selection([('', 'Bez modela'),
                                 ('HR00', 'HR00 Bez kontrole'),
                                ('HR01', 'HR01 P1-P2-P3[k(P1,P2,P3)]'),
                                ('HR02', 'HR02 P1-P2[k(P2)]-P3[k(P3)]'),
                                ('HR03', 'HR03 P1[k(P1)]-P2[k(P2)]-P3[k(P3)]'),
                                ('HR06', 'HR06 P1-P2-P3[k(P2,P3)]'),
                                ('HR99', 'HR99 Bez kontrole'),
                                ],
                                'Model',
                                default='HR01',
                                help='Model poziva na broj')
    P1_pnbr = fields.Selection(_P1_P4_selection(), 'P1', default='partner_id', help='1. polje poziva na broj.')
    P2_pnbr = fields.Selection(_P1_P4_selection(), 'P2', default='invoice_no', help='2. polje poziva na broj.')
    P3_pnbr = fields.Selection(_P1_P4_selection(), 'P3', default='delivery_ym', help='3. polje poziva na broj.')
    P4_pnbr = fields.Selection(_P1_P4_selection(), 'P4', default=False, help='4. polje poziva na broj.')

    def create_sequence(self, cr, uid, vals, context=None):
        """
        Create new entry sequence for every new Joural
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be process
        @param context: context arguments, like lang, time zone
        @return: return a result
        """
        seq_pool = self.pool.get('ir.sequence')
        seq_typ_pool = self.pool.get('ir.sequence.type')

        name = vals['name']
        code = vals['code'].lower()

        types = {
            'name': name,
            'code': code
        }
        seq_typ_pool.create(cr, uid, types)

        seq = {
            'name': name,
            'code': code,
            'active': True,
            'prefix': "%(y)s-",
            'padding': 4,
            'number_increment': 1
        }
        return seq_pool.create(cr, uid, seq)

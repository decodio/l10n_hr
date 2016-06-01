# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Slobodni programi d.o.o.
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

from openerp.osv import fields, orm


class res_company(orm.Model):
    _inherit = "res.company"

    _columns = {
        'receivable_account_id': fields.many2one('account.account', 'Default Receivable Account', domain=[('type', '=', 'receivable')], help= 'Set here the receivable account that will be used, by default, if the partner is not found',),
        'payable_account_id': fields.many2one('account.account', 'Default Payable Account', domain=[('type', '=', 'payable')], help= 'Set here the payable account that will be used, by default, if the partner is not found'),
        'use_journal_seq': fields.boolean('Use Journal Sequence', help='Use Sequence from Bank Journal when importing bank statmens from files, insted of file sequence')
    }



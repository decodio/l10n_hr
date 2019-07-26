# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Authors:  Goran Kliska @ Slobodni-programi.hr Milan Tribuson @Infokom.hr
#    mail:   
#    Copyright: 
#    Contributions: Marko Carević @Infokom.hr
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
from openerp.tools.translate import _


class l10n_hr_obrazac_eu_obrazac(models.Model):
    _name = 'l10n_hr_pdv.eu.obrazac'
    _description = 'Vrsta Obrasca EU'
    _order = "sequence"

    def _default_company(self):
        user = self.env['res.users'].browse(self._uid)
        if user.company_id:
            return user.company_id.id
        return self.env['res.company'].search([('parent_id', '=', False)])[0]

    code =fields.Char('Code')
    name = fields.Char('Description',)
    type =fields.Selection([('pdv_s', 'Obrazac PDV-S')
                            ,('pdv_zp', 'Obrazac PDV-ZP')
                            ,('ppo', 'Obrazac PPO')
                            ],'Type', required=True )
    company_id = fields.Many2one('res.company', 'Company', required=True, default=_default_company)
    sequence = fields.Integer('Sequence', required=True, help="Poredak obrasca EU u prikazu", default=10)
    journal_ids = fields.Many2many('account.journal', 'l10n_hr_pdv_eu_obrazac_journal_rel',
                'obrazac_id', 'journal_id', 'Journals', required=True,
                domain=[('type', 'in', ('sale','sale_refund','purchase','purchase_refund'))],)

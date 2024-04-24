# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2023- Ecodica d.o.o., Zagreb
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

from odoo import models, fields, api, _

OPZ_STAT_VAT_IDS = [
    ("vat", "1"),
    ("vat_id", "2"),
    ("other", "3"),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    opz_stat_vat_id = fields.Selection(OPZ_STAT_VAT_IDS, compute='_compute_opz_stat_id', string="OPZ-STAT ID",
                                       required=True, prefetch=False, index=True, readonly=False, store=True,
                                       default=OPZ_STAT_VAT_IDS[0][0])

    @api.depends('vat', 'country_id')
    def _compute_opz_stat_id(self):
        for partner in self:
            if partner.vat:
                if partner.vat.startswith('HR') or (partner.country_id and partner.country_id.code == 'HR'):
                    partner.opz_stat_vat_id = 'vat'
                elif partner.country_id:
                    partner.opz_stat_vat_id = 'vat_id'
                else:
                    partner.opz_stat_vat_id = 'other'
            else:
                partner.opz_stat_vat_id = 'other'

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_opz_stat
#    Author: Tomislav Bosnjakovic
#    mail:   tomislav.bosnjakovic(AT)slobodni-programi.hr
#    Copyright: Slobodni programi d.o.o., Zagreb
#    Contributions:
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

{
    "name": "Croatia Print Payment Slip",
    "description": """
Croatian localisation.
======================
Prints payment Slip (HUb obrazac, Virman) from Sales Order
""",
    "version": "1.0",
    "author": "Slobodni programi",
    "category": 'Localization',
    "website": "",

    'depends': [
                'sale',
                ],
    'data': [
                'report/report_data.xml',
                #'security/ir.model.access.csv',
            ],
    "demo": [],
    'test': [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Author:
#    mail:
#    Copyright:
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

{
    'name' : 'Fiskal Sale Account',
    'description' : """
Croatian localisation.
======================

Description:
-------------
    * Popunjava Nacin Placanja i Prostor kod izrade racuna iz sale ordera


""",
    'version': '8.0.0.0',
    'author' : 'Croatian community',
    'category' : 'Localisation/Croatia',
    'website': 'https://launchpad.net/openobject-croatia',

    'depends': [
                'sale_base',
                'l10n_hr_fiskal',
                ],

    'data': [
    ],
    'installable': True,
    'auto_install': True,
}
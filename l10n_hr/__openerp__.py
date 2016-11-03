# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr
#    Author: Goran Kliska
#    mail:   goran.kliska(AT)slobodni-programi.hr
#    Copyright: Slobodni programi d.o.o., Zagreb
#    Contributions:
#              Tomislav Bošnjaković, Storm Computers d.o.o. :
#                 - account types
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
    "name": "Croatia - RRIF's 2014 chat of accounts",
    "description": """
Croatian localisation.
======================

Author: Slobodni programi d.o.o., Zagreb
        http://www.slobodni-programi.hr

Contributions:

Description:

Croatian Chart of Accounts (RRIF ver.2014)

RRIF-ov računski plan za poduzetnike za 2014.
Vrste konta
Kontni plan prema RRIF-u, dorađen u smislu kraćenja naziva i dodavanja analitika
Porezne grupe prema poreznoj prijavi
Porezi PDV-a
Ostali porezi (samo češće korišteni) povezani s kontima kontnog plana

Izvori podataka:
 http://www.rrif.hr
""",
    "version": "2014.1",
    "author": "OpenERP Croatian Community",
    "category": 'Localization/Account Charts',
    "website": "https://code.launchpad.net/openobject-croatia",

    'depends': [
                'account',
                'base_vat',
                'base_iban',
                'account_chart',
                ],
    'data': [
                'data/account.account.type.csv',
                'data/account.tax.code.template.csv',
                'data/account.account.template.csv',
                #'data/account.fiscal.position.template.csv',
                #'data/account_account_type_data.xml',
                #'data/account_account_template_data.xml',
                #'data/account_tax_code_template_data.xml',
                #'data/account_tax_code_data.xml',
                'data/account_fiscal_position_template_data.xml',
                'l10n_hr_wizard.xml',
                'data/account.tax.template.csv',
                #'data/fiscal_position.xml',
            ],
    "demo": [],
    'test': [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

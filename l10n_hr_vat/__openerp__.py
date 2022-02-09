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
    "name" : "Croatia - VAT reporting",
    "description" : """
Croatian localisation.
======================

Description:
-------------
    * Knjiga URA/IRA
    * PDV obrazac

Authors:
--------
    * Goran Kliska @ Slobodni programi d.o.o.
    * Tomislav Bošnjakovič @ Slobodni programi d.o.o.

""",
    "version": "8.0.2.0.0",
    "author" : "Croatian community",
    "category" : "Localisation/Croatia",
    "website": "https://launchpad.net/openobject-croatia",

    'depends': [
                'account',
                #'account_tax_payment',
                'base_vat',
                'base_iban',
                #'account_chart',
                'l10n_hr_data',
                #'oca_base',
                #'account_report_alt',
                ],
    'data': [
                'security/ir.model.access.csv',
                'account_view.xml',
                'pdv_knjiga_view.xml',
                'pdv_obrazac_eu_view.xml',
                'pdv_config_view.xml',
                'wizard/wizard_pdv_obrazac_view.xml',
                'wizard/wizard_pdv_knjiga_view.xml',
                'wizard/account_vat_settlement_view.xml',
                'wizard/wizard_obrazac_pdv_eu_view.xml',
                'report/report.xml',
                #'data/l10n_hr_pdv.knjiga.csv',  #import manualy or new module
                #'data/l10n_hr_pdv.report.obrazac.csv', #fails on mc now on Verso HR 
                #'data/l10n_hr_pdv.report.knjiga.csv', #import manualy or new module  
                   ],
    "demo_xml" : [],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

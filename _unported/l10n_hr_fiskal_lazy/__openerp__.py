# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_fiskal_lazy
#    Author: Davor Bojkić
#    mail:   bole@dajmi5.com
#    Copyright (C) 2012- Daj Mi 5, 
#                  http://www.dajmi5.com
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
    "name" : "Croatian localization - Fiscalization module addon",
    "description" : """
Fiskalizacija izdanih računa
============================

Author: Davor Bojkić - Bole @ DAJ MI 5     www.dajmi5.com

               

Description:
Dodaje default prostor, naplatni uređaj i dnevnik za usera.
na računu uzima zadane vrijednosti.

PAZI - fiskalizirani broj je podešen na 3 znamenke ( 13/ ) !!!
 
""",
    "version" : "1.07",
    "author" : "DAJ MI 5",
    "category" : "Localisation/Croatia",
    "website": "http://www.dajmi5.com",

    'depends': [
                'l10n_hr_fiskal',
                ],
    'update_xml': [
                   'res_users_view.xml',
                   'account_invoice_view.xml',
                   ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

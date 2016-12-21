# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_fiskal
#    Author: Davor Bojkić
#    mail:   bole@dajmi5.com
#    Copyright (C) 2012- Daj Mi 5, 
#                  http://www.dajmi5.com
#    Contributions: Hrvoje ThePython - Free Code!
#                   Goran Kliska (AT) Slobodni Programi
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
    "name" : "Croatian localization - Fiscalization module",
    "description" : """
Fiskalizacija izdanih računa
====================================

Author: Davor Bojkić - Bole @ DAJ MI 5
        www.dajmi5.com

Contributions: Hrvoje ThePython - Free Code!
               Goran Kliska @ Slobodni Programi
               Tomislav Bošnjaković @ Slobodni Programi


TODO/WIP: - new API,
 replace libs with
 https://github.com/kodmasin/fiskpy
 https://github.com/decodio/fiskpy


Preduvjeti: 
    na serveru instalirati:
        python-dev, python-ms2crypto, libxmlsec1-dev
        build/install pyxmlsec-0.3.2! 
""",
    "version" : "1.02",
    "author" : "DAJ MI 5",
    "category" : "Localisation/Croatia",
    "website": "http://www.dajmi5.com",

    'depends': [
                'base_vat',
                #'account_storno',
                'l10n_hr_account',
                'crypto',
                ],
    'external_dependencies':{'python':['M2Crypto'#,'PyXMLSec'
                                       ],
                             #'bin':'libxmlsec-dev'
                             },
    'data': [
                   'certificate_view.xml',
                   'fiskalizacija_view.xml',
                   'security/ir.model.access.csv',
                   'account_view.xml',
                   'account_invoice_view.xml',
                   'l10n_hr_fiskal_data.xml',
                   'company_view.xml',
                   ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

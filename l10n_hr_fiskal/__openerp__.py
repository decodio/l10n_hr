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

Potrebni otvoreni TCP portovi prema CIS sustavu: 8449

https://www.porezna-uprava.hr/HR_Fiskalizacija/Aktualnosti%20dokumenti/Fiskalizacija%20-%20Tehnicka%20specifikacija%20za%20korisnike_v1.1.pdf

TODO/WIP: - new API,
 replace libs with
 https://github.com/decodio/fiskpy


Preduvjeti: 
    na serveru instalirati:
        python-dev, python-ms2crypto, libxmlsec1-dev
        build/install pyxmlsec-0.3.2!

Preduvjeti fisk.py
    signxml - pip install signxml (version 2 supported from fiskpy v0.8.1)
    To install PyCrypto
    Pull form:
    https://github.com/decodio/pycrypto.git

    To install the package under the site-packages directory of
    your Python installation, run "python setup.py install".
""",
    "version" : "8.0.1.1.0",
    "author" : "DAJ MI 5",
    "category" : "Localisation/Croatia",
    "website": "http://www.dajmi5.com",

    'depends': [
                'base_vat',
                #'account_storno',
                'l10n_hr_account',
                'crypto',
                ],
    'external_dependencies': {'python':['fisk'],
                             },
    'data': [
         'views/certificate_view.xml',
         'views/fiskalizacija_view.xml',
         'views/account_view.xml',
         'views/account_invoice_view.xml',
         'views/company_view.xml',
         'security/ir.model.access.csv',
         'data/l10n_hr_fiskal_data.xml',
                   ],
    "active": False,
    "installable": True,
}

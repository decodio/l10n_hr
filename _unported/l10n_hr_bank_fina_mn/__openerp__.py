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

{
    "name": "Bank Statement - Import from file",
    "version": "1.0",
    "author": "Slobodni programi d.o.o.",
    "description": """
Croatian localisation
======================

Description:
-------------
    * Imports bank statements FINA format

Authors:
--------
    * Tomislav Bošnjakovič @ Slobodni programi d.o.o.
    * Goran Kliska @ Slobodni programi d.o.o.

    """,
    "website": "",
    "depends": [
                "account",
                #"account_extra",
    ],
    "category": "Accounting",
    "data": [
        #"security/import_bank_statement_security.xml", #TODO
        "security/ir.model.access.csv",
        "res_company_view.xml",
        "wizard/import_bank_statement_wiz_view.xml",
        "bank_statement_import_view.xml",
        "account_view.xml",
       
    ],
    "init_xml": [],
    "update_xml": [],
    "installable": True,
    "active": False,
}

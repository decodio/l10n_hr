# -*- coding: utf-8 -*-
# Odoo, Open Source Management Solution
# Copyright (C) 2019 Decodio
# License LGPL-3.0 (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Croatia E-Racun base',
    'version': '12.0.0.0.1',
    'author': 'Decodio Applications ltd',
    'summary': 'Croation localisation of account invoice ubl',
    'category': 'Accounting',
    'website': 'http://decod.io',
    'license': 'LGPL-3',
    'depends': [
        'base_unece',
        'account_payment_unece',
        'account_invoice_ubl',
        'l10n_hr_account_oca',
    ],
    'demo': [],
    'data': [
        'data/unece_document_type.xml',
        'data/partner_doctype.xml',
        'data/unece.xml',
        'views/company.xml',
        'views/account_invoice_view.xml',
        'views/partner_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
#     'description': """
#     E-račun postavke
#
# - Taxes: UNECE Tax Type, UNECE Tac Category
#
# - Partner - UBL Schema - select proper default schema for generating invoices
#
# - Company : Memorandum data - svi podaci iz zaglavlja/podnožja računa
#      - obavezni podaci : članovi uprave, Matični broj, osnivački kapital isl..
#        a koji se ne nalaze na drugim mjestima (OIB, VAT, bankovni računi itd)
# - naselje na poslovnom prostoru ( mjesto izdavanja računa)
#
#
# - testirati obje verzije.. prioritet je B2G
#        ISSUES
#
#     - pokriven je samo standardni PDV
#     - ne radi prijenos porezne obveze - razvoj ako i kad se pokaže potreba
#
#
#
#
#     """
}

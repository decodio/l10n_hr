# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Slobodni programi d.o.o.
#
##############################################################################

{
    "name": "Sepa",
    "version": "1.0",
    "author": "Slobodni programi d.o.o.",
    "description": """
Croatian localisation
======================

Description:
-------------
    * sepa

Authors:
--------
    * Goran Kliska @ Slobodni programi d.o.o.

    """,
    "website": "",
    "depends": [
        'account_bank_statement_import_camt',  # depends account_bank_statement_import
        'account_bank_statement_period_from_line_date',
        'account_bank_statement_import_save_file', #'summary': 'Keep imported bank statements as raw data','depends': [ 'account_bank_statement_import',],
        #"account_banking", depreciated!!
        'account_banking_sepa_credit_transfer', # depends account_banking_pain_base, depends account_banking_payment_export
        'account_banking_payment_transfer', # use interim account for payments
        'account_banking_sepa_direct_debit', #depends 'account_direct_debit','account_banking_mandate','account_banking_pain_base',
        'account_invoice_reference',  #
        'account_payment_return_import_sepa_pain',

        'base_transaction_id',
        'account_easy_reconcile',
        #not installable'account_statement_so_completion' #'depends': ['account_statement_base_completion', 'sale'],
    ],
    "category": "Accounting",
    "data": [
        #"security/import_bank_statement_security.xml", #TODO
        #"security/ir.model.access.csv",
        #"res_company_view.xml",
        #"wizard/import_bank_statement_wiz_view.xml",
        #bank_statement_import_view.xml",
        #"account_view.xml",
       
    ],
    "init_xml": [],
    "update_xml": [],
    "installable": True,
    "active": False,
}

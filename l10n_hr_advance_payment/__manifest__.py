# -*- coding: utf-8 -*-
# Copyright 2022 Ecodica
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "l10n_hr_advance_payment",

    'summary': """
        Advance Payment Invoices""",

    'description': """
        Advance Payment Invoices
    """,

    'author': 'Ecodica',
    'website': 'https://www.ecodica.eu',
    'license': 'LGPL-3',

    'category': 'Accounting & Finance',
    'version': '12.0.0.0.1',

    # TODO: refactor AccountInvoice.action_move_create method so that it calls super in account_base module, afterwards
    #  remove dependency link between these two modules
    'depends': ['sale', 'account', 'account_base', 'purchase_deposit'],

    # always loaded
    'data': [
        'views/account_journal_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
    ],
    # only if external dependency exists
    'external_dependencies': {
        "python": [],
        "bin": []
    },
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
    ],
    "auto_install": False,
    "installable": True,
}

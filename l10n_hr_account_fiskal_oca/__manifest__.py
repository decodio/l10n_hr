# Copyright 2021 Ecodica
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': "Croatia accounting - fiscalisation",

    'summary': """
        Fiscalization of issued invoices
        """,

    'description': """
       Law regulates the way of issueing all kind of customer invoices regarding 
        payment - all except bank transfer must be ficalized at time of confirming or
        if that is not possible within 48 hours of confirming.
        This module adds fiscalization functionality.
        
        pip install pycryptodome
        pip install backports.ssl_match_hostname
        pip install signxml
    """,

    'author': 'Ecodica',
    'website': 'https://www.ecodica.eu',
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoices & Payments',
    'version': '12.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_hr_account_oca',
        'crypto_store',
    ],

    # always loaded
    'data': [
        'wizard/zastitini_kod_view.xml',
        'views/res_users.xml',
        'views/res_company.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
        'security/ir.model.access.csv',


    ],
    # only if external dependency exists
    'external_dependencies': {
        "python": [],
        "bin": [],
        "pycryptodome": [],
        "backports.ssl_match_hostname": [],
        "signxml": []
    },
    'conflicts': ['l10n_hr_account'],  #by UVID, from odoo app store if ported to v12

    'demo': [],
    'qweb': [],
    "auto_install": False,
    "installable": True,
}

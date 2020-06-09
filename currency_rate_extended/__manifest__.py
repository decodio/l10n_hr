# -*- coding: utf-8 -*-
# Copyright 2019 Decodio Applications
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Currency rate Extensions",

    'summary': """
        On Currency rate provider, enables multiple rates (buy, mid, sell)
        Enables using per journal defined currency rate,
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': 'Decodio Apllications Ltd',
    'website': 'https://www.decod.io',
    'licence': 'AGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoices & Payments',
    'version': '12.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'currency_rate_update',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_currency_rate_views.xml',
        'views/account_journal_views.xml',
        'views/res_currency_rate_provider_views.xml',
    ],
    # only if external dependency exists
    'external_dependencies': {
        "python": [],
        "bin": []
    },
    'conflicts': ['currency_monthly_rate',
                  'currency_rate_inverted'],

    'demo': [],
    'qweb': [],
    "auto_install": False,
    "installable": True,
}

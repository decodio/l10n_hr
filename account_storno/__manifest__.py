# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Storno',
    'summary': 'Allows Storno accounting (negative accounting entries)',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'author': 'Slobodni programi d.o.o., '
              'Decodio Applications d.o.o.,'
              'Forest and Biomass Romania, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'LGPL-3',
    'installable': True,
    'depends': [
        'account'
    ],
    'data': [
        'views/account_view.xml',
        'views/account_invoice_view.xml'
    ]
}

# -*- coding: utf-8 -*-
# © 2016 Goran Kliska
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Croatian Municipalities',
    'summary': 'Support for CRO municipalities through Eurostat LAUs',
    'version': '8.0.1.0.0',
    'category': 'Localisation/Croatia',
    'website': 'https://odoo-community.org/',
    'author': 'Goran Kliska, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'base_location',  # from oca/partner-contact
        'base_location_lau',  # from oca/partner-contact
        'base_location_nuts',  # from oca/partner-contact
        ],
    'data': [
        'data/res.partner.lau.csv',
        ],
}

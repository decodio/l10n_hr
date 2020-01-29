# -*- coding: utf-8 -*-

{
    "name": """Partner fiscal responsible""",
    "summary": """Fiskal responsability enabled on persons""",
    "category": "Partner",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    'author': "Decodio Application ltd.",
    'website': "http://www.decod.io",
    "support": "support@decod.io",
    "licence": "LGPL-3",
    #"price" : 20.00,   #-> only if module if sold!
    #"currency": "EUR",

    "depends": [
        'base'
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        'security/fiscal_security.xml',
        'security/ir.model.access.csv',
        'views/partner_views.xml',

    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}

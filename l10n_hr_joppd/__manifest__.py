# -*- coding: utf-8 -*-

{
    "name": """JOPPD obrazac""",
    "summary": """joppd obrazac osnova""",
    "category": "Croatia",
    "images": [],
    "version": "1.1.0",
    "application": False,

    'author': "Decodio Application ltd.",
    'website': "http://www.decod.io",
    "support": "support@decod.io",
    "licence": "LGPL-3",
    #"price" : 20.00,   #-> only if module if sold!
    #"currency": "EUR",

    "depends": [
        "l10n_hr_base",
        "base_address_extended",  # Zbog adrese i kucnog broja!
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "security/joppd_security.xml",
        "security/ir.model.access.csv",
        "views/joppd_menuitems.xml",
        "views/joppd_views.xml",

    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}

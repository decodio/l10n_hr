# -*- coding: utf-8 -*-

{
    "name": """Croatia - base""",
    "summary": """Croatia base localization data""",
    "category": "Localisation / Croatia",
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

    ],
    "external_dependencies": {
        "python": [
            'tzlocal'
        ],
        "bin": []
    },
    "data": [
        #"data/res_bank_data.xml",
        "views/res_company_view.xml",

        # NKD
        #"views/l10n_hr_nkd_view.xml",
        #"data/localization_settings.xml",
        #"security/ir.model.access.csv",
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}


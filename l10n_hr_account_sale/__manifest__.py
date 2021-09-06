# Copyright 2021 Ecodica
{
    "name": "Croatia - Sales to Accounting",
    "summary": "Croatia Sales to accounting localisation",
    "category": "Croatia",
    "images": [],
    "version": "12.0.0.0.1",
    "application": False,

    'author': "Ecodica",
    'website': "https://www.ecodica.eu",
    "support": "support@decod.io",
    "license": "LGPL-3",
    "depends": [
        "l10n_hr_account_oca",
        "sale",
    ],
    "excludes": ["l10n_hr_account"],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "views/crm_team.xml",
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}

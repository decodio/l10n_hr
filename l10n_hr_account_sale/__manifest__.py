
{
    "name": "Croatia - Sales to Accounting",
    "summary": "Croatia Sales to accounting localisation",
    "category": "Croatia",
    "images": [],
    "version": "12.0.0.0.1",
    "application": False,

    'author': "Decodio Application ltd.",
    'website': "http://www.decod.io",
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

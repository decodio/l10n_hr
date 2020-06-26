
{
    "name": "Croatia - Accounting base",
    "summary": "Croatia accounting localisation",
    "category": "Croatia",
    "images": [],
    "version": "12.0.0.0.1",
    "application": False,

    'author': "Decodio Application ltd.",
    'website': "http://www.decod.io",
    "support": "support@decod.io",
    "license": "LGPL-3",
    "depends": [
        "account",
        # "account_storno",
        "base_vat",
        "base_iban",
        "l10n_hr_base",
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "security/ir.model.access.csv",
        #"views/res_config_view.xml",
        "views/res_company_view.xml",
        "views/res_users_view.xml",
        "views/account_invoice_view.xml",
        "views/account_journal_view.xml",
        "views/menuitems.xml",
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}

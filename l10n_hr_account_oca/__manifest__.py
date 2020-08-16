
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
        "account_storno",
        "base_vat",
        "base_iban",
        "l10n_hr_base",
        "account_invoice_tax_note",  # BOLE: testirati
        #"partner_firstname", # BOLE: odgovorna osoba
        "partner_fiskal_responsible",
    ],
    "excludes": [
        "l10n_hr_account"  # possible other localization module
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
        "data/partner_fiskal_tag.xml"
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}

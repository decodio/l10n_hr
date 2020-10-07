# -*- coding: utf-8 -*-
{
    "name": "Croatia COA - RRIF 2015",
    "summary": "Croatia COA template - RRIF2015",
    "category": "Localization",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    "author": "Decodio Applications d.o.o," 
              "DAJ MI 5," 
              "Odoo Hrvatska",
    "support": "support@odoo-hrvatska.org",
    "website": "http://odoo-hrvatska.org",
    "licence": "LGPL-3",
    "depends": [
        "account",
        "base_vat",
        "base_iban",
        # TESTNO
        "account_invoice_tax_note", # from OCA! - oslobodjenja!

    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "data/l10n_hr_account_chart_data.xml", # DB: template id = l10n_hr_coa_rrif_2015_template
        "data/res_county_group.xml",           # Dodoajem EU države bez HR
        "data/account.account.type.csv",       # Tipovi konta, reducirano za dodane u standardnom odoo
        "data/account.tax.group.csv",          # 9.11.2017 dodan na template field tax_group_id!
        "data/account.group.csv",              # 16.1.2020: koristim account grupe za sintetiku!
        "data/account.account.tag.csv",        # Tax tagovi prema pozicijam PDV obrasca, Account tagovi - klase, razredi, grupe, (sintetika 2)
        "data/account.account.template.csv",   # dodan group_id
        "data/company_croatia.xml",            # ponovo update template-a
        "data/account.tax.template.csv",       # porezi, TODO: dopuna za 50/50 : gorivo, repka isl...
        "data/account.fiscal.position.template.csv",
        "data/account.fiscal.position.tax.template.csv",
        "data/account.fiscal.position.account.template.csv",
        # "data/account_tax_group_data.xml",    -> vec ucitano kroz csv, eventualno ako koristim no_update
        #"data/account_chart_template_apply.yml",
        'data/account_chart_template_load.xml'
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
    #"post_init_hook": '_install_l10n_hr_modules',
}



# -*- coding: utf-8 -*-
{
    'name': "Croatia - VAT reports",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list

    "category": "Croatia",
    'version': '12.0.0.0.1',
    'summary': """
        Hrvatska . porezni izvještaji""",

    'description': """
        PDV 
        PDV-S
        ZP
        PPO
        
        TODO:
        URA
        IRA...
    """,

    'author': "Decodio Apllications Ltd",
    'website': "https://www.decod.io",
    "licence": "LGPL-3",

    'depends': [
        'l10n_hr_base',
        'l10n_hr_account_oca',
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/res_company_view.xml',
        'views/report_config_pdv_views.xml',
        'views/report_pdv_views.xml',
        # 'views/account_tax.xml',

        'data/l10n.hr.porezna.uprava.csv',
        'data/l10n.hr.config.report.pdv.csv',
        'data/l10n.hr.config.report.pdv.line.csv',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "auto_install": False,
    "installable": True,
}

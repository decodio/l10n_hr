# -*- coding: utf-8 -*-
# Copyright 2022 Ecodica
{
    "name": """Croatia MIS reports""",
    "summary": """MIS report templates for Croatia""",
    "category": "Croatia",
    "images": [],
    "version": "12.0.0.1",
    "application": False,

    'author': "Ecodica",
    'website': "https://www.ecodica.eu",
    "support": "odoo.support@ecodica.eu",
    "licence": "LGPL-3",

    "depends": [
        "mis_builder",
        "account",
        "l10n_hr_base",
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        # 'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/mis_report_kpi_view.xml',
        'views/mis_report_view.xml',
        'wizard/mis_report_gfi_pod_wizard_view.xml',
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}

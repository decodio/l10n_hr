# -*- coding: utf-8 -*-
# © 2018 DAJ MI 5 <https://www.dajmi5.hr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": """Alternative layout for qweb - Invoice Croatia""",
    "summary": """QWEB invoice loacalization - Croatia""",
    "category": "Hidden",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    "author": "DAJ MI 5!",
    "licence": "LGPL-3",
    "depends": [
        'report_qweb_al_invoice',
        'l10n_hr_account_oca'
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "views/report_invoice.xml",
    ],
    "qweb": [],
    "demo": [],

    "auto_install": True,
    "installable": True,
}


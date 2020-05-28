# -*- coding: utf-8 -*-
{
    "name": """Account reference: Poziv na broj""",
    "summary": """Add reference type: Poziv na broj""",
    "category": "Accounting",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    "author": "Decodio Applications ltd",
    "licence": "LGPL-3",

    "depends": [
        'account'
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "views/account_journal_view.xml",
        "views/account_invoice_view.xml",
        "views/report_invoice.xml"
    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}

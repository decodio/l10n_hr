# -*- coding: utf-8 -*-
# Copyright 2021 Ecodica
{
    "name": """Croatia MIS reports""",
    "summary": """MIS report templates for Croatia""",
    "category": "Croatia",
    "images": [],
    "version": "1.0.0",
    "application": False,

    'author': "Ecodica",
    'website': "https://www.ecodica.eu",
    "support": "support@decod.io",
    "licence": "LGPL-3",
    #"price" : 20.00,   #-> only if module if sold!
    #"currency": "EUR",

    "depends": [
        "mis_builder",
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "data/mis_report_style_data.xml",
        "data/mis_report_data.xml",
        # KOntni planovi
        "data/mis_kpi_COA_unstructured.xml",
        "data/mis_kpi_COA_structured.xml",
        #PDV
        "data/mis_kpi_pdv.xml",
    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}

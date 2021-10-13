# -*- coding: utf-8 -*-
# Copyright 2021 Ecodica
{
    "name": """Croatia - City data""",
    "summary": """Adds location data for Croatia - Cities, post offices etc.""",
    "category": "Croatia",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    'author': "Ecodica",
    'website': "https://www.ecodica.eu",
    "support": "support@decod.io",
    "licence": "LGPL-3",
    #"price" : 20.00,   #-> only if module if sold!
    #"currency": "EUR",

    "depends": [
        "base_address_city",
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "data/res_country_state_data.xml",
        "data/res.city.csv",
    ],
    "qweb": [],
    "demo": [],

    "auto_install": False,
    "installable": True,
}


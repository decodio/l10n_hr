# Copyright 2021 Ecodica
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": """Odoo Cryptography Manager""",
    "summary": """Management for all sort of keys, certificates, etc.""",
    "category": "Tools",
    "images": [],
    "version": "12.0.1.0.0",
    "application": False,

    "author": "Coop. Trab. Moldeo Interactive Ltda.,"
              "Ecodica",
    # "support": "support@odoo-hrvatska.orgr",
    "website": "https://decod.io",
    "license": "LGPL-3",
    "depends": [
        "base"
    ],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": [
        "views/crypto_menuitems.xml",
        "wizard/generate_pairkey.xml",
        "wizard/generate_certificate.xml",
        "wizard/generate_certificate_request.xml",
        "views/pairkey_view.xml",
        "views/certificate_view.xml",
        "security/crypto_security.xml",
        "security/ir.model.access.csv",
    ],
    "qweb": [],
    "demo": [],
    "test": [
        "test/test_pairkey.yml",
        "test/test_certificate.yml"
    ],

    "auto_install": False,
    "installable": True,
}

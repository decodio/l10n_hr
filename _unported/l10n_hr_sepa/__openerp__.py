# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Slobodni programi d.o.o.
#
##############################################################################

{
    "name": "Croatian Sepa",
    "version": "1.0",
    "author": "Decodio Application d.o.o.",
    "description": """
Croatian localisation
======================

Description:
-------------
    Sepa Credit Transfer Croatian Localization.
    So far only SEPA pain.001.001.03 is supported

Authors:
--------
    * Tomislav Bosnjakovic @ Decodio Application d.o.o.

    """,
    "website": "",
    "depends": [
        'account_payment',
        'account_banking_sepa_credit_transfer',
    ],
    "category": "Accounting",
    "data": [
    ],
    "init_xml": [],
    "update_xml": [],
    "installable": True,
    "active": False,
}

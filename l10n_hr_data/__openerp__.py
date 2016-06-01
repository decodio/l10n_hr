# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_base
#    Author: Goran Kliska
#    mail:   goran.kliska(AT)slobodni-programi.hr
#    Copyright: Slobodni programi d.o.o., Zagreb
#                  http://www.slobodni-programi.hr
#    Contributions:
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" :"Croatian localization - base module",
    "description": u"""
Croatian localisation.
======================

Description:

Podaci o organizaciji u raznim tijelima državne uprave:
--------------------------------------------------------
    * Porezna uprava
    * Porezna ispostava
    * Br. obveze mirovinsko
    * Br. obveze zdravstveno
    * Matični broj
    * Nacionalna klasifikacija djelatnosti
    * Županije RH
    * Gradovi RH

Banke:
-------
    * VBB - Vodeći broj banke
    * Popis banaka

Cjenik:
-------
    * Change currency on product price type to HRK

Authors:
--------
    * Goran Kliska @ Slobodni programi www.slobodni-programi.hr

""",
    "version": "14.8.1",
    "author": "Slobodni programi d.o.o.",
    "category": "Localisation/Croatia",
    "website": "http://www.slobodni-programi.hr",
    'depends': ['base_vat','base_base'],
    'data':[
            'security/ir.model.access.csv',
            'data/res.bank.csv',
            'data/l10n_hr_base.nkd.csv',
            'data/res.country.state.csv',
            #'data/res.city.csv',
            'l10n_hr_data_view.xml',
            'l10n_hr_price_type.xml',
            ],
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

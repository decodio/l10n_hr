# -*- coding: utf-8 -*-
# author: bole@dajmi5.com


# from odoo import api, SUPERUSER_ID
#
#
# def _install_l10n_hr_modules(env):
#     """
#     l10n_hr_account canot be dependant on single COA,
#       as COA moduels can be extended, or different COS odules
#     # install all localization needed modules from here
#     # so everything is set according to needs
#
#     :param env:
#     :return:
#     """
#
#     modules = env['ir.module.module']
#     to_install = [
#         'l10n_hr_account',
#         'l10n_hr_bank',
#         'l10n_hr_base_location',
#     ]
#     for module in to_install:
#         m = modules.search([('name', '=', module)], limit=1)
#         # TODO: provjera autora modula:
#         #  npr...nije kompatabilno sa modulima od Uvid d.o.o.
#         if m and m.state != 'installed':
#             m.button_immediate_install()
#
# def post_init(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     _install_l10n_hr_modules(env)

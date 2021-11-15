# -*- coding: utf-8 -*-

import logging

from openerp import SUPERUSER_ID
from openerp.api import Environment


logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, if a database has a few hundred thousand
    journal entries, which is not unlikely, the update will take
    at least a few hours.

    The pre init script only writes 0 in the field maturity_residual
    so that it is not computed by the install.

    The post init script sets the value of maturity_residual.
    """
    store_field_stored_invoice_id(cr)


def post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})


def store_field_stored_invoice_id(cr):
    cr.execute(
        """
        ALTER TABLE account_move_line ADD COLUMN real_invoice_id bigint;
        COMMENT ON COLUMN account_move_line.stored_invoice_id IS 'Invoice';
        """)

    logger.info('Computing field real_invoice_id on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line aml
        SET real_invoice_id = inv.id
        FROM account_move AS am, account_invoice AS inv
        WHERE am.id = aml.move_id
        AND am.id = inv.move_id
        """
    )

# -*- encoding: utf-8 -*-
# © 2019 Decodio Applications d.o.o. (davor.bojkic@decod.io)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, tools, _
from openerp.exceptions import Warning as UserError

class BaseUbl(models.AbstractModel):
    _inherit = 'base.ubl'
    _description = 'Common methods to generate and parse UBL XML files'

    @api.model
    def ubl_parse_party(self, party_node, ns):
        res = super(BaseUbl, self).ubl_parse_party(party_node, ns)

        return res


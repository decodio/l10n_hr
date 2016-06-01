# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 OCA-Croatia
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


import time
from openerp.report import report_sxw

class pdv(report_sxw.rml_parse):
    

    
    def __init__(self, cr, uid, name, context=None):
        super(pdv, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'lang': self.get_lang,
        })
    
    def get_lang(self):
        #nemam lang u contextu nikako... ?
        self.cr.execute("select id from res_lang where iso_code='hr'")
        res = self.cr.fetchone[0]
        return res
    

        
report_sxw.report_sxw('report.pdv', 
                      'l10n.hr.porez',
                      'addons/l10n_hr_report_pdv/report/pdv.rml',
                      parser=pdv, 
                      header=False)
        
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

class pdvs(report_sxw.rml_parse):
    
    
    def __init__(self, cr, uid, name, context=None):
        super(pdvs, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'totals':self.get_totals,
            'obrazac':context['active_id']
        })
    
    def get_totals(self,obj):
        self.cr.execute(""" 
        SELECT sum(dobra) uk_dobra
             , sum(usluge) uk_usluge
        FROM l10n_hr_pdvs_line
        WHERE obrazac = %(obrazac)s 
        """, {'obrazac':self.localcontext['obrazac']})
        res = self.cr.dictfetchone()
        return res

        
report_sxw.report_sxw('report.pdvs', 
                      'l10n.hr.porez',
                      'addons/l10n_hr_report_pdv/report/pdvs.rml',
                      parser=pdvs, 
                      header=False)
        
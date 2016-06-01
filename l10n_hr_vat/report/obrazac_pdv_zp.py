# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Author:
#    mail:
#    Copyright:
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


import time
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools.translate import _
from vat_book_report_common import get_vat_book_report_common


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        self.sums = {}
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_wizard_params': self.get_wizard_params,
            'get_lines': self.get_lines,
            'get_totals': self.get_totals,
            'get_company_data': self.get_company_data,
        })
        
    def get_month_name(self, cr, uid, month, context=None):
        _months = {1:_("siječanj"), 2:_("veljača"), 3:_("ožujak"), 4:_("travanj"), 5:_("svibanj"), 6:_("lipanj"), 7:_("srpanj"), 8:_("kolovoz"), 9:_("rujan"), 10:_("listopad"), 11:_("studeni"), 12:_("prosinac")}
        return _months[month]

    def get_wizard_params(self, date_start, company_id, fiscal_year_id, period_from):
        self.date_start = date_start
        self.company_id = company_id
        self.fiscal_year_id = fiscal_year_id
        self.period_from = period_from

    def get_lines(self):
        date_start = self.date_start
        month = int(date_start.split('-')[1])
        period_from = self.period_from
        self.cr.execute('''
            SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as row_number
                ,aml.partner_id
                ,rc.code as ccode
                ,coalesce (rp.name, 'neupisan') as partner_name
                ,coalesce (rp.vat, 'xxneupisan') as vat
                ,SUM(CASE WHEN aml.tax_code_id in (97) THEN aml.credit + aml.debit ELSE 0.00 END) as usluge
                ,0 as dob_4263  -- nemam definirano pa punim nule
                ,0 as dob_tro   -- al nek stoji ako zatreba definiracemo
                ,SUM(CASE WHEN aml.tax_code_id in (29366) THEN aml.credit + aml.debit ELSE 0.00 END) as dobra
            FROM account_move_line aml
             JOIN account_move am on am.id = aml.move_id
             LEFT JOIN res_partner rp on rp.id = aml.partner_id
             LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
            -- JOIN res_country rc on rc.id = rpa.country_id --v6
            WHERE am.state = 'posted'
              --AND rpa.type = 'default' --v6
              AND aml.tax_code_id in (29366) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
              AND aml.period_id = %(period)s
            GROUP BY
                aml.partner_id
                ,rp.name
                ,rp.vat
                ,rc.code'''
            % {'period': period_from}
                        )
        data = self.cr.dictfetchall()
        return data

    def get_totals(self):
       period_from = self.period_from
       self.cr.execute('''
            SELECT SUM(CASE WHEN aml.tax_code_id in (97) THEN aml.credit + aml.debit ELSE 0.00 END) as sum_usluge
                  ,SUM(CASE WHEN aml.tax_code_id in (29366) THEN aml.credit + aml.debit ELSE 0.00 END) as sum_dobra
            FROM account_move_line aml
             JOIN account_move am on am.id = aml.move_id
             LEFT JOIN res_partner rp on rp.id = aml.partner_id
             LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
            -- JOIN res_country rc on rc.id = rpa.country_id --v6
            WHERE 1=1
              AND am.state = 'posted'
              --AND rpa.type = 'default'  --v6
              AND aml.tax_code_id in (29366) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
              AND aml.period_id = %(period)s'''
            % {'period': period_from}
                        )
       pdvzp_sum = self.cr.dictfetchone()
       return pdvzp_sum

    def get_company_data(self):
        data = {}
        date_start = self.date_start
        month = int(date_start.split('-')[1])
        data['month_name'] = self.get_month_name(self.cr, self.uid, month)
        fiscal_year_id = self.fiscal_year_id
        data['year'] = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, fiscal_year_id).name
        company_id = self.company_id
        data['porezna_uprava'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).porezna_uprava
        data['ispostava'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).ispostava

        data['name'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).name
        data['zip'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).zip
        data['city'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).city
        data['street'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).street
        data['vat'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).partner_id.vat[2:]

        data['responsible_fname'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).responsible_fname
        data['responsible_lname'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).responsible_lname
        data['responsible_tel'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).responsible_tel
        data['responsible_email'] = self.pool.get('res.company').browse(self.cr, self.uid, company_id).responsible_email
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
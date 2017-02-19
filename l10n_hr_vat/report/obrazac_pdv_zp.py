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
        _months = {1: _("siječanj"), 2: _("veljača"), 3: _("ožujak"), 4: _("travanj"), 5: _("svibanj"),
                   6: _("lipanj"), 7: _("srpanj"), 8: _("kolovoz"), 9: _("rujan"), 10: _("listopad"),
                   11: _("studeni"), 12: _("prosinac")}
        return _months[month]

    def get_wizard_params(self, data):
        self.date_start = data['form'].get('date_start')
        self.company_id = data['form'].get('company_id')
        self.fiscal_year_id = data['form'].get('fiscal_year_id')
        self.period_from = data['form'].get('period_from')
        self.obrazac_id = data['form'].get('obrazac_id')
        self.fiscalyear_id = data['form'].get('fiscalyear_id')

    def _get_report_taxes(self, data):
        if not self.obrazac_id:
            return False
        columns = [11, 12, 13, 14]
        all_taxes = {}
        obrazac_stavka_obj = self.pool.get('l10n_hr_pdv.eu.obrazac.stavka')
        for col in columns:
            poz_id = self.pool.get('l10n_hr_pdv.report.eu.obrazac').search(self.cr,
                                                                           self.uid,
                                                                           [('obrazac_id', '=', self.obrazac_id),
                                                                            ('position', '=', str(col))])
            all_taxes[col] = None
            if poz_id:
                stavka_id = obrazac_stavka_obj.search(self.cr, self.uid,
                                                      [('obrazac_eu_id', '=', poz_id[0])])
                stavka = obrazac_stavka_obj.browse(self.cr, self.uid, stavka_id)
                taxes = []
                for st in stavka:
                    if st.tax_code_id:
                        taxes.append(st.tax_code_id.id)
                all_taxes[col] = taxes

        return all_taxes

    def _get_report_journals(self, data):
        if not self.obrazac_id:
            return False
        journals = []
        obrazac = self.pool.get('l10n_hr_pdv.eu.obrazac').browse(self.cr, self.uid, self.obrazac_id)
        for journal in obrazac.journal_ids:
            journals.append(journal.id)

        return journals

    def get_lines(self, data):
        date_start = self.date_start
        month = int(date_start.split('-')[1])
        period_from = self.period_from
        self.all_taxes = self._get_report_taxes(data)
        journals = self._get_report_journals(data)
        self.journals = '(' + str(journals).strip('[]') + ')'
        self.sum_col = []
        col11_sql = ' ,0.0 AS dobra_refund, 0.0 AS dobra_invoice '
        sum_col11_sql = ' ,0.0 AS usluge '
        col12_sql = ' ,0.0 AS dob_4263_refund, 0.0 AS dob_4263_invoice '
        sum_col12_sql = ' ,0.0 AS dob_4263 '
        col13_sql = ' ,0.0 AS dob_tro_refund, 0.0 AS dob_tro_invoice '
        sum_col13_sql = ' ,0.0 AS dob_tro '
        col14_sql = ' ,0.0 AS usluge_refund, 0.0 AS usluge_invoice '
        sum_col14_sql = ' ,0.0 AS usluge '
        if self.all_taxes[11]:
            self.sum_col.append(str(self.all_taxes[11]).strip('[]'))
            col11_sql = """
                        ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                           AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1
                          ELSE 0.00
                        END) as dobra_refund
                       ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                           AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit
                          ELSE 0.00
                      END) as dobra_invoice
            """ % {'journals': self.journals,
                   'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')',
                   }
            sum_col11_sql = """
                ,SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                 SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit ELSE 0.00 END) as dobra
            """ % {'journals': self.journals,
                   'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')',
                   }
        if self.all_taxes[12]:
            self.sum_col.append(str(self.all_taxes[12]).strip('[]'))
            col12_sql = """
                        ,SUM(CASE WHEN aml.tax_code_id in %(col12)s
                           AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1
                          ELSE 0.00
                        END) as dob_4263_refund
                       ,SUM(CASE WHEN aml.tax_code_id in %(col12)s
                           AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit
                          ELSE 0.00
                      END) as dob_4263_invoice
            """ % {'journals': self.journals,
                   'col12': '(' + str(self.all_taxes[12]).strip('[]') + ')',
                   }
            sum_col12_sql = """
                ,SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                 SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit ELSE 0.00 END) as dob_4263
            """ % {'journals': self.journals,
                   'col12': '(' + str(self.all_taxes[12]).strip('[]') + ')',
                   }
        if self.all_taxes[13]:
            self.sum_col.append(str(self.all_taxes[13]).strip('[]'))
            col13_sql = """
                        ,SUM(CASE WHEN aml.tax_code_id in %(col13)s
                           AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1
                          ELSE 0.00
                        END) as dob_tro_refund
                       ,SUM(CASE WHEN aml.tax_code_id in %(col13)s
                           AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit
                          ELSE 0.00
                      END) as dob_tro_invoice
            """ % {'journals': self.journals,
                   'col13': '(' + str(self.all_taxes[13]).strip('[]') + ')',
                   }
            sum_col13_sql = """
                ,SUM(CASE WHEN aml.tax_code_id in %(col13)s AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                 SUM(CASE WHEN aml.tax_code_id in %(col13)s AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit ELSE 0.00 END) as dob_tro
            """ % {'journals': self.journals,
                   'col13': '(' + str(self.all_taxes[13]).strip('[]') + ')',
                   }

        if self.all_taxes[14]:
            self.sum_col.append(str(self.all_taxes[14]).strip('[]'))
            col14_sql = """
                        ,SUM(CASE WHEN aml.tax_code_id in %(col14)s
                           AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1
                          ELSE 0.00
                        END) as usluge_refund
                       ,SUM(CASE WHEN aml.tax_code_id in %(col14)s
                           AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit
                          ELSE 0.00
                      END) as usluge_invoice
            """ % {'journals': self.journals,
                   'col14': '(' + str(self.all_taxes[14]).strip('[]') + ')',
                   }
            sum_col14_sql = """
                ,SUM(CASE WHEN aml.tax_code_id in %(col14)s AND am.journal_id in %(journals)s
                          THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                 SUM(CASE WHEN aml.tax_code_id in %(col14)s AND am.journal_id not in %(journals)s
                          THEN aml.credit + aml.debit ELSE 0.00 END) as usluge
            """ % {'journals': self.journals,
                   'col14': '(' + str(self.all_taxes[14]).strip('[]') + ')',
                   }
        sql = """
            SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as row_number
                ,aml.partner_id
                ,rc.code as ccode
                ,coalesce (rp.name, 'neupisan') as partner_name
                ,coalesce (rp.vat, 'xxneupisan') as vat
                """ + col11_sql + col12_sql + col13_sql + col14_sql + \
              sum_col11_sql + sum_col12_sql + sum_col13_sql + sum_col14_sql + """
            FROM account_move_line aml
             JOIN account_move am on am.id = aml.move_id
             LEFT JOIN res_partner rp on rp.id = aml.partner_id
             LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            WHERE am.state = 'posted'
              AND aml.tax_code_id in %(sum_col)s
              AND aml.period_id = %(period)s
            GROUP BY
                aml.partner_id
                ,rp.name
                ,rp.vat
                ,rc.code
            """ % {'period': period_from,
                   'sum_col': tuple(self.sum_col)
                   }

        self.cr.execute(sql)
        data = self.cr.dictfetchall()
        return data

    def get_totals(self):
        period_from = self.period_from
        total_col11_sql = ' , 0.0 AS sum_dobra '
        total_col12_sql = ' , 0.0 AS sum_dob_4263 '
        total_col13_sql = ' , 0.0 AS sum_dob_tro '
        total_col14_sql = ' , 0.0 AS sum_usluge '
        if self.all_taxes[11]:
            total_col11_sql = """
                  ,SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                            THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                            THEN aml.credit + aml.debit ELSE 0.00 END) as sum_dobra
            """ % {'journals': self.journals,
                   'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')',
                   }
        if self.all_taxes[12]:
            total_col12_sql = """
                  ,SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id in %(journals)s
                            THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id not in %(journals)s
                            THEN aml.credit + aml.debit ELSE 0.00 END) as sum_dob_4263
            """ % {'journals': self.journals,
                   'col12': '(' + str(self.all_taxes[12]).strip('[]') + ')',
                   }
        if self.all_taxes[13]:
            total_col13_sql = """
                  ,SUM(CASE WHEN aml.tax_code_id in %(col13)s AND am.journal_id in %(journals)s
                            THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col13)s AND am.journal_id not in %(journals)s
                            THEN aml.credit + aml.debit ELSE 0.00 END) as sum_dob_tro
            """ % {'journals': self.journals,
                   'col13': '(' + str(self.all_taxes[13]).strip('[]') + ')',
                   }
        if self.all_taxes[14]:
            total_col14_sql = """
                  ,SUM(CASE WHEN aml.tax_code_id in %(col14)s AND am.journal_id in %(journals)s
                            THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col14)s AND am.journal_id not in %(journals)s
                            THEN aml.credit + aml.debit ELSE 0.00 END) as sum_usluge
            """ % {'journals': self.journals,
                   'col14': '(' + str(self.all_taxes[14]).strip('[]') + ')',
                   }

        sql = """
            SELECT 1
                   """ + total_col11_sql + total_col12_sql + total_col13_sql + total_col14_sql + """
            FROM account_move_line aml
             JOIN account_move am on am.id = aml.move_id
             LEFT JOIN res_partner rp on rp.id = aml.partner_id
             LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            WHERE 1=1
              AND am.state = 'posted'
              AND aml.tax_code_id in %(sum_col)s
              AND aml.period_id = %(period)s
            """ % {'period': period_from,
                   'sum_col': tuple(self.sum_col)
                   }

        self.cr.execute(sql)
        pdvzp_sum = self.cr.dictfetchone()
        return pdvzp_sum

    def get_company_data(self):
        data = {}
        date_start = self.date_start
        month = int(date_start.split('-')[1])
        data['month_name'] = self.get_month_name(self.cr, self.uid, month)
        fiscal_year_id = self.fiscalyear_id
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
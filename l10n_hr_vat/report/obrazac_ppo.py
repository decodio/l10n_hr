# -*- encoding: utf-8 -*-


import time
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools.translate import _
from vat_book_report_common import get_vat_book_report_common


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        self.grand_total = 0.0
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_wizard_params': self.get_wizard_params,
            'get_lines_first': self.get_lines_first,
            'get_lines_second': self.get_lines_second,
            'get_lines_third': self.get_lines_third,
            'get_totals_first': self.get_totals_first,
            'get_totals_second': self.get_totals_second,
            'get_totals_third': self.get_totals_third,
            'get_grand_total': self.get_grand_total,
            'get_company_data': self.get_company_data,
        })
        
    def get_month_name(self, month):
        _months = {1:_("siječanj"), 2:_("veljača"), 3:_("ožujak"), 4:_("travanj"), 5:_("svibanj"),
                   6:_("lipanj"), 7:_("srpanj"), 8:_("kolovoz"), 9:_("rujan"), 10:_("listopad"),
                   11:_("studeni"), 12:_("prosinac")}
        return _months[month]

    def get_wizard_params(self, data):
        self.date_start = data['form'].get('date_start')
        self.company_id = data['form'].get('company_id')
        self.fiscal_year_id = data['form'].get('fiscal_year_id')
        self.period_from = data['form'].get('period_from')
        self.obrazac_id = data['form'].get('obrazac_id')
        self.fiscalyear_id = data['form'].get('fiscalyear_id')
        self.all_taxes = self._get_report_taxes(data)
        self.journals = self._get_report_journals(data)

    def _get_report_taxes(self, data):
        if not self.obrazac_id:
            return False
        columns = [11]
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

    def get_lines_first(self, data):
        period_from = self.period_from
        return self._calculate_lines(period_from)

    def get_lines_second(self, data):
        period_from = self.period_from + 1
        return self._calculate_lines(period_from)

    def get_lines_third(self, data):
        period_from = self.period_from + 2
        return self._calculate_lines(period_from)

    def _calculate_lines(self, period_from):
        sql = """
              SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as row_number
                  ,coalesce (rp.vat, 'xxneupisan') as vat
                  ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                             AND am.journal_id in %(journals)s
                            --THEN (aml.credit - aml.debit)  * -1
                            THEN aml.tax_amount  * -1
                            ELSE 0.00
                        END) as isporuke_refund
                  ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                             AND am.journal_id not in %(journals)s
                            --THEN aml.credit - aml.debit
                            THEN aml.tax_amount
                            ELSE 0.00
                        END) as isporuke_invoice
                  ,SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                            --THEN (aml.credit - aml.debit) * -1 ELSE 0.00 END)
                            THEN aml.tax_amount * -1 ELSE 0.00 END)
                     +
                   SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                            --THEN aml.credit - aml.debit ELSE 0.00 END) as isporuke
                            THEN aml.tax_amount ELSE 0.00 END) as isporuke
              FROM account_move_line aml
                  JOIN account_move am on am.id = aml.move_id
                  LEFT JOIN res_partner rp on rp.id = aml.partner_id
                  LEFT JOIN res_country rc on rc.id = rp.country_id
              WHERE 1=1
                AND am.state = 'posted'
                AND aml.tax_code_id in %(col11)s
                AND aml.period_id = %(period)s
              GROUP BY
                     aml.partner_id
                     ,rp.name
                     ,rp.vat
                     ,rc.code
              """ % {'period': period_from,
                     'journals': '(' + str(self.journals).strip('[]') + ')',
                     'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')'
                     }
        self.cr.execute(sql)
        data = self.cr.dictfetchall()
        return data

    def get_totals_first(self):
        period_from = self.period_from
        return self.calculate_totals(period_from)

    def get_totals_second(self):
        period_from = self.period_from + 1
        return self.calculate_totals(period_from)

    def get_totals_third(self):
        period_from = self.period_from + 2
        return self.calculate_totals(period_from)

    def calculate_totals(self, period_from):
        sql = """
            SELECT SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                           --THEN (aml.credit - aml.debit) * -1 ELSE 0.00 END)
                             THEN aml.tax_amount * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                           --THEN aml.credit - aml.debit ELSE 0.00 END)
                           THEN aml.tax_amount ELSE 0.00 END)
                   as sum_isporuke
                FROM account_move_line aml
                    JOIN account_move am on am.id = aml.move_id
                    LEFT JOIN res_partner rp on rp.id = aml.partner_id
                    LEFT JOIN res_country rc on rc.id = rp.country_id
                WHERE 1=1
                    AND am.state = 'posted'
                    AND aml.tax_code_id in %(col11)s
                    AND aml.period_id = %(period)s
            """ % {'period': period_from,
                   'journals': '(' + str(self.journals).strip('[]') + ')',
                   'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')'
                   }
        self.cr.execute(sql)
        ppo_sum = self.cr.dictfetchone()
        self.grand_total += ppo_sum.get('sum_isporuke', 0.0) or 0.0
        return ppo_sum

    def get_grand_total(self):
        return self.grand_total

    def get_company_data(self):
        data = {}
        date_start = self.date_start
        month = int(date_start.split('-')[1])
        data['start_month_name'] = self.get_month_name(month)
        data['end_month_name'] = self.get_month_name(month + 2)
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
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
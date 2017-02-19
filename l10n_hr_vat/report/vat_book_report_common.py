# -*- encoding: utf-8 -*-

from openerp.tools.translate import _

class get_vat_book_report_common(object):         

    def get_lines(self, report_object, data, stupci, row_start_values_sql, invoice_sql='', journal_sql= ''):
         
        periods_ids = report_object.period_ids
        knjiga_id = data['form']['knjiga_id'] or False
        company_id = report_object.pool.get('account.tax.code').browse(report_object.cr, report_object.uid, data['form']['chart_tax_id']).company_id.id or False
        if not knjiga_id:
            return False

        date_start = data['form']['date_start'] or False
        date_stop = data['form']['date_stop'] or False
        journal_ids = data['form']['journal_ids'] or []
        #journal_list = str(journal_ids)[1:-1]
        journal_list = journal_ids

        all_taxes = {}
        for stupac in stupci:
            poz_id = report_object.pool.get('l10n_hr_pdv.report.knjiga').search(report_object.cr, report_object.uid, [('knjiga_id','=',knjiga_id), ('position','=',str(stupac))])
            all_taxes[stupac] = None
            if poz_id:                 
                all_taxes[stupac] = report_object.pool.get('l10n_hr_pdv.report.knjiga.stavka').search(report_object.cr, report_object.uid, [('report_knjiga_id','=',poz_id[0])])
            
        stupciSql = {}
        sum_all_stupci = sum_sql = line_query2  = ''
        i = 0
        for stupac in stupci:
            i += 1
            stupciSql[stupac] = self.create_column_query(stupac, all_taxes, company_id, journal_list)
            sum_all_stupci += ' + stupac' + str(stupac)
            sum_sql += 'SUM(stupac' + str(stupac) + ') AS stupac' + str(stupac) + ' '
            stupacText = stupciSql[stupac]
            if not stupacText:
                stupacText = str(0)
            else:
                stupacText = '(' + stupciSql[stupac] + ')'
            line_query2 += stupacText + ' AS stupac' + str(stupac)
            if i < len(stupci):
                line_query2 += ', '
                sum_sql += ', '        
                              
        viewSQL = 'CREATE OR REPLACE VIEW l10n_hr_vat_' + str(report_object.uid) + ' AS '
        line_query = 'SELECT ' + row_start_values_sql + line_query2 + """ FROM l10n_hr_pdv_knjiga_stavka AS stavka 
            """ + invoice_sql + """
            --LEFT JOIN account_invoice AS invoice ON (invoice_id=invoice.id)
               --LEFT JOIN res_users AS users ON (invoice.user_id=users.id)
               LEFT JOIN account_move am ON (am.id=stavka.move_id)
               LEFT JOIN res_partner p ON (p.id=am.partner_id)                
                WHERE stavka.id """
        linesSelect = 'IN ( \
            select id from l10n_hr_pdv_knjiga_stavka \
                where (l10n_hr_pdv_knjiga_id=' + str(knjiga_id) + ') \
                    AND (period_id in (' + str(periods_ids).strip('[]') + '))'
        if date_start:
            linesSelect += " AND (invoice_date_invoice >= \'" + date_start + "\')"
        if date_stop:
            linesSelect += " AND (invoice_date_invoice <= \'" + date_stop + "\')" 
        linesSelect += ')'
        
        report_object.cr.execute(viewSQL + line_query + linesSelect)
        
        select_sql = 'SELECT * FROM l10n_hr_vat_' + str(report_object.uid) + \
            ' WHERE (' + sum_all_stupci + ') <> 0 ORDER BY invoice_date, rbr'
        report_object.cr.execute(select_sql) 
        res = report_object.cr.dictfetchall() 
        self.set_rbr(data, report_object, res)
        report_object.cr.execute('SELECT ' + sum_sql + ' FROM l10n_hr_vat_' + str(report_object.uid))       
        report_object.sums = report_object.cr.dictfetchall()
        report_object.cr.execute('DROP VIEW l10n_hr_vat_' + str(report_object.uid)) 
               
        return res

    def set_rbr(self, data, report_object, res):
        line_count = 0
        lines = res
        for line in lines:
            line_count += 1
            line['rbr'] = str(line_count) + '.'   

        
    def create_column_query(self, stupac, all_taxes, company_id, journal_list):
        if not all_taxes[stupac]:
            return None
        states = ['draft']
        sql = 'SELECT COALESCE(SUM(line.tax_amount)/COALESCE(AVG(NULLIF(knjiga_stavka.tax_code_koef,0)),1),0) AS tax_amount \
         FROM account_move_line AS line, \
         account_account AS account INNER JOIN \
         l10n_hr_pdv_report_knjiga_stavka AS knjiga_stavka ON (knjiga_stavka.id IN (' + str(all_taxes[stupac]).strip('[]')  + ')) \
         WHERE line.state NOT IN (' + str(states).strip('[]') + ') \
         AND line.tax_code_id IN (select id from account_tax_code where \
            (parent_left > (select parent_left from account_tax_code where id=knjiga_stavka.tax_code_id)) and \
            (parent_left < (select parent_right from account_tax_code where id=knjiga_stavka.tax_code_id)) or (id=knjiga_stavka.tax_code_id) order by id) \
        AND line.account_id = account.id \
        AND account.company_id = ' + str(company_id) + ' \
        AND line.period_id IN (stavka.period_id)  \
        AND line.move_id = stavka.move_id \
        AND line.journal_id IN (' + str(journal_list).strip('[]') + ') \
        AND account.active '
        
        return sql 

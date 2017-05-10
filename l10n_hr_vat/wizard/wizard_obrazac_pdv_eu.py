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

import os
import base64
from openerp.osv import orm, fields
from openerp.tools.translate import _
from datetime import datetime
from lxml import objectify
import xml_common as rc

class obrazac_pdv_eu(orm.TransientModel):
    _name = 'obrazac.pdv.eu'
    _inherit = 'account.common.report'

    _columns = {
        'chart_tax_id': fields.many2one('account.tax.code', 'Chart of Tax',
                                        help='Select Charts of Taxes', required=True,
                                        domain=[('parent_id', '=', False)]),
        'obrazac_id': fields.many2one('l10n_hr_pdv.eu.obrazac', 'Obrazac EU',
                                      help='Odaberite obrazac za ispis', required=True),
        'data': fields.binary('File', readonly=True),
        'name': fields.char('Filename', size=32, readonly=True),
        'state': fields.selection((('choose', 'choose'), ('get', 'get'), )),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(obrazac_pdv_eu, self).default_get(cr, uid, fields, context=context)
        res['state'] = 'choose'
        return res

    def _get_tax(self, cr, uid, context=None):
        taxes = self.pool.get('account.tax.code').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return taxes and taxes[0] or False

    _defaults = {
        'chart_tax_id': _get_tax
    }

    def _get_start_date(self, cr, uid, period_ids):
        start_date = None
        for period_id in period_ids:
            period_date_start = self.pool.get('account.period').browse(cr, uid, period_id).date_start
            if start_date is None:
                start_date = period_date_start
            return start_date
        else:
            return False

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        period_obj = self.pool.get('account.period')
        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        period_id = period_obj.search(cr, uid,
                            [('id', '=',  datas['form']['period_from']),
                             ('company_id', '=',  datas['form']['company_id']),
                             ('special', '=', False)])
        datas['form']['date_start'] = self._get_start_date(cr, uid, period_id)

#        if datas['form']['knjiga_id']:
#            knjiga_type = self.pool.get('l10n_hr_pdv.knjiga').browse(cr, uid, datas['form']['knjiga_id']).type
#        else:
#            raise orm.except_orm(_('Knjiga nije upisana!'),
#                                 _("Knjiga je obavezan podatak kod ovog ispisa!"))

#        if (datas['form']['period_from'] and not datas['form']['period_to']) or \
#            (not datas['form']['period_from'] and datas['form']['period_to']):
#            raise orm.except_orm(_('Krivi periodi!'),_("Potrebno je upisati oba perioda za ispis po periodima!"))
#
#        if (datas['form']['date_start'] and not datas['form']['date_stop']) or \
#            (not datas['form']['date_start'] and datas['form']['date_stop']):
#            raise orm.except_orm(_('Krivo razdoblje!'),_("Potrebno je upisati oba datuma za ispis po datumima!"))

        report_name = None
        obrazac = self.pool.get('l10n_hr_pdv.eu.obrazac').browse(cr, uid, datas['form']['obrazac_id'])
        if obrazac.type == 'pdv_s':
            report_name = 'obrazac_pdv_s_odt'
        if obrazac.type == 'pdv_zp':
            report_name = 'obrazac_pdv_zp_odt'
        if obrazac.type == 'ppo':
            report_name = 'obrazac_ppo_odt'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
        }

    def export_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        period_obj = self.pool.get('account.period')
        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        period = False
        # Za sada samo jedan period.
        # if datas['form']['period_from'] == datas['form']['period_to']:

        per = self.browse(cr, uid, ids[0]).period_from  # date_start date_end
        period = {'id': per.id,
                  'date_start': per.date_start,
                  'date_stop': per.date_stop}
        # period = datas['form']['period_from']['id']
        obrazac = self.pool.get('l10n_hr_pdv.eu.obrazac').browse(cr, uid, datas['form']['obrazac_id'])
        if period and obrazac.type == 'pdv_s':
            xml = self.generate_pdvs(cr, uid, datas, period, context)
        if period and obrazac.type == 'pdv_zp':
            xml = self.generate_pdvzp(cr, uid, datas, period, context)
        if period and obrazac.type == 'ppo':
            xml = self.generate_ppo(cr, uid, datas, period, context)

        xml['path'] = os.path.dirname(os.path.abspath(__file__))
        # VALIDACIJA preko xsd-a
        validate = rc.validate_xml(self, xml)
        if validate:
            data64 = base64.encodestring(xml['xml'].encode('windows-1250'))
            self.write(cr, uid, ids, {'state': 'get', 'data': data64, 'name': obrazac.name + '_export.xml'},
                              context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'obrazac.pdv.eu',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'views': [(False, 'form')],
            'target': 'new',
        }


    def _get_report_taxes(self, cr, uid, data, columns):
        obrazac_id = data['form'].get('obrazac_id', False)
        if not obrazac_id:
            return False
        all_taxes = {}
        obrazac_stavka_obj = self.pool.get('l10n_hr_pdv.eu.obrazac.stavka')
        for col in columns:
            poz_id = self.pool.get('l10n_hr_pdv.report.eu.obrazac').search(cr, uid,
                                                                           [('obrazac_id', '=', obrazac_id),
                                                                            ('position', '=', str(col))])
            all_taxes[col] = None
            if poz_id:
                stavka_id = obrazac_stavka_obj.search(cr, uid, [('obrazac_eu_id', '=', poz_id[0])])
                stavka = obrazac_stavka_obj.browse(cr, uid, stavka_id)
                taxes = []
                for st in stavka:
                    if st.tax_code_id:
                        taxes.append(st.tax_code_id.id)
                all_taxes[col] = taxes

        return all_taxes

    def _get_report_journals(self, cr, uid, data):
        obrazac_id = data['form'].get('obrazac_id', False)
        if not obrazac_id:
            return False
        journals = []
        obrazac = self.pool.get('l10n_hr_pdv.eu.obrazac').browse(cr, uid, obrazac_id)
        for journal in obrazac.journal_ids:
            journals.append(journal.id)

        return journals

    def generate_pdvzp(self, cr, uid, data, period, context=None):
        period_obj = self.pool.get('account.period')
        period_id = period_obj.search(cr, uid,
                                      [('id', '=', period['id']),
                                       ('company_id', '=', data['form']['company_id']),
                                       ('special', '=', False)])
        date_start = self._get_start_date(cr, uid, period_id)
        month = int(date_start.split('-')[1])
        self.all_taxes = self._get_report_taxes(cr, uid, data, [11, 12, 13, 14])
        journals = self._get_report_journals(cr, uid, data)
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
             --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id
             --LEFT JOIN res_country rc on rc.id = rpa.country_id
            WHERE am.state = 'posted'
              --AND rpa.type = 'default'
              AND aml.tax_code_id in %(sum_col)s
              AND aml.period_id = %(period)s
            GROUP BY
                aml.partner_id
                ,rp.name
                ,rp.vat
                ,rc.code
            """ % {'period': period['id'],
                   'sum_col': tuple(self.sum_col)
                   }

        cr.execute(sql)
        pdvzp_vals = cr.dictfetchall()

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
             --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id
             --LEFT JOIN res_country rc on rc.id = rpa.country_id
            WHERE 1=1
              AND am.state = 'posted'
              --AND rpa.type = 'default'
              AND aml.tax_code_id in %(sum_col)s
              AND aml.period_id = %(period)s
            """ % {'period': period['id'],
                   'sum_col': tuple(self.sum_col)
                   }

        cr.execute(sql)
        pdvzp_sum = cr.dictfetchone()

        for l in pdvzp_vals:
            if (not l['ccode'] or not l['vat']) or (l['ccode'] is None or l['vat'] is None):
                raise orm.except_orm(_('Invalid data!'),
                                     _("Partner (%s) does not have country code or vat number!") % l['partner_name'])

        EM = objectify.ElementMaker(annotate=False)
        zp_list = [EM.Isporuka(
            EM.RedBr(l['row_number']),
            EM.KodDrzave(l['ccode']),
            EM.PDVID(l['vat'].startswith(l['ccode']) and l['vat'][2:].strip() or l['vat'].strip()),
            EM.I1(l['dobra']),
            EM.I2(l['dob_4263']),
            EM.I3(l['dob_tro']),
            EM.I4(l['usluge'])) for l in pdvzp_vals if l['ccode'] and l['vat']]

        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka),
                           EM.IsporukeUkupno(
                               EM.I1(pdvzp_sum['sum_dobra']),
                               EM.I2('0'),
                               EM.I3('0'),
                               EM.I4(pdvzp_sum['sum_usluge'])))

        tijelo.Isporuke.Isporuka = zp_list
        author, company, metadata = rc.get_common_data(self, cr, uid, data, context)

        metadata[
            'naslov'] = u"Zbirna prijavu za isporuke dobara i usluga u druge države članice Europske unije"  # template.xsd_id.title
        metadata['uskladjenost'] = u"ObrazacZP-v1-0"  # template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        PDVZP = objectify.ElementMaker(annotate=False,
                                       namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacZP/v1-0")  # template.xsd_id.namespace)
        pdvzp = PDVZP.ObrazacZP(xml_metadata, xml_header, tijelo, verzijaSheme="1.0")  # template.xsd_id.version)

        # return rc.attachment_values(self, template, pdvs, identifikator)
        return {'xml': rc.etree_tostring(self, pdvzp),
                'xsd_path': 'shema/ZP',  # template data
                'xsd_name': 'ObrazacZP-v1-0.xsd'}

    def generate_pdvs(self, cr, uid, data, period, context=None):
        self.all_taxes = self._get_report_taxes(cr, uid, data, [11, 12])
        self.journals = self._get_report_journals(cr, uid, data)
        sql = """
         SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as rbr
             --,aml.partner_id
             --,coalesce (rp.name, 'neupisan') as name
             ,rc.code ccode
             ,coalesce (rp.vat, 'xxneupisan') as vat
             ,SUM(CASE WHEN aml.tax_code_id in %(col12)s
                        AND am.journal_id in %(journals)s
                       THEN (aml.credit + aml.debit) * -1
                       ELSE 0.00
                   END) as usluge_refund
             ,SUM(CASE WHEN aml.tax_code_id in %(col12)s
                        AND am.journal_id not in %(journals)s
                       THEN aml.credit + aml.debit
                       ELSE 0.00
                   END) as usluge_invoice
             ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                        AND am.journal_id in %(journals)s
                       THEN (aml.credit + aml.debit)  * -1
                       ELSE 0.00
                   END) as dobra_refund
             ,SUM(CASE WHEN aml.tax_code_id in %(col11)s
                        AND am.journal_id not in %(journals)s
                       THEN aml.credit + aml.debit
                       ELSE 0.00
                   END) as dobra_invoice
             ,SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id in %(journals)s
                       THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                +
              SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id not in %(journals)s
                       THEN aml.credit + aml.debit ELSE 0.00 END) as usluge
             ,SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                       THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                +
              SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                       THEN aml.credit + aml.debit ELSE 0.00 END) as dobra
         FROM account_move_line aml
             JOIN account_move am on am.id = aml.move_id
             LEFT JOIN res_partner rp on rp.id = aml.partner_id
             LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
             --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id
             /*
            LEFT JOIN LATERAL (SELECT partner_id, street, city, country_id, type
                 FROM res_partner_address
                WHERE partner_id =rp.id AND type = 'default'
                limit 1) rpa ON True
             LEFT JOIN res_country rc on rc.id = rpa.country_id
             */
         WHERE 1=1
           --AND rpa.type = 'default'
           AND am.state = 'posted'
           AND aml.tax_code_id in %(col11_12)s
           AND aml.period_id = %(period)s
         GROUP BY
                aml.partner_id
                ,rp.name
                ,rp.vat
                ,rc.code
         """ % {'period': period['id'],
                'journals': '(' + str(self.journals).strip('[]') + ')',
                'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')',
                'col12': '(' + str(self.all_taxes[12]).strip('[]') + ')',
                'col11_12': '(' + str(self.all_taxes[11]).strip('[]') + ',' + str(self.all_taxes[12]).strip('[]') + ')'
                }

        cr.execute(sql)
        pdvs_vals = cr.dictfetchall()

        sql = """
            SELECT SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id in %(journals)s
                            THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col12)s AND am.journal_id not in %(journals)s
                            THEN aml.credit + aml.debit ELSE 0.00 END)
                   as sum_usluge
                  ,SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id in %(journals)s
                           THEN (aml.credit + aml.debit) * -1 ELSE 0.00 END)
                   +
                   SUM(CASE WHEN aml.tax_code_id in %(col11)s AND am.journal_id not in %(journals)s
                           THEN aml.credit + aml.debit ELSE 0.00 END)
                   as sum_dobra
                FROM account_move_line aml
                    JOIN account_move am on am.id = aml.move_id
                    LEFT JOIN res_partner rp on rp.id = aml.partner_id
                    LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
                    --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id
                    /*
                   LEFT JOIN LATERAL (SELECT partner_id, street, city, country_id, type
                        FROM res_partner_address
                       WHERE partner_id =rp.id AND type = 'default'
                       limit 1) rpa ON True
                    LEFT JOIN res_country rc on rc.id = rpa.country_id
                    */
                WHERE 1=1
                    --AND rpa.type = 'default'
                    AND am.state = 'posted'
                    AND aml.tax_code_id in %(col11_12)s
                    AND aml.period_id = %(period)s
            """ % {'period': period['id'],
                   'journals': '(' + str(self.journals).strip('[]') + ')',
                   'col11': '(' + str(self.all_taxes[11]).strip('[]') + ')',
                   'col12': '(' + str(self.all_taxes[12]).strip('[]') + ')',
                   'col11_12': '(' + str(self.all_taxes[11]).strip('[]') + ',' + str(self.all_taxes[12]).strip(
                       '[]') + ')'
                   }
        cr.execute(sql)
        pdvs_sum = cr.dictfetchone()

        for l in pdvs_vals:
            if (not l['ccode'] or not l['vat']) or (l['ccode'] is None or l['vat'] is None):
                raise orm.except_orm(_('Invalid data!'),
                                     _("Partner (%s) does not have country code or vat number!") % l['partner_name'])
        # skucam retke u listu xml objekata
        EM = objectify.ElementMaker(annotate=False)
        pdvs_list = [EM.Isporuka(
            EM.RedBr(l['rbr']),
            EM.KodDrzave(l['ccode']),
            EM.PDVID(l['vat'].startswith(l['ccode']) and l['vat'][2:].strip() or l['vat'].strip()),
            EM.I1(l['dobra']),
            EM.I2(l['usluge'])) for l in pdvs_vals if l['ccode'] and l['vat']]

        # i sve to zgovnjam u report
        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka),
                           EM.IsporukeUkupno(
                               EM.I1(pdvs_sum['sum_dobra']),
                               EM.I2(pdvs_sum['sum_usluge'])))

        tijelo.Isporuke.Isporuka = pdvs_list

        author, company, metadata = rc.get_common_data(self, cr, uid, data, context)

        metadata[
            'naslov'] = u"Prijava za stjecanje dobara i primljene usluge iz drugih država članica Europske unije"  # template.xsd_id.title
        metadata['uskladjenost'] = u"ObrazacPDVS-v1-0"  # template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        PDVS = objectify.ElementMaker(annotate=False,
                                      namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDVS/v1-0")  # template.xsd_id.namespace)
        pdvs = PDVS.ObrazacPDVS(xml_metadata, xml_header, tijelo, verzijaSheme="1.0")  # template.xsd_id.version)

        # return rc.attachment_values(self, template, pdvs, identifikator)

        return {'xml': rc.etree_tostring(self, pdvs),
                'xsd_path': 'shema/PDV-S',  # template data
                'xsd_name': 'ObrazacPDVS-v1-0.xsd'}


    def generate_ppo(self, cr, uid, data, period, context=None):
        EM = objectify.ElementMaker(annotate=False)
        period_obj = self.pool.get('account.period')
        all_taxes = self._get_report_taxes(cr, uid, data, [11])
        journals = self._get_report_journals(cr, uid, data)
        grand_total = 0.0

        period_from = period.get('id')
        first_data = self._calculate_lines(cr, uid, period_from, all_taxes, journals)
        first_total = self.calculate_totals(cr, uid, period_from, all_taxes, journals)
        grand_total += first_total.get('sum_isporuke', 0.0) or 0.0
        for l in first_data:
            if not l['vat'] or l['vat'] is None:
                raise orm.except_orm(_('Invalid data!'),
                                     _("Partner (%s) does not have vat number!") % l['partner_name'])
        ppo_list = self._get_PPO_xml_lines(cr, uid, first_data, first_total, period_from)

        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka(EM.Podaci)),
                           EM.Iznos(first_total['sum_isporuke']),
                           EM.DatumOd(period.get('date_start')),
                           EM.DatumDo(period.get('date_stop')))

        tijelo.Isporuke.Isporuka.Podaci.Podatak = ppo_list

        second_period = period_obj.next(cr, uid, period_obj.browse(cr, uid, period_from), 1, context=context)
        second_data = self._calculate_lines(cr, uid, second_period, all_taxes, journals)
        second_total = self.calculate_totals(cr, uid, second_period, all_taxes, journals)
        grand_total += second_total.get('sum_isporuke', 0.0) or 0.0
        for l in second_data:
            if not l['vat'] or l['vat'] is None:
                raise orm.except_orm(_('Invalid data!'),
                                     _("Partner (%s) does not have vat number!") % l['partner_name'])
        second_ppo_list = self._get_PPO_xml_lines(cr, uid, second_data, second_total, second_period)
        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka(EM.Podaci)),
                           EM.Iznos(first_total['sum_isporuke']),
                           EM.DatumOd(period.get('date_start')),
                           EM.DatumDo(period.get('date_stop')))

        tijelo.Isporuke.Isporuka.Podaci.Podatak = second_ppo_list

        third_period = period_obj.next(cr, uid, period_obj.browse(cr, uid, second_period), 1, context=context)
        third_data = self._calculate_lines(cr, uid, third_period, all_taxes, journals)
        third_total = self.calculate_totals(cr, uid, third_period, all_taxes, journals)
        grand_total += third_total.get('sum_isporuke', 0.0) or 0.0
        for l in third_data:
            if not l['vat'] or l['vat'] is None:
                raise orm.except_orm(_('Invalid data!'),
                                     _("Partner (%s) does not have vat number!") % l['partner_name'])
        third_ppo_list = self._get_PPO_xml_lines(cr, uid, third_data, third_total, third_period)
        tijelo = EM.Tijelo(EM.Isporuke(EM.Isporuka(EM.Podaci)),
                           EM.Iznos(first_total['sum_isporuke']),
                           EM.DatumOd(period.get('date_start')),
                           EM.DatumDo(period.get('date_stop')))

        tijelo.Isporuke.Isporuka.Podaci.Podatak = third_ppo_list

        author, company, metadata = rc.get_common_data(self, cr, uid, data, context)

        metadata[
            'naslov'] = u"Prijava prijenosa porezne obveze"  # template.xsd_id.title
        metadata['uskladjenost'] = u"ObrazacPPO-v1-0"  # template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        PPO = objectify.ElementMaker(annotate=False,
                                      namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPPO/v1-0")  # template.xsd_id.namespace)
        ppo = PPO.ObrazacPPO(xml_metadata, xml_header, tijelo, verzijaSheme="1.0")  # template.xsd_id.version)

        return {'xml': rc.etree_tostring(self, ppo),
                'xsd_path': 'shema/PPO',  # template data
                'xsd_name': 'ObrazacPPO-v1-0.xsd'}

    def _get_PPO_xml_lines(self, cr, uid, lines, total, period):
        period_rec = self.pool.get('account.period').browse(cr, uid, period)
        EM = objectify.ElementMaker(annotate=False)
        ppo_list = [EM.Podatak(
            EM.RedniBroj(l['row_number']),
            EM.OIB(l['vat'].startswith('HR') and l['vat'][2:].strip() or l['vat'].strip()),
            EM.Iznos(l['isporuke'])) for l in lines if l['vat']]

        return ppo_list

    def _calculate_lines(self, cr, uid, period_from, all_taxes, journals):
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
                     'journals': '(' + str(journals).strip('[]') + ')',
                     'col11': '(' + str(all_taxes[11]).strip('[]') + ')'
                     }
        cr.execute(sql)
        data = cr.dictfetchall()
        return data


    def calculate_totals(self, cr, uid, period_from, all_taxes, journals):
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
                   'journals': '(' + str(journals).strip('[]') + ')',
                   'col11': '(' + str(all_taxes[11]).strip('[]') + ')'
                   }
        cr.execute(sql)
        pdvs_sum = cr.dictfetchone()
        return pdvs_sum



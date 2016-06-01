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
        'report_type': fields.selection([
                                        ('pdv_s', 'Obrazac PDV-S'),
                                        ('pdv_zp', 'Obrazac PDV-ZP'),
                                        ], 'Ispis', select=True, required=True),
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
        if datas['form']['report_type'] == 'pdv_s':
            report_name = 'obrazac_pdv_s_odt'
        if datas['form']['report_type'] == 'pdv_zp':
            report_name = 'obrazac_pdv_zp_odt'
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
        #Za sada samo jedan period.
        #if datas['form']['period_from'] == datas['form']['period_to']:

        per = self.browse(cr, uid, ids[0]).period_from # date_start date_end
        period = {'id':per.id,
                  'date_start':per.date_start,
                  'date_stop': per.date_stop}
        #period = datas['form']['period_from']['id']

        if period and datas['form']['report_type'] == 'pdv_s':
            xml = self.generate_pdvs(cr, uid, datas, period, context)
        if period and datas['form']['report_type'] == 'pdv_zp':
            xml = self.generate_pdvzp(cr, uid, datas, period, context)

        xml['path'] = os.path.dirname(os.path.abspath(__file__))
        #VALIDACIJA preko xsd-a
        validate = rc.validate_xml(self, xml)
        if validate:
            data64 = base64.encodestring(xml['xml'].encode('windows-1250'))
            return self.write(cr, uid, ids, {'state': 'get', 'data': data64, 'name': datas['form']['report_type'] + '_export.xml'},
                               context=context)
        #BOLE TODO : KAMO S NJIM???

    def generate_pdvzp(self, cr, uid, datas, period, context=None):
        cr.execute("""
        SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as row_number
            ,aml.partner_id
            ,rc.code as ccode
            ,coalesce (rp.name, 'neupisan') as partner_name
            ,coalesce (rp.vat, NULL) as vat
            ,SUM(CASE WHEN aml.tax_code_id in (97) THEN aml.credit + aml.debit ELSE 0.00 END) as usluge
            ,0 as dob_4263  -- nemam definirano pa punim nule
            ,0 as dob_tro   -- al nek stoji ako zatreba definiracemo
            ,SUM(CASE WHEN aml.tax_code_id in (29404, 29397) THEN aml.credit + aml.debit ELSE 0.00 END) as dobra
        FROM account_move_line aml
         JOIN account_move am on am.id = aml.move_id
         LEFT JOIN res_partner rp on rp.id = aml.partner_id
        LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
        --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
        --LEFT JOIN res_country rc on rc.id = rpa.country_id --v6
        WHERE am.state = 'posted'
          --AND rpa.type = 'default' --v6
          AND aml.tax_code_id in (29404, 29397,97) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
          AND aml.period_id = %(period)s
        GROUP BY
            aml.partner_id
            ,rp.name
            ,rp.vat
            ,rc.code
        """, {'period':period['id']})
        pdvzp_vals = cr.dictfetchall()

        cr.execute("""
        SELECT SUM(CASE WHEN aml.tax_code_id in (97) THEN aml.credit + aml.debit ELSE 0.00 END) as sum_usluge
              ,SUM(CASE WHEN aml.tax_code_id in (929404, 29397) THEN aml.credit + aml.debit ELSE 0.00 END) as sum_dobra
        FROM account_move_line aml
         JOIN account_move am on am.id = aml.move_id
         LEFT JOIN res_partner rp on rp.id = aml.partner_id
        LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
        --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
        --LEFT JOIN res_country rc on rc.id = rpa.country_id --v6
        WHERE am.state = 'posted'
          --AND rpa.type = 'default' v6
          AND aml.tax_code_id in (29404, 29397,97) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
          AND aml.period_id = %(period)s
        """, {'period':period['id']})
        pdvzp_sum = cr.dictfetchone()

        for l in pdvzp_vals:
            if (not l['ccode'] or not l['vat']) or (l['ccode'] is None or l['vat'] is None):
                raise orm.except_orm(_('Invalid data!'),_("Partner (%s) does not have country code or vat number!") % l['partner_name'])

        EM = objectify.ElementMaker(annotate=False)
        zp_list = [ EM.Isporuka(
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

        author, company, metadata = rc.get_common_data(self, cr, uid, datas, context)

        metadata['naslov']= u"Zbirna prijavu za isporuke dobara i usluga u druge države članice Europske unije"   #template.xsd_id.title
        metadata['uskladjenost'] = u"ObrazacZP-v1-0"              #template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        PDVZP = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacZP/v1-0")   #template.xsd_id.namespace)
        pdvzp = PDVZP.ObrazacZP(xml_metadata, xml_header, tijelo, verzijaSheme="1.0" )   #template.xsd_id.version)

        #return rc.attachment_values(self, template, pdvs, identifikator)
        return {'xml':rc.etree_tostring(self, pdvzp),
                'xsd_path':'shema/ZP',                # template data
                'xsd_name':'ObrazacZP-v1-0.xsd'}

    def generate_pdvs(self, cr, uid, datas, period, context=None):
        #dohvat redaka
        cr.execute("""
        SELECT ROW_NUMBER() OVER (Order by aml.partner_id) as rbr
            --,aml.partner_id
            --,coalesce (rp.name, 'neupisan') as name
            ,rc.code ccode
            ,coalesce (rp.name, 'neupisan') as partner_name
            ,coalesce (rp.vat, NULL) as vat
            ,SUM(CASE WHEN aml.tax_code_id in (202) THEN aml.credit + aml.debit ELSE 0.00 END) as usluge
            ,SUM(CASE WHEN aml.tax_code_id in (29401) THEN aml.credit + aml.debit ELSE 0.00 END) as dobra
        FROM account_move_line aml
            JOIN account_move am on am.id = aml.move_id
            LEFT JOIN res_partner rp on rp.id = aml.partner_id
            LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
            --LEFT JOIN res_country rc on rc.id = rpa.country_id --v6
        WHERE 1=1
          --AND rpa.type = 'default' --v6
          AND am.state = 'posted'
          AND aml.tax_code_id in (29401) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
          AND aml.period_id = %(period)s
        GROUP BY
                   aml.partner_id
                   ,rp.name
                   ,rp.vat
                   ,rc.code
        """, {'period':period['id']})
        pdvs_vals = cr.dictfetchall()

        cr.execute("""
        SELECT SUM(CASE WHEN aml.tax_code_id in (202) THEN aml.credit + aml.debit ELSE 0.00 END ) as sum_usluge
              ,SUM(CASE WHEN aml.tax_code_id in (29401) THEN aml.credit + aml.debit ELSE 0.00 END ) as sum_dobra
        FROM account_move_line aml
            JOIN account_move am on am.id = aml.move_id
            LEFT JOIN res_partner rp on rp.id = aml.partner_id
            LEFT JOIN res_country rc on rc.id = rp.country_id --v7,v8
            --LEFT JOIN res_partner_address rpa on rpa.partner_id = rp.id --v6
            --LEFT JOIN res_country rc on rc.id = rpa.country_id --v6
        WHERE 1=1
            --AND rpa.type = 'default' --v6
            AND am.state = 'posted'
            AND aml.tax_code_id in (29401) -- TODO: konfiguracijska tablica kao za PDV obrazac i knjige
            AND aml.period_id = %(period)s
        """, {'period':period['id']})
        pdvs_sum = cr.dictfetchone()

        for l in pdvs_vals:
            if (not l['ccode'] or not l['vat']) or (l['ccode'] is None or l['vat'] is None):
                raise orm.except_orm(_('Invalid data!'),_("Partner (%s) does not have country code or vat number!") % l['partner_name'])
        #skucam retke u listu xml objekata
        EM = objectify.ElementMaker(annotate=False)
        pdvs_list = [ EM.Isporuka(
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

        author, company, metadata = rc.get_common_data(self, cr, uid, datas, context)

        metadata['naslov']= u"Prijava za stjecanje dobara i primljene usluge iz drugih država članica Europske unije"   #template.xsd_id.title
        metadata['uskladjenost'] = u"ObrazacPDVS-v1-0"              #template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        PDVS = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDVS/v1-0")   #template.xsd_id.namespace)
        pdvs = PDVS.ObrazacPDVS(xml_metadata, xml_header, tijelo, verzijaSheme="1.0" )   #template.xsd_id.version)

        #return rc.attachment_values(self, template, pdvs, identifikator)

        return {'xml':rc.etree_tostring(self, pdvs),
                'xsd_path':'shema/PDV-S',                # template data
                'xsd_name':'ObrazacPDVS-v1-0.xsd'}

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

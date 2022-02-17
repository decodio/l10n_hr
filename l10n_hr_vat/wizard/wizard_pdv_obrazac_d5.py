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
from openerp.osv import orm, fields
from openerp.tools.translate import _
from datetime import datetime

#import xml.etree.cElementTree as ET fuj.. .ruzno.. .dosadno...
from lxml import objectify  # niceee.. clean...

# no need for this ... -> xml_common
#import uuid no
#import base64
import base64
import xml_common as rc



class pdv_obrazac(orm.TransientModel):
    _name = 'pdv.obrazac'
    _inherit = 'account.common.report'

    _columns = {
        'chart_tax_id': fields.many2one('account.tax.code', 'Chart of Tax',
                help='Select Charts of Taxes', required=True, domain=[('parent_id', '=', False)]),
        'obrazac_id': fields.many2one('l10n_hr_pdv.obrazac', 'Obrazac PDV', select=True, required=True),
        'data': fields.binary('File', readonly=True),
        'name': fields.char('Filename', size=16, readonly=True),
        'state': fields.selection((('choose', 'choose'), ('get', 'get'), )),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(pdv_obrazac, self).default_get(cr, uid, fields, context=context)
        res['state'] = 'choose'
        return res

    def _get_tax(self, cr, uid, context=None):
        taxes = self.pool.get('account.tax.code').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return taxes and taxes[0] or False

    _defaults = {
        'chart_tax_id': _get_tax
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        if datas['form']['period_to']:
            cr.execute("select date_stop from account_period WHERE id = %s", [datas['form']['period_to'][0]])
            last_date = cr.fetchone()[0]
        if last_date < '2013-07-01':  # Which report will be printed depends on date when it was valid
            report_name = 'pdv.obrazac'
        elif last_date < '2014-01-01':
            report_name = 'pdv.obrazac.july.2013'
        elif last_date < '2015-01-01':
            report_name = 'pdv.obrazac.january.2014'           
        else:
            report_name = 'pdv.obrazac.january.2015'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
        }

    def export_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        if 'company_id' in datas['form'].keys():
            if isinstance(datas['form']['company_id'], tuple):
                datas['form']['company_id'] = datas['form']['company_id'][0]
        res = {}
        self.period_ids = []
        #self.name = 'pdv.obrazac'
        period_obj = self.pool.get('account.period')
        res['periods'] = ''
        res['fiscalyear'] = datas['form'].get('fiscalyear_id', False)[0]
        if datas['form'].get('period_from', False) and datas['form'].get('period_to', False):
            self.period_ids = period_obj.build_ctx_periods(cr, uid, 
                                  datas['form']['period_from'][0], datas['form']['period_to'][0])
        if not self.period_ids:
            cr.execute("select id from account_period where fiscalyear_id = %s", (res['fiscalyear'], ))
            periods = cr.fetchall()
            period_ids = [p[0] for p in periods]
        if self.period_ids:
            if type(self.period_ids) is not list:
                self.period_ids = [self.period_ids]
        self.cr = cr
        self.uid = uid

        #BOLE:
        if self.period_ids and len(self.period_ids) == 1:
            cr.execute("""select date_start, date_stop from account_period where id =%(id)s""", {'id':self.period_ids[0]})
        elif self.period_ids and len(self.period_ids) > 1:
            cr.execute("""select min(date_start) as date_start,
                          max(date_stop) as date_stop 
                          from account_period where id in %s""", (tuple(self.period_ids),))
        else:
            #ako nema perioda ? raise* exit?
            pass

        period = cr.dictfetchone()

        EM = objectify.ElementMaker(annotate=False)
        tijelo = EM.Tijelo(
                    EM.Podatak000("%.2f" % (self._get_value(cr, uid, datas, 'A', 1) or 0)),
                    EM.Podatak100("%.2f" % (self._get_value(cr, uid, datas, 'I', 1) or 0)),
                    EM.Podatak101("%.2f" % (self._get_value(cr, uid, datas, 'I1', 1) or 0)),
                    EM.Podatak102("%.2f" % (self._get_value(cr, uid, datas, 'I2', 1) or 0)),
                    EM.Podatak103("%.2f" % (self._get_value(cr, uid, datas, 'I3', 1) or 0)),
                    EM.Podatak104("%.2f" % (self._get_value(cr, uid, datas, 'I4', 1) or 0)),
                    EM.Podatak105("%.2f" % (self._get_value(cr, uid, datas, 'I5', 1) or 0)),
                    EM.Podatak106("%.2f" % (self._get_value(cr, uid, datas, 'I6', 1) or 0)),
                    EM.Podatak107("%.2f" % (self._get_value(cr, uid, datas, 'I7', 1) or 0)),
                    EM.Podatak108("%.2f" % (self._get_value(cr, uid, datas, 'I8', 1) or 0)),
                    EM.Podatak109("%.2f" % (self._get_value(cr, uid, datas, 'I9', 1) or 0)),
                    EM.Podatak110("%.2f" % (self._get_value(cr, uid, datas, 'I10', 1) or 0)),
                    EM.Podatak200(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II', 2) or 0))),
                    EM.Podatak201(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II1', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II1', 2) or 0))),
                    EM.Podatak202(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II2', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II2', 1) or 0))),
                    EM.Podatak203(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II3', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II3', 2) or 0))),
                    EM.Podatak204(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II4', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II4', 2) or 0))),
                    EM.Podatak205(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II5', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II5', 2) or 0))),
                    EM.Podatak206(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II6', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II6', 2) or 0))),
                    EM.Podatak207(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II7', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II7', 2) or 0))),
                    EM.Podatak208(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II8', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II8', 2) or 0))),
                    EM.Podatak209(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II9', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II9', 2) or 0))),
                    EM.Podatak210(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II10', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II10', 2) or 0))),
                    EM.Podatak211(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II11', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II11', 2) or 0))),
                    EM.Podatak212(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II12', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II12', 2) or 0))),
                    EM.Podatak213(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II13', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II13', 2) or 0))),
                    EM.Podatak214(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II14', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II14', 2) or 0))),
                    EM.Podatak215(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'II15', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'II15', 2) or 0))),
                    EM.Podatak300(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III', 2) or 0))),
                    EM.Podatak301(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III1', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III1', 2) or 0))),
                    EM.Podatak302(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III2', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III2', 2) or 0))),
                    EM.Podatak303(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III3', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III3', 2) or 0))),
                    EM.Podatak304(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III4', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III4', 2) or 0))),
                    EM.Podatak305(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III5', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III5', 2) or 0))),
                    EM.Podatak306(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III6', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III6', 2) or 0))),
                    EM.Podatak307(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III7', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III7', 2) or 0))),
                    EM.Podatak308(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III8', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III8', 2) or 0))),
                    EM.Podatak309(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III9', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III9', 2) or 0))),
                    EM.Podatak310(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III10', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III10', 2) or 0))),
                    EM.Podatak311(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III11', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III11', 2) or 0))),
                    EM.Podatak312(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III12', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III12', 2) or 0))),
                    EM.Podatak313(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III13', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III13', 2) or 0))),
                    EM.Podatak314(EM.Vrijednost("%.2f" % (self._get_value(cr, uid, datas, 'III14', 1) or 0)), EM.Porez("%.2f" % (self._get_value(cr, uid, datas, 'III14', 2) or 0))),
                    EM.Podatak315("%.2f" % (self._get_value(cr, uid, datas, 'III15', 2) or 0)),
                    EM.Podatak400("%.2f" % abs((self._get_value(cr, uid, datas, 'IV', 2) or 0))),
                    EM.Podatak500("%.2f" % abs((self._get_value(cr, uid, datas, 'V', 2) or 0))),
                    EM.Podatak600("%.2f" % abs((self._get_value(cr, uid, datas, 'VI', 2) or 0))),
                    EM.Podatak700(0.0),
                    EM.Podatak810("%.2f" % (self._get_value(cr, uid, datas, 'VIII1', 1) or 0)),
                    EM.Podatak811("%.2f" % (self._get_value(cr, uid, datas, 'VIII11', 1) or 0)),
                    EM.Podatak812("%.2f" % (self._get_value(cr, uid, datas, 'VIII12', 1) or 0)),
                    EM.Podatak813("%.2f" % (self._get_value(cr, uid, datas, 'VIII13', 1) or 0)),
                    EM.Podatak814("%.2f" % (self._get_value(cr, uid, datas, 'VIII14', 1) or 0)),
                    EM.Podatak815("%.2f" % (self._get_value(cr, uid, datas, 'VIII15', 1) or 0)),
                    EM.Podatak820("%.2f" % (self._get_value(cr, uid, datas, 'VIII2', 1) or 0)),
                    EM.Podatak830("%.2f" % (self._get_value(cr, uid, datas, 'VIII3', 1) or 0)),
                    EM.Podatak831("%.2f" % (self._get_value(cr, uid, datas, 'VIII31', 1) or 0), EM.Broj(0)),
                    EM.Podatak832("%.2f" % (self._get_value(cr, uid, datas, 'VIII32', 1) or 0), EM.Broj(0)),
                    EM.Podatak833("%.2f" % (self._get_value(cr, uid, datas, 'VIII33', 1) or 0), EM.Broj(0)),
                    EM.Podatak840("%.2f" % (self._get_value(cr, uid, datas, 'VIII4', 1) or 0)),
                    EM.Podatak850("%.2f" % (self._get_value(cr, uid, datas, 'VIII5', 1) or 0)),
                    EM.Podatak860("%.2f" % (self._get_value(cr, uid, datas, 'VIII6', 1) or 0)),
                    EM.Podatak870(False)                                                                             
                    )        

        author, company, metadata = rc.get_common_data(self, cr, uid, datas)

        metadata['naslov']= u"Prijava poreza na dodanu vrijednost"   #template.xsd_id.title
        metadata['uskladjenost'] = u'ObrazacPDV-v9-0'                #template.xsd_id.name

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        OBRAZACPDV = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDV/v9-0")   #template.xsd_id.namespace)
        obrazacpdv = OBRAZACPDV.ObrazacPDV(xml_metadata, xml_header, tijelo, verzijaSheme="9.0" )   #template.xsd_id.version)

        xml = {'xml': rc.etree_tostring(self, obrazacpdv),
               'xsd_path':'shema/PDV2015', # template data
               'xsd_name':'ObrazacPDV-v9-0.xsd'}
        xml['path'] = os.path.dirname(os.path.abspath(__file__))

        validate = rc.validate_xml(self, xml)
        if validate:
            data64 = base64.encodestring(xml['xml'].encode('windows-1250'))
            self.write(cr, uid, ids, {'state': 'get', 'data': data64, 'name': 'pdv_export.xml'},
                           context=context)
        #msg = ET.tostring(ObrazacPDV)
        #msg = '<?xml version="1.0" encoding="windows-1250" standalone="yes"?>' + msg  
        #data64 = base64.encodestring(msg.encode('windows-1250'))
        #return self.write(cr, uid, ids, {'state': 'get', 'data': data64, 'name': 'pdv_export.xml'},
        #                   context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pdv.obrazac',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'views': [(False, 'form')],
            'target': 'new',
        }  

    def _get_company_nkd(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.l10n_hr_base_nkd_id and \
            self.pool.get('account.tax.code').browse(cr, uid,
                         data['form']['chart_tax_id'][0]).company_id.l10n_hr_base_nkd_id.code or False
        return name

    def _get_company_oib(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.partner_id.vat and \
            self.pool.get('account.tax.code').browse(cr, uid,
                         data['form']['chart_tax_id'][0]).company_id.partner_id.vat[2:] or False
        return name

    def _get_company_name(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.name or False
        return name

    def _get_company_city(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                            data['form']['chart_tax_id'][0]).company_id.city or False
        return name

    def _get_company_sreet(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.street or False
        return name

    def _get_author_fname(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.responsible_fname or False
        if not name:
            raise orm.except_orm(_('Error'), _('Podaci za PDV export nisu popunjeni.'))
        return name

    def _get_author_lname(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.responsible_lname or False
        if not name:
            raise orm.except_orm(_('Error'), _('Podaci za PDV export nisu popunjeni.'))
        return name

    def _get_author_tel(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.responsible_tel or False
        return name

    def _get_author_email(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.responsible_email or False
        return name

    def _get_ispostava(self, cr, uid, data):
        name = self.pool.get('account.tax.code').browse(cr, uid,
                             data['form']['chart_tax_id'][0]).company_id.ispostava or False
        return name

    def _get_start_date(self, cr, uid, data):
        start_date = None
        if self.period_ids:
            for period in self.period_ids:
                period_date_start = self.pool.get('account.period').browse(cr, uid, period).date_start
                if start_date is None:
                    start_date = period_date_start
                if datetime.strptime(period_date_start, '%Y-%m-%d') < datetime.strptime(start_date, '%Y-%m-%d'):
                    start_date = period_date_start
            return start_date
        else:
            return False

    def _get_end_date(self, cr, uid, data):
        end_date = None
        if self.period_ids:
            for period in self.period_ids:
                period_date_stop = self.pool.get('account.period').browse(cr, uid, period).date_stop
                if end_date is None:
                    end_date = period_date_stop
                if datetime.strptime(period_date_stop, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                    end_date = period_date_stop
            return end_date
        else:
            return False

    def _get_value(self, cr, uid, data, poz, rbr):
        value = 0.0
        value_sum = 0.0
        atc_obj = self.pool.get('account.tax.code')
        #company_id = self.pool.get('account.tax.code').browse(self.cr, self.uid, data['form']['chart_tax_id'][0]).company_id.id or False

        if poz:
            poz_id = self.pool.get('l10n_hr_pdv.report.obrazac').search(self.cr, self.uid,
                                                                    [('position', '=', poz)])
            if poz_id:
                obrazac = self.pool.get('l10n_hr_pdv.report.obrazac').browse(self.cr, self.uid, poz_id[0])
                base_code_ids = obrazac.stavka_osnovice_ids
                tax_code_ids = obrazac.stavka_poreza_ids
                tax_code_2_ids = obrazac.stavka_nepriznati_porez_ids
            else:
                return value
        else:
            return value

        if rbr == 0:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), tax_code_2_ids)
        elif rbr == 1:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), base_code_ids)
        else:
            current_tax_code_ids = map(lambda x: (x.base_code_id.id, x.base_code_tax_koef), tax_code_ids)

        if len(self.period_ids) == 1:
            where_clause = 'and line.period_id = ' + str(self.period_ids[0])
        else:
            where_clause = 'and line.period_id in ' + str(tuple(self.period_ids))

        for line in current_tax_code_ids:
            value_tax = atc_obj._sum(self.cr, self.uid, [line[0]], self, {}, {}, where_clause)
            if value_tax:
                value = value_tax[line[0]]
            if line[1] == 0:
                value = 0
            else:
                value = value / line[1]
            value_sum += value

        return value_sum or 0.0

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

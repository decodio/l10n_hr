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

from openerp.osv import orm, fields
import xml.etree.cElementTree as ET
import uuid
from datetime import datetime
import xml
import base64
from openerp.tools.translate import _


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
            for p in periods:
                self.period_ids.append(p[0])

        if self.period_ids:
            if type(self.period_ids) is not list:
                self.period_ids = [self.period_ids]
        self.cr = cr
        self.uid = uid

        ObrazacPDV = ET.Element("ObrazacPDV")
        ObrazacPDV.set("verzijaSheme", "10.0")
        ObrazacPDV.set("xmlns", "http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPDV/v10-0")
        
        Metapodaci = ET.SubElement(ObrazacPDV,"Metapodaci")
        Metapodaci.set("xmlns", "http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0")
        
        Naslov = ET.SubElement(Metapodaci, "Naslov")
        Naslov.text = "Prijava poreza na dodanu vrijednost"
        Naslov.set("dc", "http://purl.org/dc/elements/1.1/title")
        Autor = ET.SubElement(Metapodaci, "Autor")
        Autor.text = self._get_author_fname(cr, uid, datas) + " " + self._get_author_lname(cr, uid, datas)
        Autor.set("dc", "http://purl.org/dc/elements/1.1/creator")
        Datum = ET.SubElement(Metapodaci, "Datum")
        Datum.text = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
        Datum.set("dc", "http://purl.org/dc/elements/1.1/date")
        Format = ET.SubElement(Metapodaci, "Format")
        Format.text = "text/xml"
        Format.set("dc", "http://purl.org/dc/elements/1.1/format")
        Jezik = ET.SubElement(Metapodaci, "Jezik")
        Jezik.text = "hr-HR"
        Jezik.set("dc", "http://purl.org/dc/elements/1.1/language")
        Identifikator = ET.SubElement(Metapodaci, "Identifikator")
        Identifikator.text = str(uuid.uuid1())
        Identifikator.set("dc", "http://purl.org/dc/elements/1.1/identifier")
        Uskladjenost = ET.SubElement(Metapodaci, "Uskladjenost")
        Uskladjenost.text = "ObrazacPDV-v10-0"
        Uskladjenost.set("dc", "http://purl.org/dc/terms/conformsTo")
        Tip = ET.SubElement(Metapodaci, "Tip")
        Tip.text = u"Elektronički obrazac"
        Tip.set("dc", "http://purl.org/dc/elements/1.1/type")
        Adresant = ET.SubElement(Metapodaci, "Adresant")
        Adresant.text = "Ministarstvo Financija, Porezna uprava, Zagreb"
        
        Zaglavlje = ET.SubElement(ObrazacPDV, "Zaglavlje")
        
        Razdoblje = ET.SubElement(Zaglavlje, "Razdoblje")
        
        DatumOd = ET.SubElement(Razdoblje, "DatumOd")
        DatumOd.text = self._get_start_date(cr, uid, datas)
        DatumDo = ET.SubElement(Razdoblje, "DatumDo")
        DatumDo.text = self._get_end_date(cr, uid, datas)
        
        Obveznik = ET.SubElement(Zaglavlje, "Obveznik")
        
        Naziv = ET.SubElement(Obveznik, "Naziv")
        Naziv.text = self._get_company_name(cr, uid, datas)
        OIB = ET.SubElement(Obveznik, "OIB")
        OIB.text = self._get_company_oib(cr, uid, datas)
        #SifraDjelatnosti = ET.SubElement(Obveznik, "SifraDjelatnosti")
        #SifraDjelatnosti.text = self._get_company_nkd(cr, uid, datas)
        Adresa = ET.SubElement(Obveznik, "Adresa")
        
        Mjesto = ET.SubElement(Adresa, "Mjesto")
        Mjesto.text = self._get_company_city(cr, uid, datas)
        full_addr = self._get_company_sreet(cr, uid, datas)
        part_addr = full_addr.split(' ')
        num = part_addr[len(part_addr) - 1]
        addr = ""
        for index in range(len(part_addr) - 1):
            addr += part_addr[index]+" "
        if len(addr) > 0:
            addr = addr[:-1]
        Ulica = ET.SubElement(Adresa, "Ulica")
        Ulica.text = addr
        Broj = ET.SubElement(Adresa, "Broj")
        Broj.text = num
        
        ObracunSastavio = ET.SubElement(Zaglavlje, "ObracunSastavio")
        
        Ime = ET.SubElement(ObracunSastavio, "Ime")
        Ime.text = self._get_author_fname(cr, uid, datas)
        Prezime = ET.SubElement(ObracunSastavio, "Prezime")
        Prezime.text = self._get_author_lname(cr, uid, datas)
        #Telefon = ET.SubElement(ObracunSastavio, "Telefon")
        #Telefon.text = self._get_author_tel(cr, uid, datas)
        #Email = ET.SubElement(ObracunSastavio, "Email")
        #Email.text = self._get_author_email(cr, uid, datas)
        
        Ispostava = ET.SubElement(Zaglavlje, "Ispostava")
        Ispostava.text = self._get_ispostava(cr, uid, datas)
        
        Tijelo = ET.SubElement(ObrazacPDV, "Tijelo")
        
        Podatak000 = ET.SubElement(Tijelo, "Podatak000")
        Podatak000.text = "%.2f" % (self._get_value(cr, uid, datas,'A',1) or 0)
        Podatak100 = ET.SubElement(Tijelo, "Podatak100")
        Podatak100.text = "%.2f" % (self._get_value(cr, uid, datas,'I',1) or 0)
        Podatak101 = ET.SubElement(Tijelo, "Podatak101")
        Podatak101.text = "%.2f" % (self._get_value(cr, uid, datas,'I1',1) or 0)
        Podatak102 = ET.SubElement(Tijelo, "Podatak102")
        Podatak102.text = "%.2f" % (self._get_value(cr, uid, datas,'I2',1) or 0)
        Podatak103 = ET.SubElement(Tijelo, "Podatak103")
        Podatak103.text = "%.2f" % (self._get_value(cr, uid, datas,'I3',1) or 0)
        Podatak104 = ET.SubElement(Tijelo, "Podatak104")
        Podatak104.text = "%.2f" % (self._get_value(cr, uid, datas,'I4',1) or 0)
        Podatak105 = ET.SubElement(Tijelo, "Podatak105")
        Podatak105.text = "%.2f" % (self._get_value(cr, uid, datas,'I5',1) or 0)
        Podatak106 = ET.SubElement(Tijelo, "Podatak106")
        Podatak106.text = "%.2f" % (self._get_value(cr, uid, datas,'I6',1) or 0)
        Podatak107 = ET.SubElement(Tijelo, "Podatak107")
        Podatak107.text = "%.2f" % (self._get_value(cr, uid, datas,'I7',1) or 0)
        Podatak108 = ET.SubElement(Tijelo, "Podatak108")
        Podatak108.text = "%.2f" % (self._get_value(cr, uid, datas,'I8',1) or 0)  
        Podatak109 = ET.SubElement(Tijelo, "Podatak109")
        Podatak109.text = "%.2f" % (self._get_value(cr, uid, datas,'I9',1) or 0)
        Podatak110 = ET.SubElement(Tijelo, "Podatak110")
        Podatak110.text = "%.2f" % (self._get_value(cr, uid, datas,'I10',1) or 0)
        Podatak111 = ET.SubElement(Tijelo, "Podatak111")
        Podatak111.text = "%.2f" % (self._get_value(cr, uid, datas, 'I11', 1) or 0)
        Podatak200 = ET.SubElement(Tijelo, "Podatak200")
        Vrijednost200 = ET.SubElement(Podatak200, "Vrijednost")
        Vrijednost200.text = "%.2f" % (self._get_value(cr, uid, datas,'II',1) or 0)
        Porez200 = ET.SubElement(Podatak200, "Porez")
        Porez200.text = "%.2f" % (self._get_value(cr, uid, datas,'II',2) or 0)
        Podatak201 = ET.SubElement(Tijelo, "Podatak201")
        Vrijednost201 = ET.SubElement(Podatak201, "Vrijednost")
        Vrijednost201.text = "%.2f" % (self._get_value(cr, uid, datas,'II1',1) or 0)
        Porez201 = ET.SubElement(Podatak201, "Porez")
        Porez201.text = "%.2f" % (self._get_value(cr, uid, datas,'II1',2) or 0)
        Podatak202 = ET.SubElement(Tijelo, "Podatak202")
        Vrijednost202 = ET.SubElement(Podatak202, "Vrijednost")
        Vrijednost202.text = "%.2f" % (self._get_value(cr, uid, datas,'II2',1) or 0)
        Porez202 = ET.SubElement(Podatak202, "Porez")
        Porez202.text = "%.2f" % (self._get_value(cr, uid, datas,'II2',2) or 0)
        Podatak203 = ET.SubElement(Tijelo, "Podatak203")
        Vrijednost203 = ET.SubElement(Podatak203, "Vrijednost")
        Vrijednost203.text = "%.2f" % (self._get_value(cr, uid, datas,'II3',1) or 0)
        Porez203 = ET.SubElement(Podatak203, "Porez")
        Porez203.text = "%.2f" % (self._get_value(cr, uid, datas,'II3',2) or 0)
        Podatak204 = ET.SubElement(Tijelo, "Podatak204")
        Vrijednost204 = ET.SubElement(Podatak204, "Vrijednost")
        Vrijednost204.text = "%.2f" % (self._get_value(cr, uid, datas,'II4',1) or 0)
        Porez204 = ET.SubElement(Podatak204, "Porez")
        Porez204.text = "%.2f" % (self._get_value(cr, uid, datas,'II4',2) or 0)
        Podatak205 = ET.SubElement(Tijelo, "Podatak205")
        Vrijednost205 = ET.SubElement(Podatak205, "Vrijednost")
        Vrijednost205.text = "%.2f" % (self._get_value(cr, uid, datas,'II5',1) or 0)
        Porez205 = ET.SubElement(Podatak205, "Porez")
        Porez205.text = "%.2f" % (self._get_value(cr, uid, datas,'II5',2) or 0)        
        Podatak206 = ET.SubElement(Tijelo, "Podatak206")
        Vrijednost206 = ET.SubElement(Podatak206, "Vrijednost")
        Vrijednost206.text = "%.2f" % (self._get_value(cr, uid, datas,'II6',1) or 0)
        Porez206 = ET.SubElement(Podatak206, "Porez")
        Porez206.text = "%.2f" % (self._get_value(cr, uid, datas,'II6',2) or 0)
        Podatak207 = ET.SubElement(Tijelo, "Podatak207")
        Vrijednost207 = ET.SubElement(Podatak207, "Vrijednost")
        Vrijednost207.text = "%.2f" % (self._get_value(cr, uid, datas,'II7',1) or 0)
        Porez207 = ET.SubElement(Podatak207, "Porez")
        Porez207.text = "%.2f" % (self._get_value(cr, uid, datas,'II7',2) or 0)
        Podatak208 = ET.SubElement(Tijelo, "Podatak208")
        Vrijednost208 = ET.SubElement(Podatak208, "Vrijednost")
        Vrijednost208.text = "%.2f" % (self._get_value(cr, uid, datas,'II8',1) or 0)
        Porez208 = ET.SubElement(Podatak208, "Porez")
        Porez208.text = "%.2f" % (self._get_value(cr, uid, datas,'II8',2) or 0)
        Podatak209 = ET.SubElement(Tijelo, "Podatak209")
        Vrijednost209 = ET.SubElement(Podatak209, "Vrijednost")
        Vrijednost209.text = "%.2f" % (self._get_value(cr, uid, datas,'II9',1) or 0)
        Porez209 = ET.SubElement(Podatak209, "Porez")
        Porez209.text = "%.2f" % (self._get_value(cr, uid, datas,'II9',2) or 0)
        Podatak210 = ET.SubElement(Tijelo, "Podatak210")
        Vrijednost210 = ET.SubElement(Podatak210, "Vrijednost")
        Vrijednost210.text = "%.2f" % (self._get_value(cr, uid, datas,'II10',1) or 0)
        Porez210 = ET.SubElement(Podatak210, "Porez")
        Porez210.text = "%.2f" % (self._get_value(cr, uid, datas,'II10',2) or 0)
        Podatak211 = ET.SubElement(Tijelo, "Podatak211")
        Vrijednost211 = ET.SubElement(Podatak211, "Vrijednost")
        Vrijednost211.text = "%.2f" % (self._get_value(cr, uid, datas,'II11',1) or 0)
        Porez211 = ET.SubElement(Podatak211, "Porez")
        Porez211.text = "%.2f" % (self._get_value(cr, uid, datas,'II11',2) or 0)
        Podatak212 = ET.SubElement(Tijelo, "Podatak212")
        Vrijednost212 = ET.SubElement(Podatak212, "Vrijednost")
        Vrijednost212.text = "%.2f" % (self._get_value(cr, uid, datas,'II12',1) or 0)
        Porez212 = ET.SubElement(Podatak212, "Porez")
        Porez212.text = "%.2f" % (self._get_value(cr, uid, datas,'II12',2) or 0)   
        Podatak213 = ET.SubElement(Tijelo, "Podatak213")
        Vrijednost213 = ET.SubElement(Podatak213, "Vrijednost")
        Vrijednost213.text = "%.2f" % (self._get_value(cr, uid, datas,'II13',1) or 0)
        Porez213 = ET.SubElement(Podatak213, "Porez")
        Porez213.text = "%.2f" % (self._get_value(cr, uid, datas,'II13',2) or 0)        
        Podatak214 = ET.SubElement(Tijelo, "Podatak214")
        Vrijednost214 = ET.SubElement(Podatak214, "Vrijednost")
        Vrijednost214.text = "%.2f" % (self._get_value(cr, uid, datas,'II14',1) or 0)
        Porez214 = ET.SubElement(Podatak214, "Porez")
        Porez214.text = "%.2f" % (self._get_value(cr, uid, datas,'II14',2) or 0)
        Podatak215 = ET.SubElement(Tijelo, "Podatak215")
        Vrijednost215 = ET.SubElement(Podatak215, "Vrijednost")
        Vrijednost215.text = "%.2f" % (self._get_value(cr, uid, datas,'II15',1) or 0)
        Porez215 = ET.SubElement(Podatak215, "Porez")
        Porez215.text = "%.2f" % (self._get_value(cr, uid, datas,'II15',2) or 0)                                   
        Podatak300 = ET.SubElement(Tijelo, "Podatak300")
        Vrijednost300 = ET.SubElement(Podatak300, "Vrijednost")
        Vrijednost300.text = "%.2f" % (self._get_value(cr, uid, datas,'III',1) or 0)
        Porez300 = ET.SubElement(Podatak300, "Porez")
        Porez300.text = "%.2f" % (self._get_value(cr, uid, datas,'III',2) or 0)
        Podatak301 = ET.SubElement(Tijelo, "Podatak301")
        Vrijednost301 = ET.SubElement(Podatak301, "Vrijednost")
        Vrijednost301.text = "%.2f" % (self._get_value(cr, uid, datas,'III1',1) or 0)
        Porez301 = ET.SubElement(Podatak301, "Porez")
        Porez301.text = "%.2f" % (self._get_value(cr, uid, datas,'III1',2) or 0)
        Podatak302 = ET.SubElement(Tijelo, "Podatak302")
        Vrijednost302 = ET.SubElement(Podatak302, "Vrijednost")
        Vrijednost302.text = "%.2f" % (self._get_value(cr, uid, datas,'III2',1) or 0)
        Porez302 = ET.SubElement(Podatak302, "Porez")
        Porez302.text = "%.2f" % (self._get_value(cr, uid, datas,'III2',2) or 0)
        Podatak303 = ET.SubElement(Tijelo, "Podatak303")
        Vrijednost303 = ET.SubElement(Podatak303, "Vrijednost")
        Vrijednost303.text = "%.2f" % (self._get_value(cr, uid, datas,'III3',1) or 0)
        Porez303 = ET.SubElement(Podatak303, "Porez")
        Porez303.text = "%.2f" % (self._get_value(cr, uid, datas,'III3',2) or 0)
        Podatak304 = ET.SubElement(Tijelo, "Podatak304")
        Vrijednost304 = ET.SubElement(Podatak304, "Vrijednost")
        Vrijednost304.text = "%.2f" % (self._get_value(cr, uid, datas,'III4',1) or 0)
        Porez304 = ET.SubElement(Podatak304, "Porez")
        Porez304.text = "%.2f" % (self._get_value(cr, uid, datas,'III4',2) or 0)
        Podatak305 = ET.SubElement(Tijelo, "Podatak305")
        #PorezNeOdb305 = ET.SubElement(Podatak305, "PorezNeOdb")
        #PorezNeOdb305.text = "%.2f" % (self._get_value(cr, uid, datas,'III5',0) or 0)
        Vrijednost305 = ET.SubElement(Podatak305, "Vrijednost")
        Vrijednost305.text = "%.2f" % (self._get_value(cr, uid, datas,'III5',1) or 0)
        Porez305 = ET.SubElement(Podatak305, "Porez")
        Porez305.text = "%.2f" % (self._get_value(cr, uid, datas,'III5',2) or 0)
        Podatak306 = ET.SubElement(Tijelo, "Podatak306")
        #PorezNeOdb306 = ET.SubElement(Podatak306, "PorezNeOdb")
        #PorezNeOdb306.text = "%.2f" % (self._get_value(cr, uid, datas,'III6',0) or 0)
        Vrijednost306 = ET.SubElement(Podatak306, "Vrijednost")
        Vrijednost306.text = "%.2f" % (self._get_value(cr, uid, datas,'III6',1) or 0)
        Porez306 = ET.SubElement(Podatak306, "Porez")
        Porez306.text = "%.2f" % (self._get_value(cr, uid, datas,'III6',2) or 0)
        Podatak307 = ET.SubElement(Tijelo, "Podatak307")
        #PorezNeOdb307 = ET.SubElement(Podatak307, "PorezNeOdb")
        #PorezNeOdb307.text = "%.2f" % (self._get_value(cr, uid, datas,'III7',0) or 0)
        Vrijednost307 = ET.SubElement(Podatak307, "Vrijednost")
        Vrijednost307.text = "%.2f" % (self._get_value(cr, uid, datas,'III7',1) or 0)
        Porez307 = ET.SubElement(Podatak307, "Porez")
        Porez307.text = "%.2f" % (self._get_value(cr, uid, datas,'III7',2) or 0)
        Podatak308 = ET.SubElement(Tijelo, "Podatak308")
        #PorezNeOdb308 = ET.SubElement(Podatak308, "PorezNeOdb")
        #PorezNeOdb308.text = "%.2f" % (self._get_value(cr, uid, datas,'III8',0) or 0)
        Vrijednost308 = ET.SubElement(Podatak308, "Vrijednost")
        Vrijednost308.text = "%.2f" % (self._get_value(cr, uid, datas,'III8',1) or 0)
        Porez308 = ET.SubElement(Podatak308, "Porez")
        Porez308.text = "%.2f" % (self._get_value(cr, uid, datas,'III8',2) or 0)
        Podatak309 = ET.SubElement(Tijelo, "Podatak309")
        #PorezNeOdb309 = ET.SubElement(Podatak309, "PorezNeOdb")
        #PorezNeOdb309.text = "%.2f" % (self._get_value(cr, uid, datas,'III9',0) or 0)
        Vrijednost309 = ET.SubElement(Podatak309, "Vrijednost")
        Vrijednost309.text = "%.2f" % (self._get_value(cr, uid, datas,'III9',1) or 0)
        Porez309 = ET.SubElement(Podatak309, "Porez")
        Porez309.text = "%.2f" % (self._get_value(cr, uid, datas,'III9',2) or 0)
        Podatak310 = ET.SubElement(Tijelo, "Podatak310")
        #PorezNeOdb310 = ET.SubElement(Podatak310, "PorezNeOdb")
        #PorezNeOdb310.text = "%.2f" % (self._get_value(cr, uid, datas,'III10',0) or 0)
        Vrijednost310 = ET.SubElement(Podatak310, "Vrijednost")
        Vrijednost310.text = "%.2f" % (self._get_value(cr, uid, datas,'III10',1) or 0)
        Porez310 = ET.SubElement(Podatak310, "Porez")
        Porez310.text = "%.2f" % (self._get_value(cr, uid, datas,'III10',2) or 0)
        Podatak311 = ET.SubElement(Tijelo, "Podatak311")
        #PorezNeOdb311 = ET.SubElement(Podatak311, "PorezNeOdb")
        #PorezNeOdb311.text = "%.2f" % (self._get_value(cr, uid, datas,'III11',0) or 0)
        Vrijednost311 = ET.SubElement(Podatak311, "Vrijednost")
        Vrijednost311.text = "%.2f" % (self._get_value(cr, uid, datas,'III11',1) or 0)
        Porez311 = ET.SubElement(Podatak311, "Porez")
        Porez311.text = "%.2f" % (self._get_value(cr, uid, datas,'III11',2) or 0) 
        Podatak312 = ET.SubElement(Tijelo, "Podatak312")
        #PorezNeOdb312 = ET.SubElement(Podatak312, "PorezNeOdb")
        #PorezNeOdb312.text = "%.2f" % (self._get_value(cr, uid, datas,'III12',0) or 0)
        Vrijednost312 = ET.SubElement(Podatak312, "Vrijednost")
        Vrijednost312.text = "%.2f" % (self._get_value(cr, uid, datas,'III12',1) or 0)
        Porez312 = ET.SubElement(Podatak312, "Porez")
        Porez312.text = "%.2f" % (self._get_value(cr, uid, datas,'III13',2) or 0)
        Podatak313 = ET.SubElement(Tijelo, "Podatak313")
        #PorezNeOdb313 = ET.SubElement(Podatak313, "PorezNeOdb")
        #PorezNeOdb313.text = "%.2f" % (self._get_value(cr, uid, datas,'III13',0) or 0)
        Vrijednost313 = ET.SubElement(Podatak313, "Vrijednost")
        Vrijednost313.text = "%.2f" % (self._get_value(cr, uid, datas,'III13',1) or 0)
        Porez313 = ET.SubElement(Podatak313, "Porez")
        Porez313.text = "%.2f" % (self._get_value(cr, uid, datas,'III13',2) or 0)
        Podatak314 = ET.SubElement(Tijelo, "Podatak314")
        #PorezNeOdb314 = ET.SubElement(Podatak314, "PorezNeOdb")
        #PorezNeOdb314.text = "%.2f" % (self._get_value(cr, uid, datas,'III14',0) or 0)
        Vrijednost314 = ET.SubElement(Podatak314, "Vrijednost")
        Vrijednost314.text = "%.2f" % (self._get_value(cr, uid, datas,'III14',1) or 0)
        Porez314 = ET.SubElement(Podatak314, "Porez")
        Porez314.text = "%.2f" % (self._get_value(cr, uid, datas,'III14',2) or 0)
        #Podatak315 = ET.SubElement(Tijelo, "Podatak315")
        #PorezNeOdb315 = ET.SubElement(Podatak315, "PorezNeOdb")
        #PorezNeOdb315.text = "%.2f" % (self._get_value(cr, uid, datas,'III15',0) or 0)
        #Vrijednost315 = ET.SubElement(Podatak315, "Vrijednost")
        #Vrijednost315.text = "%.2f" % (self._get_value(cr, uid, datas,'III15',1) or 0)
        #Porez315 = ET.SubElement(Podatak315, "Porez")
        #Porez315.text = "%.2f" % (self._get_value(cr, uid, datas,'III15',2) or 0)
        Podatak315 = ET.SubElement(Tijelo, "Podatak315")
        Podatak315.text = "%.2f" % (self._get_value(cr, uid, datas,'III15',2) or 0)                                                                          
        Podatak400 = ET.SubElement(Tijelo, "Podatak400")
        Podatak400.text = "%.2f" % (self._get_value(cr, uid, datas,'IV',2) or 0)
        Podatak500 = ET.SubElement(Tijelo, "Podatak500")
        Podatak500.text = "%.2f" % (self._get_value(cr, uid, datas,'V',2) or 0)
        # removing from 01.01.2023
        # Podatak600 = ET.SubElement(Tijelo, "Podatak600")
        # Podatak600.text = "%.2f" % (self._get_value(cr, uid, datas,'VI',2) or 0)
        # Podatak700 = ET.SubElement(Tijelo, "Podatak700")
        # Podatak700.text = "%.2f" % (self._get_value(cr, uid, datas,'VII',1) or 0)
        #new addition VIII
        #Podatak800 ne postoji u xsd shemi
        #Podatak800 = ET.SubElement(Tijelo, "Podatak800")
        #Podatak800.text = "%.2f" % (self._get_value(cr, uid, datas,'VIII',1) or 0)
        Podatak610 = ET.SubElement(Tijelo, "Podatak610")
        Podatak610.text = "%.2f" % (self._get_value(cr, uid, datas,'VI1',1) or 0)
        Podatak611 = ET.SubElement(Tijelo, "Podatak611")
        Podatak611.text = "%.2f" % (self._get_value(cr, uid, datas,'VI11',1) or 0)
        Podatak612 = ET.SubElement(Tijelo, "Podatak612")
        Podatak612.text = "%.2f" % (self._get_value(cr, uid, datas,'VI12',1) or 0)
        Podatak613 = ET.SubElement(Tijelo, "Podatak613")
        Podatak613.text = "%.2f" % (self._get_value(cr, uid, datas,'VI13',1) or 0)
        Podatak614 = ET.SubElement(Tijelo, "Podatak614")
        Podatak614.text = "%.2f" % (self._get_value(cr, uid, datas,'VI14',1) or 0)
        Podatak615 = ET.SubElement(Tijelo, "Podatak615")
        Podatak615.text = "%.2f" % (self._get_value(cr, uid, datas,'VI15',1) or 0)
        Podatak620 = ET.SubElement(Tijelo, "Podatak620")
        Podatak620.text = "%.2f" % (self._get_value(cr, uid, datas,'VI2',1) or 0)
        Podatak630 = ET.SubElement(Tijelo, "Podatak630")
        Podatak630.text = "%.2f" % (self._get_value(cr, uid, datas,'VI3',1) or 0)
        Podatak640 = ET.SubElement(Tijelo, "Podatak640")
        Podatak640.text = "%.2f" % (self._get_value(cr, uid, datas,'VI4',1) or 0)
        Podatak650 = ET.SubElement(Tijelo, "Podatak650")
        Podatak650.text = "%.2f" % (self._get_value(cr, uid, datas,'VI5',1) or 0)
        Podatak660 = ET.SubElement(Tijelo, "Podatak660")
        Podatak660.text = "%.2f" % (self._get_value(cr, uid, datas,'VI6',1) or 0)

        msg = ET.tostring(ObrazacPDV)
        msg = '<?xml version="1.0" encoding="windows-1250" standalone="yes"?>' + msg
        data64 = base64.encodestring(msg.encode('windows-1250'))
        self.write(cr, uid, ids, {'state': 'get', 'data': data64, 'name': 'pdv_export.xml'},
                           context=context)
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

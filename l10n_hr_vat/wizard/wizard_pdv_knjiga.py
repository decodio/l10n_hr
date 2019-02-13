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

import base64
import os
import uuid
from lxml import etree, objectify
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning


class pdv_knjiga(orm.TransientModel):
    _name = 'pdv.knjiga'
    _inherit = 'account.common.report'

    _columns = {
        'chart_tax_id': fields.many2one('account.tax.code', 'Chart of Tax',
                          help='Select Charts of Taxes', required=True,
                          domain=[('parent_id', '=', False)]),
        'knjiga_id': fields.many2one('l10n_hr_pdv.knjiga', 'Porezna knjiga', 
                      help='Odaberite poreznu knjigu za ispis', required=True),
        'date_start': fields.date('Od datuma'),
        'date_stop': fields.date('Do datuma'),
        'journal_ids': fields.many2many('account.journal', 'pdv_knjiga_journal_rel', 'pdv_knjiga_id', 'journal_id',
                                       'Journals'),
        'data': fields.binary('File', readonly=True),
        'name': fields.char('Filename', size=128, readonly=True),
        'state': fields.selection((('choose', 'choose'), ('get', 'get'),)),
    }

    def _get_tax(self, cr, uid, context=None):
        taxes = self.pool.get('account.tax.code').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return taxes and taxes[0] or False

    _defaults = {
        'chart_tax_id': _get_tax,
        'journal_ids': [],
        'state': 'choose',
    }


    # def export_vat(self, cr, uid, ids, context=None):
    #     """
    #     Kopiram logiku iz parsera bez potezanja parsera
    #     """
    #     if context is None:
    #         context = {}

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        if not datas['form'].get('journal_ids', False):
            sql = """SELECT id FROM account_journal"""
            cr.execute(sql)
            datas['form']['journal_ids'] = [a for (a,) in cr.fetchall()]

        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        if datas['form']['knjiga_id']:
            knjiga_type = self.pool.get('l10n_hr_pdv.knjiga').browse(cr, uid, datas['form']['knjiga_id']).type
        else:
            raise orm.except_orm(_('Knjiga nije upisana!'),
                                 _("Knjiga je obavezan podatak kod ovog ispisa!"))

#        if (datas['form']['period_from'] and not datas['form']['period_to']) or \
#            (not datas['form']['period_from'] and datas['form']['period_to']):
#            raise orm.except_orm(_('Krivi periodi!'),_("Potrebno je upisati oba perioda za ispis po periodima!"))
#
#        if (datas['form']['date_start'] and not datas['form']['date_stop']) or \
#            (not datas['form']['date_start'] and datas['form']['date_stop']):
#            raise orm.except_orm(_('Krivo razdoblje!'),_("Potrebno je upisati oba datuma za ispis po datumima!"))

        report_name = None
        if knjiga_type == 'ira':
            # report_name = 'knjiga.ira'
            # report_name = 'knjiga.ira.eu.2014'
            report_name = 'knjiga_ira_ods'
        elif knjiga_type in ('ura', 'ura_uvoz'):
            # report_name = 'knjiga.ura'
            # report_name = 'knjiga.ura.eu.2014'
            report_name = 'knjiga_ura_ods'
        elif knjiga_type in ('ura_tu', 'ura_st', 'ura_nerezident'):
            report_name = 'knjiga_ura_prijenos'
        if context.get('xml'):
            return self.create_xml(cr, uid, ids, context, datas, report_name)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
        }

    def create_xml(self, cr, uid, ids, context=None, datas=False, report_name=False):
        form = self.browse(cr, uid, ids)[0]
        if not form.company_id.podrucje_djelatnosti:
            raise Warning(_('Warning'),
                          _('Please set company data : Area of activity'))
        if form.knjiga_id.type != 'ura':
            raise Warning(_('Warning'),
                          _('Only URA is for XML export!'))

        try:
            from ..report import knjiga_ura as URA
            from ..report.vat_book_report_common import get_vat_book_report_common
            from . import xml_common
        except:
            raise Warning(_('Warning'),
                          _('Important librarys missing!'))

        def decimal_num(num):
            # JER ETO u podacim mi dodje round na 3 znamenke...
            num = str(round(num, 2))
            dec = num.split('.')[1]
            if dec == '0':
                num += '0'
            elif len(dec) > 2:
                num = num[:-1]
            return num


        parser = URA.Parser(cr, uid, report_name, context=context)
        parser.set_context(objects=[], data=datas, ids=[])
        parser_ctx = parser.localcontext

        lines = parser_ctx['get_lines'](datas)
        total = parser_ctx['get_totals']()
        total = total and total[0] or False




        metadata, identifier = xml_common.create_xml_metadata(self, {
            'naslov': u'Knjiga primljenih (ulaznih) računa',
            'autor': ' '.join((
                form.company_id.responsible_fname,
                form.company_id.responsible_lname)),
            'format': 'text/xml',
            'jezik': 'hr-HR',
            'uskladjenost': 'ObrazacURA-v1-0',
            'tip': u'Elektronički obrazac',
            'adresant': 'Ministarstvo Financija, Porezna uprava, Zagreb'
        })

        EM = objectify.ElementMaker(annotate=False)

        date_start = form.date_start and form.date_start or \
                     form.period_from.date_start
        date_stop = form.date_stop and form.date_stop or \
                     form.period_to.date_stop
        zaglavlje = EM.Zaglavlje(
                EM.Razdoblje(
                    EM.DatumOd(date_start),
                    EM.DatumDo(date_stop)),
                EM.Obveznik(
                    EM.OIB(form.company_id.vat[2:]),
                    EM.Naziv(form.company_id.name),
                    EM.Adresa(
                        EM.Mjesto(form.company_id.city),
                        EM.Ulica(form.company_id.ulica),
                        EM.Broj(form.company_id.kbr),
                        EM.DodatakKucnomBroju(form.company_id.kbr_dodatak and \
                                              form.company_id.kbr_dodatak or '')
                        ),
                    EM.PodrucjeDjelatnosti(form.company_id.podrucje_djelatnosti),
                    EM.SifraDjelatnosti(form.company_id.l10n_hr_base_nkd_id.code),),
                EM.ObracunSastavio(
                    EM.Ime(form.company_id.responsible_fname),
                    EM.Prezime(form.company_id.responsible_lname),
                    ),
                )
        racuni = []
        errors = []
        for line in lines:
            partner = line['partner_name'].split(', ')
            partner_r4 = partner[0]
            partner_r5 = ', '.join((partner[1], partner[2]))
            if line['partner_oib'] == '':
                errors.append(line)
                continue
            racuni.append(EM.R(
                EM.R1(line['rbr'].replace('.', '')),
                EM.R2(line['invoice_number']),
                EM.R3(line['invoice_date']),
                EM.R4(partner_r4),
                EM.R5(partner_r5),
                EM.R6(line['vat_type']),
                EM.R7(line['partner_oib'].lstrip().rstrip()),
                EM.R8(decimal_num(line['stupac6'])),
                EM.R9(decimal_num(line['stupac7'])),
                EM.R10(decimal_num(line['stupac8'])),
                EM.R11(decimal_num(line['stupac9'])),
                EM.R12(decimal_num(line['stupac10'])),
                EM.R13(decimal_num(line['stupac11'])),
                EM.R14(decimal_num(line['stupac12'])),
                EM.R15(decimal_num(line['stupac13'])),
                EM.R16(decimal_num(line['stupac14'])),
                EM.R17(decimal_num(line['stupac15'])),
                EM.R18(decimal_num(line['stupac16'])),
            ))

        Racuni = EM.Racuni(EM.R)
        Racuni.R = racuni
        Ukupno = EM.Ukupno(
            EM.U8(decimal_num(total['stupac6'])),
            EM.U9(decimal_num(total['stupac7'])),
            EM.U10(decimal_num(total['stupac8'])),
            EM.U11(decimal_num(total['stupac9'])),
            EM.U12(decimal_num(total['stupac10'])),
            EM.U13(decimal_num(total['stupac11'])),
            EM.U14(decimal_num(total['stupac12'])),
            EM.U15(decimal_num(total['stupac13'])),
            EM.U16(decimal_num(total['stupac14'])),
            EM.U17(decimal_num(total['stupac15'])),
            EM.U18(decimal_num(total['stupac16'])),
        )
        tijelo = EM.Tijelo(Racuni, Ukupno)
        PDV = objectify.ElementMaker(
            namespace='http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacURA/v1-0',
        )
        obrazac = PDV.ObrazacURA(metadata, zaglavlje, tijelo, verzijaSheme='1.0')
        pdv_xml = xml_common.etree_tostring(self, obrazac)
        pdv_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pdv_xml
        # print pdv_xml

        # TODO: validate xml
        # xml_common.validate_xml
        file_path = os.path.dirname(os.path.abspath(__file__))
        xml = {
            'path': file_path,
            'xsd_path': 'shema/URA',
            'xsd_name': 'ObrazacURA-v1-0.xsd',
            'xml': pdv_xml
        }
        valid = xml_common.validate_xml(self, xml)

        data64 = base64.encodestring(pdv_xml)
        xml_name = 'PDV_Obrazac_%s_%s.XML' % (date_start.replace('-', ''),
                                              date_stop.replace('-',''))
        form.write({'state': 'get',
                    'data': data64,
                    'name': xml_name
                    })
        if errors:
            msg= "Errors\n"
            for e in errors:
                msg += "%s - %s\n" % (e['rbr'], e['partner_name'])
            #raise Warning('Nedostaje OIB', msg)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pdv.knjiga',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'views': [(False, 'form')],
            'target': 'new',
        }



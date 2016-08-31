# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Decodio
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

from openerp import models, fields, api, _
from datetime import datetime
from lxml import objectify
import os
import base64
import xml_common as rc
import time
from openerp.modules.module import get_module_resource
#from openerp.exceptions import except_orm, ValidationError, Warning, RedirectWarning


class OpzStat(models.Model):
    _name = "opz.stat"
    _description ="OPZ STAT report"

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    name = fields.Char('Name', required=True, default = '/')
    opz_stat_line = fields.One2many('opz.stat.line', 'opz_id', string='OPZ STAT Lines',
                                    readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                             required=True, readonly=True, states={'draft': [('readonly', False)]},
                             default=lambda self: self.env['res.company']._company_default_get('opz.stat'))
    state = fields.Selection([('draft','Draft'),
                              ('confirmed', 'Confirmed'),
                              ('done','Done'),],'State', required=True, select=True, readonly=True, default='draft')
    xml_file =  fields.Binary('XML File', readonly=True)
    xml_filename = fields.Char('XML File Name', readonly=True)


    def _auto_init(self, cr, context=None):
        res = super(OpzStat, self)._auto_init(cr, context=context)
        f = get_module_resource('l10n_hr_opz_stat', 'sql', 'oe_opz_stat.sql')
        sql = open(f).read()
        cr.execute(sql)

        return res

    @api.multi
    def compute(self):
        sql = """
             SELECT DISTINCT 1
             FROM oe_opz_stat(
                     _date_to      := '%(date_to)s'
                    ,_opz_id    := %(opz_id)s
                         )

           """ % {'date_to': self.date_to,
                  'opz_id': self.id
                  }


        self._cr.execute(sql)
        return False

    @api.multi
    def set_to_confirmed(self):
        self.ensure_one()
        self.state = 'confirmed'

    @api.multi
    def set_to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def print_report(self):
        pass

    @api.multi
    def export_xml(self):
        self.ensure_one()
        kupac_line_no = 1
        period = {'date_start': self.date_from,
                    'date_stop': self.date_to
                  }
        #last_due_date = (
        #datetime.strptime(self.date_to, '%Y-%m-%d') + relativedelta(months=1)).strftime('%Y-%m-%d')

        Tijelo = objectify.Element("Tijelo")
        Kupci = objectify.SubElement(Tijelo, "Kupci")


        UkupanIznosRacunaObrasca = 0.0
        UkupanIznosPdvObrasca = 0.0
        UkupanIznosRacunaSPdvObrasca = 0.0
        UkupniPlaceniIznosRacunaObrasca = 0.0
        NeplaceniIznosRacunaObrasca = 0.0
        OPZUkupanIznosRacunaSPdv = 0.0
        OPZUkupanIznosPdv = 0.0

        partners = self._get_partners()
        for partner in partners:
            lines = self._get_partner_lines(partner['partner_id'])
            Kupac = objectify.SubElement(Kupci, "Kupac")
            Kupac.K1 = kupac_line_no # Redni broj
            Kupac.K2 = partner['partner_vat_type'] # Oznaka poreznog broja 1=OIB, 2=PDV ID, 3=ostali porezni brojevi
            Kupac.K3 = partner['partner_vat_number'] # porezni broj ovisno o vrijednosti K2
            Kupac.K4 = partner['partner_name'] # Naziv kupca
            Kupac.K5 = partner['partner_amount'] # Iznos računa ukupno
            Kupac.K6 = partner['partner_amount_tax'] # Iznos PDV ukupno
            Kupac.K7 = partner['partner_amount_total'] # Iznos računa s PDV ukupno
            Kupac.K8 = partner['partner_paid'] # Plaćeni iznos ukupno
            Kupac.K9 = partner['partner_unpaid']  # Neplaćeni iznos ukupno

            Racuni = objectify.SubElement(Kupac, "Racuni")
            line_no = 1
            for line in lines:
                Racun = objectify.SubElement(Racuni, "Racun")
                Racun.R1 = line_no # Redni broj
                Racun.R2 = line['invoice_number'] # Broj (naziv) računa
                Racun.R3 = line['invoice_date'] # Datum računa
                Racun.R4 = line['due_date'] # Datum dospjeća
                Racun.R5 = line['overdue_days'] # broj dana kašnjenja
                Racun.R6 = line['amount'] # iznos računa bez PDV-a
                Racun.R7 = line['amount_tax'] # iznos PDV-a
                Racun.R8 = line['amount_total'] # iznos računa s PDV-om
                Racun.R9 = line['paid'] # plaćeni iznos
                Racun.R10 = line['unpaid'] # otvoreni iznos
                line_no += 1

                UkupanIznosRacunaObrasca += line['amount']
                UkupanIznosPdvObrasca += line['amount_tax']
                UkupanIznosRacunaSPdvObrasca += line['amount_total']
                UkupniPlaceniIznosRacunaObrasca += line['paid']
                NeplaceniIznosRacunaObrasca += line['unpaid']
                OPZUkupanIznosRacunaSPdv = 0.0
                OPZUkupanIznosPdv = 0.0

            kupac_line_no += 1

        Tijelo.UkupanIznosRacunaObrasca = UkupanIznosRacunaObrasca
        Tijelo.UkupanIznosPdvObrasca = UkupanIznosPdvObrasca
        Tijelo.UkupanIznosRacunaSPdvObrasca = UkupanIznosRacunaSPdvObrasca
        Tijelo.UkupniPlaceniIznosRacunaObrasca = UkupniPlaceniIznosRacunaObrasca
        Tijelo.NeplaceniIznosRacunaObrasca = NeplaceniIznosRacunaObrasca
        Tijelo.OPZUkupanIznosRacunaSPdv = OPZUkupanIznosRacunaSPdv
        Tijelo.OPZUkupanIznosPdv = OPZUkupanIznosPdv

        tijelo = Tijelo

        author, company, metadata = rc.get_common_data(self,self._cr, self._uid, self)

        metadata['naslov'] = u'Obrazac OPZ'
        metadata['uskladjenost'] = u'ObrazacOPZ-v1-0'

        xml_metadata, uuid = rc.create_xml_metadata(self, metadata)
        xml_header = rc.create_xml_header(self, period, company, author)

        OBRAZACOPZ = objectify.ElementMaker(annotate=False, namespace='http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacOPZ/v1-0')
        obrazacopz_stat = OBRAZACOPZ.ObrazacOPZ(xml_metadata, xml_header, tijelo, verzijaSheme="1.0")

        xml = {'xml': rc.etree_tostring(self, obrazacopz_stat),
               'xsd_path': 'schema/opz_stat_xml_v1.0',
               'xsd_name': 'ObrazacOPZ-v1-0.xsd'}
        xml['path'] = os.path.dirname(os.path.abspath(__file__))
        validate = rc.validate_xml(self, xml)
        #validate = True
        if validate:
            filename = 'opz_stat_' + time.strftime('%Y-%m-%d') + '.xml'
            data64 = base64.encodestring(xml['xml'].encode('windows-1250'))
            self.write({'xml_file': data64, 'xml_filename': filename})

        self.state = 'done'
        return False

    @api.multi
    def _get_partners(self):
        partners = []
        sql = """
                SELECT DISTINCT opzl.partner_id
                                ,CASE WHEN opzl.partner_vat_type = 'vat' THEN 1
                                      WHEN opzl.partner_vat_type = 'vatid' THEN 2
                                      WHEN opzl.partner_vat_type = 'other' THEN 3
                                END AS partner_vat_type
                                ,opzl.partner_vat_number
                                ,opzl.partner_name
                                ,SUM(opzl.amount) AS partner_amount
                                ,SUM(opzl.amount_tax) AS partner_amount_tax
                                ,SUM(opzl.amount_total) AS partner_amount_total
                                ,SUM(opzl.paid) AS partner_paid
                                ,SUM(opzl.unpaid) AS partner_unpaid
                 FROM opz_stat_line opzl
                WHERE opzl.opz_id = %(opz_id)s
               GROUP BY opzl.partner_id, opzl.partner_vat_type, opzl.partner_vat_number, opzl.partner_name
              """ % {'opz_id': self.id,
                     }

        self._cr.execute(sql)
        partners = self._cr.dictfetchall()
        return partners

    @api.multi
    def _get_partner_lines(self, partner_id):
        lines = []
        sql = """
                SELECT opzl.invoice_number
                      ,opzl.invoice_date
                      ,opzl.due_date
                      ,opzl.overdue_days
                      ,opzl.amount
                      ,opzl.amount_tax
                      ,opzl.amount_total
                      ,opzl.paid
                      ,opzl.unpaid
                 FROM opz_stat_line opzl
                WHERE opzl.opz_id = %(opz_id)s
                  AND opzl.partner_id = %(partner_id)s
              """ % {'opz_id': self.id,
                     'partner_id': partner_id
                     }

        self._cr.execute(sql)
        lines = self._cr.dictfetchall()
        return lines

class OpzStatLine(models.Model):
    _name = "opz.stat.line"
    _description ="OPZ STAT report lines"
    _order = 'invoice_date'

    opz_id = fields.Many2one('opz.stat', 'OPZ STAT', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Partner', domain="[('customer', '=', True)]")
    partner_name = fields.Char('Partner Name', required=True)
    partner_vat_type = fields.Selection([('vat', '1'),
                                         ('vatid', '2'),
                                         ('other', '3'), ],
                        'VAT Type', required=True, select=True, default = 'vat')
    partner_vat_number = fields.Char('VAT Number', required=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice', copy=True,
                                domain="[('partner_id', '=', partner_id),"
                                       " ('account_id.type', '=', 'receivable')]")
    invoice_number = fields.Char('Invoice Number', required=True)
    invoice_date = fields.Date('Invoice Date', required=True)
    due_date = fields.Date('Due Date', required=True)
    amount = fields.Float('Amount', required=True, defaults=0.0)
    amount_tax = fields.Float('Amount Tax', required=True, defaults=0.0)
    amount_total = fields.Float('Amount with Tax', required=True, defaults=0.0)
    paid = fields.Float('Paid Amount', required=True, defaults=0.0)
    unpaid = fields.Float('Unpaid Amount', required=True, defaults=0.0)
    overdue_days = fields.Integer('Overdue Days', required=True, defaults=0)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            if self.partner_vat_type == 'vat':
                self.partner_vat_number = self.partner_id.vat and self.partner_id.vat[2:]
            else:
                self.partner_vat_number = self.partner_id.vat
        else:
            self.partner_name = False
            self.partner_vat_number = False

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            overdue =  datetime.strptime(self.opz_id.date_to, '%Y-%m-%d').date() \
                     - datetime.strptime(self.invoice_id.date_due, '%Y-%m-%d').date()
            self.invoice_number = self.invoice_id.number
            self.invoice_date = self.invoice_id.date_invoice
            self.due_date = self.invoice_id.date_due
            self.amount = self.invoice_id.amount_untaxed
            self.amount_tax = self.invoice_id.amount_tax
            self.amount_total = self.invoice_id.amount_total
            self.overdue_days = overdue.days
            #TODO residual must be computed
            self.paid = self.invoice_id.amount_total - self.invoice_id.residual
            self.unpaid = self.invoice_id.residual
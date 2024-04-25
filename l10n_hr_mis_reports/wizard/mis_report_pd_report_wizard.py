from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from io import BytesIO
from itertools import zip_longest
import openpyxl
import base64
import pytz
import uuid
from lxml import etree
FIRST_SHEET_PERIOD_FROM_CELL = 'E11'
FIRST_SHEET_PERIOD_TO_CELL = 'G11'
SHEET_AMOUNT_CELL = 'G'
XML_EXPORT_DATA_NODES_ENUM = [range(1, 35), range(341, 343), range(35, 50), range(491, 495), range(50, 51),
                               range(501, 505), range(51, 60)]
XML_EXPORT_YEAR_NODES_ENUM = range(10, -1, -1)
XML_EXPORT_YEAR_NODES_REFS = ('Godina', 'PodatakPG', 'PodatakDO', 'PodatakGPPP', 'PodatakGP')


class MisReportPDReportWizard(models.TransientModel):
    _name = 'mis.report.pd.report.wizard'
    _description = 'PD Report Wizard'

    mis_report_id = fields.Many2one('mis.report.instance', string='PD Report', required=1,
                                    default=lambda self: self._get_default_mis_report_id())
    out_xlsx = fields.Binary('Excel file', readonly=True)
    name = fields.Char(string='File name', readonly=True)
    out_xml = fields.Binary('XML file', readonly=True)
    xml_name = fields.Char(string='XML  File-name', readonly=True)

    def _get_default_mis_report_id(self):
        return self.env['mis.report.instance'].search([('l10n_hr_report_type', '=', 'pd')])

    @api.multi
    def _update_first_sheet_company_data(self, mis_report, sheet):
        sheet[FIRST_SHEET_PERIOD_FROM_CELL] = mis_report.period_ids[0].manual_date_from
        sheet[FIRST_SHEET_PERIOD_TO_CELL] = mis_report.period_ids[0].manual_date_to

    @api.multi
    def _inject_mis_report_data(self, mis_report, sheet_no, sheet):
        kpi_report_position_data = dict(
            mis_report.report_id.kpi_ids.
            filtered(lambda x: x.report_sheet == sheet_no and x.report_position).
            mapped(lambda l: (l.name, l.report_position)))
        kpi_data = mis_report.compute()
        data = dict()
        for line in kpi_data.get('body'):
            if kpi_report_position_data.get(line['row_id']):
                data[kpi_report_position_data[line['row_id']]] = line['cells'] and line['cells'][0]['val'] or 0.0
        # write MIS generated data in Sheet
        for index, value in data.items():
            cell_index = '%s%s' % (SHEET_AMOUNT_CELL, index)
            sheet[cell_index] = float_round(value, precision_digits=2)

    @api.multi
    def _create_xlsx_report(self, company):
        infile = BytesIO()
        infile.write(base64.decodebytes(company.pd_report_xlsx_template_file))
        infile.seek(0)
        xlsx_template = openpyxl.load_workbook(infile)
        # Company Data, first sheet
        self._update_first_sheet_company_data(self.mis_report_id, xlsx_template.worksheets[0])
        # MIS Report Mapping
        # Sheet 2
        self._inject_mis_report_data(self.mis_report_id, 2, xlsx_template.worksheets[1])
        # Sheet 3
        self._inject_mis_report_data(self.mis_report_id, 3, xlsx_template.worksheets[2])
        # Sheet 4
        self._inject_mis_report_data(self.mis_report_id, 4, xlsx_template.worksheets[3])
        buffer = BytesIO()
        xlsx_template.save(buffer)
        buffer.seek(0)
        out = base64.encodebytes(buffer.read())
        buffer.close()
        return out

    @api.multi
    def _generate_xml_data(self):
        form = "ObrazacPD"
        verzija_sheme = "7.0"
        xmlns = "http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacPD/v7-0"
        uskladjenost = "ObrazacPD-v7-0"
        title = "Prijava poreza na dobit"
        curr_user = self.env.user
        curr_year = fields.Date.today().year
        mis_report = self.mis_report_id
        report_company = mis_report.company_id
        today = fields.Datetime.now()
        timezone = "Europe/Zagreb"
        if curr_user.tz:
            timezone = curr_user.tz
        tz = pytz.timezone(timezone)
        utc = pytz.timezone("UTC")
        today = utc.localize(today).astimezone(tz)
        # Form
        Obrazac = etree.Element(form)
        Obrazac.set("verzijaSheme", verzija_sheme)
        Obrazac.set("xmlns", xmlns)
        # Metadata
        Metapodaci = etree.SubElement(Obrazac, "Metapodaci")
        Metapodaci.set("xmlns", "http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0")
        Naslov = etree.SubElement(Metapodaci, "Naslov")
        Naslov.text = title
        Naslov.set("dc", "http://purl.org/dc/elements/1.1/title")
        Autor = etree.SubElement(Metapodaci, "Autor")
        Autor.text = curr_user.name or ''
        Autor.set("dc", "http://purl.org/dc/elements/1.1/creator")
        Datum = etree.SubElement(Metapodaci, "Datum")
        Datum.text = today.strftime("%Y-%m-%dT%H:%M:%S")
        Datum.set("dc", "http://purl.org/dc/elements/1.1/date")
        Format = etree.SubElement(Metapodaci, "Format")
        Format.text = "text/xml"
        Format.set("dc", "http://purl.org/dc/elements/1.1/format")
        Jezik = etree.SubElement(Metapodaci, "Jezik")
        Jezik.text = "hr-HR"
        Jezik.set("dc", "http://purl.org/dc/elements/1.1/language")
        Identifikator = etree.SubElement(Metapodaci, "Identifikator")
        Identifikator.text = str(uuid.uuid4())
        Identifikator.set("dc", "http://purl.org/dc/elements/1.1/identifier")
        Uskladjenost = etree.SubElement(Metapodaci, "Uskladjenost")
        Uskladjenost.text = uskladjenost
        Uskladjenost.set("dc", "http://purl.org/dc/terms/conformsTo")
        Tip = etree.SubElement(Metapodaci, "Tip")
        Tip.text = u"Elektronički obrazac"
        Tip.set("dc", "http://purl.org/dc/elements/1.1/type")
        Adresant = etree.SubElement(Metapodaci, "Adresant")
        Adresant.text = "Ministarstvo Financija, Porezna uprava, Zagreb"
        # Header
        Zaglavlje = etree.SubElement(Obrazac, "Zaglavlje")
        Razdoblje = etree.SubElement(Zaglavlje, "Razdoblje")
        DatumOd = etree.SubElement(Razdoblje, "DatumOd")
        DatumOd.text = fields.Date.to_string(mis_report.date_from)
        DatumDo = etree.SubElement(Razdoblje, "DatumDo")
        DatumDo.text = fields.Date.to_string(mis_report.date_to)
        Obveznik = etree.SubElement(Zaglavlje, "Obveznik")
        Naziv = etree.SubElement(Obveznik, "Naziv")
        Naziv.text = report_company.name
        OIB = etree.SubElement(Obveznik, "OIB")
        OIB.text = report_company.vat[2:]
        SifraDjelatnosti = etree.SubElement(Obveznik, "SifraDjelatnosti")
        SifraDjelatnosti.text = report_company.nkd or ''
        Adresa = etree.SubElement(Obveznik, "Adresa")
        Mjesto = etree.SubElement(Adresa, "Mjesto")
        Mjesto.text = report_company.city
        full_addr = report_company.street
        part_addr = full_addr.split(" ")
        num = part_addr[len(part_addr) - 1]
        addr = ""
        for index in range(len(part_addr) - 1):
            addr += part_addr[index] + " "
        if len(addr) > 0:
            addr = addr[:-1]
        Ulica = etree.SubElement(Adresa, "Ulica")
        Ulica.text = addr
        Broj = etree.SubElement(Adresa, "Broj")
        Broj.text = num
        ime, prezime = curr_user.firstname, curr_user.lastname
        ObracunSastavio = etree.SubElement(Zaglavlje, "ObracunSastavio")
        Ime = etree.SubElement(ObracunSastavio, "Ime")
        Ime.text = ime or ''
        Prezime = etree.SubElement(ObracunSastavio, "Prezime")
        Prezime.text = prezime or ''
        # Body
        Tijelo = etree.SubElement(Obrazac, "Tijelo")
        data = [y for x in XML_EXPORT_DATA_NODES_ENUM for y in x]
        kpi_data = mis_report.compute()
        for key, line in zip_longest(data, kpi_data.get('body')):
            value = line and line.get('cells') and line['cells'][0]['val'] or 0.0
            node_ref = "Podatak%s" % key
            node = etree.SubElement(Tijelo, node_ref)
            node.text = "%.2f" % value
        for increment, year in zip_longest(XML_EXPORT_YEAR_NODES_ENUM, range(curr_year - 10, curr_year + 1)):
            key = "%.2d" % increment
            for node_ref in XML_EXPORT_YEAR_NODES_REFS:
                node_name = "%s%s" %(node_ref, key)
                node = etree.SubElement(Tijelo, node_name)
                if node_name.startswith("Godina"):
                    node.text = "%.2d" % year
                else:
                    node.text = "%.2f" % 0.0
        msg = etree.tostring(Obrazac, encoding='utf-8', pretty_print=True)
        msg = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>' + msg.decode('utf-8')
        data64 = base64.b64encode(bytes(msg, 'utf-8'))
        return data64

    @api.multi
    def create_report(self):
        company = self.mis_report_id.company_id
        if not company.pd_report_xlsx_template_file:
            raise ValidationError(_('Company PD Report XLSX template is missing!'))
        out = self._create_xlsx_report(company)
        current_time_string = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.now()))
        self.write({
            'out_xlsx': out,
            'name': _('PD_Report(%s).xlsx') % current_time_string,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('l10n_hr_mis_reports',
                                                              'mis_report_pd_report_wizard_view_action')
        action['res_id'] = self.id
        return action

    def create_xml_file(self):
        xml_data = self._generate_xml_data()
        current_time_string = fields.Datetime.to_string(fields.Datetime.context_timestamp(self,fields.Datetime.now()))
        self.write({
            'out_xml': xml_data,
            'xml_name': _('PD_Report(%s).xml') % current_time_string,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('l10n_hr_mis_reports',
                                                              'mis_report_pd_report_wizard_view_action')
        action['res_id'] = self.id
        return action


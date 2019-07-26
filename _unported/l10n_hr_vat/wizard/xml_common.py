# -*- coding: utf-8 -*-
import uuid
import os
import pytz
from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools.translate import _
from lxml import objectify, etree
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

def get_zagreb_datetime():
    #DB: Server mora biti na UTC time... ovo vraća točan local time za XML, fiskalizaciju isl...
    zg = pytz.timezone('Europe/Zagreb')
    return zg.normalize(pytz.utc.localize(datetime.utcnow()).astimezone(zg)).strftime("%Y-%m-%dT%H:%M:%S")

def _get_check_vat(self, vat):
    return  vat.startswith('HR') and vat[2:] or vat

def _check_valid_phone(self, phone):
    """Za PDV obrazac:
    Broj telefona, počinje sa znakom + nakon kojeg slijedi 8-13 brojeva, npr +38514445555
    """
    if not phone:
        return False
    phone = phone.replace(" ", "").replace("/", "").replace(",", "").replace("(", "").replace(")", "")

    if phone.startswith('00'):
        phone = '+' + phone[2:]
    if not phone.startswith('+'):
        phone = '+' + phone
    if 14 < len(phone) < 7:
        raise osv.except_osv(_('Format Error'), _('Unešeni broj telefona/faxa : %s u postavkama tvrtke nije ispravan\nOčekivani format je +385xxxxxxxx , (dozvoljno je korištenje znakova za razdvajanje i grupiranje (-/) i razmaka' % phone))

    return phone

def check_required(self, dict_object, check_list):
    for key in check_list:
        if not dict_object.get(key, False):
            raise osv.except_osv(_('Data Error'), _('Missing or misconfigured data : %s' % key))
    return True

def get_common_data(self, cr, uid, data, context=None):
    company = self.pool.get('res.company').browse(cr, uid, data['form']['company_id'])
    author_data = {
        'name':' '.join((company.responsible_fname, company.responsible_lname)),
        'fname':company.responsible_fname,
        'lname':company.responsible_lname,
        'tel':_check_valid_phone(self, company.responsible_tel),
        'mail':company.responsible_email
    }

    part_addr = company.street.split(' ')
    num = part_addr[len(part_addr) - 1]
    addr = ""
    for index in range(len(part_addr) - 1):
        addr += part_addr[index] + " "
    if len(addr) > 0:
        addr = addr[:-1]

    company_data = {
        'name':company.name,
        'vat':_get_check_vat(self, company.vat),
        'street':company.street,
        'ulica':addr,
        'kbr': num ,  # company.street2 and company.street2 or False, #TEMP solution... bolja opcija sa glavnog poslovnog prostora od fiskalizacije ;)
        'zip':company.zip,
        'city':company.city,
        'ispostava':company.ispostava, # šifra porezene uprave,
        'email': company.partner_id.email and company.partner_id.email or False,
        'tel': _check_valid_phone(self, company.responsible_tel),
        #'fax': _check_valid_phone(self, company.partner_id.fax),
    }
    metadata = {
        'autor':' '.join((company.responsible_fname, company.responsible_lname)),
        'format':'text/xml',
        'jezik':'hr-HR',
        'tip':u'Elektronički obrazac',
        'adresant':u'Ministarstvo Financija, Porezna uprava, Zagreb',
    }

    check_required(self, author_data,['name','fname','lname'])
    check_required(self, company_data,['name','vat','street','zip','city','ispostava'])
    return author_data, company_data, metadata

def create_xml_metadata(self, metadata):
    #metadata['naslov']= template.xsd_id.title           # u"Prijava poreza na dodanu vrijednost"
    #metadata['uskladjenost'] = template.xsd_id.name     # u'ObrazacPDV-v8-0'
    identifikator = uuid.uuid4()
    datum_vrijeme = get_zagreb_datetime()

    MD = objectify.ElementMaker(annotate=False, namespace="http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0")
    md = MD.Metapodaci(
            MD.Naslov(metadata['naslov'], dc="http://purl.org/dc/elements/1.1/title"),
            MD.Autor(metadata['autor'], dc="http://purl.org/dc/elements/1.1/creator"),
            MD.Datum(datum_vrijeme, dc="http://purl.org/dc/elements/1.1/date"),
            MD.Format(metadata['format'], dc="http://purl.org/dc/elements/1.1/format"),
            MD.Jezik(metadata['jezik'], dc="http://purl.org/dc/elements/1.1/language"),
            MD.Identifikator(identifikator, dc="http://purl.org/dc/elements/1.1/identifier"),
            MD.Uskladjenost(metadata['uskladjenost'], dc="http://purl.org/dc/terms/conformsTo"),
            MD.Tip(metadata['tip'], dc="http://purl.org/dc/elements/1.1/type"),
            MD.Adresant(metadata['adresant']),
            )

    return md, identifikator

def create_xml_header(self, period, company, author):
#def create_xml_header(self, obrazac, company, author):
    EM = objectify.ElementMaker(annotate=False)
    header = EM.Zaglavlje(
                EM.Razdoblje(
                    EM.DatumOd(period['date_start']),
                    EM.DatumDo(period['date_stop'])),
                EM.Obveznik(
                    EM.Naziv(company['name']),
                    EM.OIB(company['vat']),
                    EM.Adresa(
                        EM.Mjesto(company['city']),
                        EM.Ulica(company['ulica']),
                        #Broj dodam kasnije ako postoji
                        ),),
                EM.ObracunSastavio(
                    EM.Ime(author['fname']),
                    EM.Prezime(author['lname']),
                    #Tel, Fax i Email dodam kasnije ako postoje!
                    ),
                EM.Ispostava(company['ispostava']))
    #punim ostale podatke ako postoje...
    if company.get('kbr', False)  : header.Obveznik.Adresa.Broj    = EM.Broj(company['kbr'])
    #if company.get('tel', False)  : header.ObracunSastavio.Telefon = EM.Telefon(company['tel'])
    #if company.get('fax', False)  : header.ObracunSastavio.Fax     = EM.Fax(company['fax'])
    #if company.get('email', False): header.ObracunSastavio.Email   = EM.Email(company['email'])
    return header

def etree_tostring(self, object):
    objectify.deannotate(object)
    return etree.tostring(object, pretty_print=True).replace('ns0:','').replace(':ns0','')


def validate_xml(self, xml):
    # ovo provjeriti uglavnom ..
    # ...l10n_hr_pdv/wizzard ili gdje ce vec biti sheme
    xsd_path = os.path.join(xml['path'] , xml['xsd_path'])
    os.chdir(xsd_path)
    xsd_file = os.path.join(xsd_path,xml['xsd_name'])
    xsd = StringIO(open(xsd_file,'r').read())
    xml_schema = etree.XMLSchema(etree.parse(xsd))
    try:
        xml_schema.assert_(etree.parse(StringIO(xml['xml'])))
    except AssertionError as E:
        raise osv.except_osv(u'Greška u podacima',E[0])
    # print xml['xml'] # test xml printout to console
    return True
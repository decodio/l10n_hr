import uuid
import os
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, exceptions, _
from odoo.exceptions import except_orm
from lxml import objectify, etree
from odoo.tools import float_is_zero, float_round, file_open
from io import StringIO, BytesIO


def get_zagreb_datetime():
    zg = pytz.timezone("Europe/Zagreb")
    return zg.normalize(
        pytz.utc.localize(datetime.utcnow()).astimezone(zg)
    ).strftime("%Y-%m-%dT%H:%M:%S")


def _get_check_vat(self, vat):
    return vat.startswith("HR") and vat[2:] or vat


def _check_valid_phone(self, phone):
    """Za PDV obrazac:
    Broj telefona, počinje sa znakom + nakon kojeg slijedi 8-13 brojeva, npr +38514445555
    """
    if not phone:
        return False
    phone = (
        phone.replace(" ", "")
        .replace("/", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
    )

    if phone.startswith("00"):
        phone = "+" + phone[2:]
    if not phone.startswith("+"):
        phone = "+" + phone
    if 14 < len(phone) < 7:
        raise except_orm(
            _("Format Error"),
            _(
                "Unešeni broj telefona/faxa : %s u postavkama tvrtke nije ispravan\nOčekivani format je +385xxxxxxxx , (dozvoljno je korištenje znakova za razdvajanje i grupiranje (-/) i razmaka"
                % phone
            ),
        )

    return phone


def check_required(self, dict_object, check_list):
    for key in check_list:
        if not dict_object.get(key, False):
            raise except_orm(
                _("Data Error"), _("Missing or misconfigured data : %s" % key)
            )
    return True


def get_common_data(self, cr, uid, data, context=None):
    company = data.company_id
    author_data = {
        "name": " ".join(
            (company.responsible_fname, company.responsible_lname)
        ),
        "fname": company.responsible_fname,
        "lname": company.responsible_lname,
        "tel": _check_valid_phone(self, company.responsible_tel),
        "email": company.responsible_email,
    }

    part_addr = company.street.split(" ")
    num = part_addr[len(part_addr) - 1]
    addr = ""
    for index in range(len(part_addr) - 1):
        addr += part_addr[index] + " "
    if len(addr) > 0:
        addr = addr[:-1]

    company_data = {
        "name": company.name,
        "vat": _get_check_vat(self, company.vat),
        "street": company.street,
        "ulica": addr,
        "kbr": num,
        "zip": company.zip,
        "city": company.city,
        "email": company.partner_id.email
        and company.partner_id.email
        or False,
        "tel": _check_valid_phone(self, company.responsible_tel),
        "fax": _check_valid_phone(self, company.phone),  # partner_id.fax),
    }
    metadata = {
        "autor": " ".join(
            (company.responsible_fname, company.responsible_lname)
        ),
        "format": "text/xml",
        "jezik": "hr-HR",
        "tip": u"Elektronički obrazac",
        "adresant": u"Ministarstvo Financija, Porezna uprava, Zagreb",
    }

    check_required(self, author_data, ["name", "fname", "lname"])
    check_required(
        self, company_data, ["name", "vat", "street", "zip", "city"]
    )
    return author_data, company_data, metadata


def create_xml_metadata(self, metadata):
    identifikator = uuid.uuid4()
    datum_vrijeme = get_zagreb_datetime()

    MD = objectify.ElementMaker(
        annotate=False,
        namespace="http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0",
    )
    md = MD.Metapodaci(
        MD.Naslov(
            metadata["naslov"], dc="http://purl.org/dc/elements/1.1/title"
        ),
        MD.Autor(
            metadata["autor"], dc="http://purl.org/dc/elements/1.1/creator"
        ),
        MD.Datum(datum_vrijeme, dc="http://purl.org/dc/elements/1.1/date"),
        MD.Format(
            metadata["format"], dc="http://purl.org/dc/elements/1.1/format"
        ),
        MD.Jezik(
            metadata["jezik"], dc="http://purl.org/dc/elements/1.1/language"
        ),
        MD.Identifikator(
            identifikator, dc="http://purl.org/dc/elements/1.1/identifier"
        ),
        MD.Uskladjenost(
            metadata["uskladjenost"], dc="http://purl.org/dc/terms/conformsTo"
        ),
        MD.Tip(metadata["tip"], dc="http://purl.org/dc/elements/1.1/type"),
        MD.Adresant(metadata["adresant"]),
    )

    return md, identifikator


def create_xml_header(self, period, company, author):
    unpaid_to = (
        (
            # datetime.strptime(period["date_stop"], "%Y-%m-%d")
                period["date_stop"] + relativedelta(months=1)
        )
        + relativedelta(day=1, months=+1, days=-1)
    ).strftime("%Y-%m-%d")
    EM = objectify.ElementMaker(annotate=False)
    header = EM.Zaglavlje(
        EM.Razdoblje(
            EM.DatumOd(period["date_start"]), EM.DatumDo(period["date_stop"])
        ),
        EM.PorezniObveznik(
            EM.OIB(company["vat"]),
            EM.Naziv(company["name"]),
            EM.Adresa(
                EM.Mjesto(company["city"]),
                EM.Ulica(company["ulica"]),
                EM.Broj(company.get("kbr", False) and company["kbr"] or ""),
            ),
            EM.Email(company.get("email", False) and company["email"] or ""),
        ),
        EM.IzvjesceSastavio(
            EM.Ime(author["fname"]),
            EM.Prezime(author["lname"]),
            EM.Telefon(company.get("tel", False) and company["tel"] or ""),
            EM.Fax(company.get("fax", False) and company["fax"] or ""),
            EM.Email(company.get("email", False) and company["email"] or ""),
        ),
        EM.NaDan(period["date_stop"]),
        EM.NisuNaplaceniDo(unpaid_to),
    )

    return header


def etree_tostring(self, object):
    objectify.deannotate(object)
    return (
        etree.tostring(object, pretty_print=True)
        .replace(b"ns0:", b"")
        .replace(b":ns0", b"")
    )


def validate_xml(self, xml):
    xsd_file = 'l10n_hr_opz_stat/models/schema/opz_stat_xml_v1.0/ObrazacOPZ-v1-0.xsd'
    xsd_etree_obj = etree.parse(file_open(xsd_file))
    official_schema = etree.XMLSchema(xsd_etree_obj)
    try:
        t = etree.parse(BytesIO(xml["xml"]))
        official_schema.assertValid(t)
    except AssertionError as E:
        raise except_orm(u"Greška u podacima", E[0])
    return True


#     xsd_path = os.path.join(xml["path"], xml["xsd_path"])
#     os.chdir(xsd_path)
#     xsd_file = os.path.join(xsd_path, xml["xsd_name"])
#     xsd = StringIO(open(xsd_file, "r").read())
#
#     xml_schema = etree.XMLSchema(etree.parse(xsd))
#     #xml_schema = etree.parse(StringIO.BytesIO(xsd_file))  etree.XMLSchema(etree.fromstring(xsd))
#     try:
#         # print xml['xml']  # test xml printout to console
#         xml_schema.assert_(etree.parse(StringIO(xml["xml"])))
#     except AssertionError as E:
#         raise except_orm(u"Greška u podacima", E[0])
#     return True
#
# xsd_file = 'l10n_hr_opz_stat/models/schema/opz_stat_xml_v1.0/ObrazacOPZ-v1-0.xsd'
# fx = file_open(xsd_file)
# xsd_etree_obj = etree.parse(file_open(xsd_file))
# official_schema = etree.XMLSchema(xsd_etree_obj)
# try:
#     t = etree.parse(BytesIO(xml["xml"]))
#     official_schema.assertValid(t)
#
#
# # xsd_etree_obj = etree.parse(file_open(xsd_file))
# # official_schema = etree.XMLSchema(xsd_etree_obj)
# # try:
# #     t = etree.parse(BytesIO(xml_string))
# #     official_schema.assertValid(t)
# # except Exception as e:

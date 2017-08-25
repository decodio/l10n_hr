# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from lxml import etree
import logging
import base64
from datetime import datetime


try:
    from unidecode import unidecode
except ImportError:
    unidecode = None

logger = logging.getLogger(__name__)

class BankingExportHRWizard(models.TransientModel):
    _name = 'banking.export.sepa.wizard'
    _inherit = 'banking.export.sepa.wizard'
    _description = 'Export SEPA File Croatian Localisation'


    @api.multi
    def finalize_sepa_file_creation(
            self, xml_root, total_amount, transactions_count, gen_args):

        pain_flavor = self.payment_order_ids[0].mode.type.code
        nodes =xml_root.findall(".")
        value = self._get_name()

        for tree in nodes:
            for elem in tree.iter():
                if elem.tag == 'GrpHdr':
                    msgID_tag = elem.find('MsgId')
                    if msgID_tag is None:
                        msgID_tag = etree.SubElement(elem, 'MsgId')
                    msgID_tag.text = value

                if elem.tag == 'PmtInf':
                    for pline in elem.iter():
                        Strd_tag = pline.find('CdtTrfTxInf/RmtInf/Strd')
                        if Strd_tag is not None:
                            add_reef_info_tag = Strd_tag.find('AddtlRmtInf')
                            if add_reef_info_tag is None:
                                add_reef_info_tag = etree.SubElement(Strd_tag, 'AddtlRmtInf')
                                add_reef_info_tag.text = '-'
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)

        cro_pain_xsd_file = 'l10n_hr_sepa/schema/%s.xsd' % pain_flavor
        if cro_pain_xsd_file:
            xml_string = xml_string.replace("urn:iso:std:iso:20022:tech:xsd:",
                                            "urn:iso:std:iso:20022:tech:xsd:scthr:")
            gen_args['pain_xsd_file'] = cro_pain_xsd_file
        self._validate_xml(xml_string, gen_args)

        xml_root = etree.fromstring(xml_string)
        res = super(BankingExportHRWizard, self).finalize_sepa_file_creation(xml_root, total_amount,
                                                                             transactions_count, gen_args)

        self.write({'filename': value})
        return res

    @api.multi
    def _get_name(self):
        number = 1
        date_today = datetime.today()
        reference = 'UN' + date_today.strftime('%Y') + date_today.strftime('%m') \
                    + date_today.strftime('%d') + str(number).zfill(4)
        value = unidecode(reference)
        unallowed_ascii_chars = [
            '"', '#', '$', '%', '&', '*', ';', '<', '>', '=', '@',
            '[', ']', '^', '_', '`', '{', '}', '|', '~', '\\', '!']
        for unallowed_ascii_char in unallowed_ascii_chars:
            value = value.replace(unallowed_ascii_char, '-')
        return value
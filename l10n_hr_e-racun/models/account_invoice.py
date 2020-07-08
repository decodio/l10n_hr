# -*- encoding: utf-8 -*-
# © 2019 Decodio Applications d.o.o. (davor.bojkic@decod.io)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html).

import logging
from pytz import timezone
from datetime import datetime
from lxml import etree
# from StringIO import StringIO
from odoo import tools, models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

# def register_namespaces(nsmap):
#     for prefix, uri in nsmap:
#         etree.register_namespace(prefix, uri)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ubl_schema = fields.Selection(
        selection=[
            ('EN19631', 'UBL-2.1-EN19631-B2G'),
            ('HRINVOICE1', 'UBL-2.1-HRINVOICE1-B2B')
        ], string="UBL Schema",
        help="UBL shema for generating e-invoice for this partner,"
             "If left empty, HRINVOICE1-B2B schema will be applied"
    )
    ubl_business_process = fields.Selection(
        selection=[
            ('P1', 'P1-Fakturiranje isporuka dobara i usluga preko narudžbi na temelju ugovora'),
            ('P2', 'P2-Periodično fakturiranje isporuka na temelju ugovora'),
            ('P3', 'P3-Fakturiranje isporuka preko nepredviđene narudžbe'),
            ('P4', 'P4-Plaćanje predujma (avansno plaćanje)'),
            ('P5', 'P5-Plaćanje na licu mjesta'),
            ('P6', 'P6-Plaćanje prije isporuke na temelju narudžbe'),
            ('P7', 'P7-Računi s referencom na otpremnicu'),
            ('P8', 'P8-Računi s referencom na otpremnicu i primku'),
            ('P9', 'P9-Odobrenje ili negativno fakturiranje'),
            ('P10', 'P10-Korektivno fakturiranje'),
            ('P11', 'P11-Parcijalno i završno fakturiranje'),
            ('P12', 'P12-Samoizdavanje računa'),
        ], string="Business process",
        default='P1',
        help="UBL Business process described in documentation"
    )
    ubl_document_type = fields.Many2one(
        comodel_name='unece.code.list',
        string="Document type",
        domain=[('type', '=', 'doc_type')],
    )
    ubl_file = fields.Many2one(
        comodel_name='ir.attachment',
        string="UBL-XML file",
        domain=[()], copy=False
    )
    ubl_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='invoice_ubl_attachment_rel',
        column1='invoice_id', column2='att_id',
        string='UBL attached documents', copy=False
    )

    ubl_buyer_ref = fields.Char(
        string="Buyer reference",
        help="A reference provided by the buyer used for internal routing of the document.",
        copy=False
    )
    ubl_order_ref = fields.Char(
        string="Order reference",
        help="A reference to the Order with which this Invoice is associated.",
        copy=False
    )

    # -> self.company_id.croatia from base!
    # def company_croatia(self):
    #     """
    #     :return: boolean croatia comapny
    #     """
    #     company_id = self.company_id
    #     if not company_id:
    #         company = self.env['res.company']
    #         company_id = company._company_default_get(
    #             'account.invoice')
    #         company_id = company.browse(company_id)
    #     return company_id.country_id.code == 'HR'

    @api.multi
    def _ubl_add_attachments(self, parent_node, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_attachments(
            parent_node, ns, version=version)
        if self.company_id.croatia and self.ubl_attachment_ids:
            pass

    def get_invoice_issue_time(self):
        """
        ugly hack to get issue time from utc record
        :return:
        """
        user_timezone = self.env.user.partner_id.tz or 'Europe/Zagreb'
        local_tz = timezone(user_timezone)
        dt_date_time = datetime.strptime(self.vrijeme_izdavanja, "%d.%m.%Y %H:%M:%S")
        dt_date_time = dt_date_time + local_tz.utcoffset(dt_date_time)
        create_time = datetime.strftime(dt_date_time, "%Y-%m-%d %H:%M:%S")[11:]
        return create_time

    @api.multi
    def attach_ubl_xml_file_button(self):
        self.ensure_one()  # in original method also!
        schema = False
        if self.company_id.croatia:
            # check required data is entered
            if not self.company_id.eracun_memorandum:
                raise Warning(
                    _('Memorandum data is not filled on company form!'))
            if not self.ubl_schema:
                self.ubl_schema = self.partner_id.e_racun_schema or 'HRINVOICE1'
            if not self.ubl_document_type:
                # original only use 380 or 381 , we need more!
                self.ubl_document_type = self.env.ref(
                    'l10n_hr_eracun.unece_doc_380')
            schema = self.ubl_schema
        res = super(AccountInvoice, self.with_context(schema=schema)). \
            attach_ubl_xml_file_button()
        self.ubl_file = res['res_id']
        return res

    # GENERAL PART
    def _ubl_insert_element(self, parent_node, find_node, insert_node,
                            ns, before=False):
        """
        Post processing of generated XML etree-object
        :param parent_node: main node
        :param find_node: node to find as reference string
        :param insert_node: new node to insert
        :param ns: namspace dict
        :param before: position of insert_node
        """
        target_obj = parent_node.find(find_node % ns)
        if target_obj is None:
            _logger.debug("XML insert element : Target not found")
        update_obj = target_obj.getparent()
        if before:
            idx = update_obj.index(target_obj)
        else:
            idx = update_obj.index(target_obj) + 1
        update_obj.insert(idx, insert_node)

    def _ubl_l10n_hr_date_due(self, parent_node, ns):
        """
        BR-CO-25
        U slučaju pozitivnog iznosa koji dospijeva na plaćanje (BT-115),
        mora biti naveden
        ili datum dospijeća plaćanja (BT-9) -> iza IssueTime
        ili uvjeti plaćanja (BT-20).        -> Iza PaymentMeans

        BOLE: 6.11. ma fcuk!
              upisacu ja njemu oba elementa pa nek si misli...
              po specifikaciji elementi nisu obavezni ali testovi su pokazali
              da neki provideri traze bas oba elementa,
              a ako i ne traze, nije explicitno zabranjeno koristenje oba
        """
        payment_term = self.payment_term_id or False
        payment_lines = payment_term and \
            [l for l in payment_term.line_ids] or False

        # new : pisem oba uvjek
        pt_element = parent_node.find(ns['cac'] + 'PaymentTerms')
        if not pt_element:
            pay_terms = etree.Element(ns['cac'] + 'PaymentTerms')
            pay_term_note = etree.SubElement(pay_terms, ns['cbc'] + 'Note')
            pay_term_note.text = payment_term and payment_term.name or \
                _("Payment should be made by %s" % self.date_due)  # TODO: format datuma?
            self._ubl_insert_element(
                parent_node, './/%(cac)sPaymentMeans', pay_terms, ns)

        dd_element = parent_node.find(ns['cbc'] + 'DueDate')
        if not dd_element:
            date_due = etree.Element(ns['cbc'] + 'DueDate')
            date_due.text = fields.Date.to_string(self.date_due)
            self._ubl_insert_element(
                parent_node=parent_node,
                find_node='.//%(cbc)sIssueTime',
                insert_node=date_due,
                ns=ns, before=False)

    @api.multi
    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_header(
            parent_node=parent_node, ns=ns, version=version)
        if self.company_id.croatia:
            issue_time = etree.Element(ns['cbc'] + 'IssueTime')
            issue_time.text = self.get_invoice_issue_time()
            self._ubl_insert_element(
                parent_node=parent_node,
                find_node='.//%(cbc)sIssueDate',
                insert_node=issue_time, ns=ns)

            type_code = parent_node.find(ns['cbc'] + 'InvoiceTypeCode')
            if self.ubl_document_type and \
                    type_code.text != self.ubl_document_type.code:
                type_code.text = self.ubl_document_type.code

    @api.multi
    def onchange_partner_id(
            self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        # why not called?
        if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            res['value']['eracun_schema'] = p.e_racun_schema or 'HRINVOICE1'
        return res

    @api.multi
    def get_ubl_filename(self, version='2.1'):
        self.ensure_one()
        now = fields.Datetime.to_string(
            fields.Datetime.now()).replace(' ', '_')
        xml_name = "UBL-%s_[%s][%s].xml" % (self.number, now, self.ubl_schema)
        return xml_name

    def _ubl_add_invoice_line_tax_total(
            self, iline, parent_node, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_invoice_line_tax_total(
            iline, parent_node, ns, version=version)
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        res_taxes = iline.invoice_line_tax_ids.compute_all(
            price, currency=iline.currency_id,
            quantity=iline.quantity, product=iline.product_id,
            partner=self.partner_id)
        line_tax_total = parent_node.find(ns['cac'] + 'TaxTotal')
        line_tax_subtotal = line_tax_total.find(ns['cac'] + 'TaxSubtotal')
        line_subtotal_taxable = line_tax_subtotal.find(ns['cbc'] + 'TaxableAmount')
        if not line_subtotal_taxable:
            taxable_amount_node = etree.Element(
                ns['cbc'] + 'TaxableAmount',
                currencyID=self.currency_id.name)
            taxable_amount_node.text = '%0.*f' % (2, res_taxes['total_excluded'])
            line_tax_subtotal.insert(0, taxable_amount_node)

    @api.multi
    def _ubl_add_invoice_reference(self, parent_node, ns):
        # Ispred: Signature ili AccountingSupplierParty...
        existing_ref = parent_node.find('.//%(cac)sOrderReference' % ns)
        if existing_ref:
            # upisan je sadrzaj polja name, što nije naša željena referenca
            parent_node.remove(existing_ref)

        curr_node = parent_node.find('.//%(cac)sSignature' % ns)

        if curr_node is None:
            curr_node = parent_node.find('.//%(cac)sAccountingSupplierParty' % ns)
        if curr_node is None:
            _logger.debug('Reference insert node not found, skip insert reference')
            return
        idx = parent_node.index(curr_node)
        if self.ubl_order_ref:
            OrderRef = etree.Element(ns['cac'] + 'OrderReference')
            #  cbc:ID                        1-1
            #  cbc:SalesOrderID              0-1
            #  cbc:CopyIndicator             0-1
            #  cbc:UUID                      0-1
            #  cbc:IssueDate                 0-1
            #  cbc:IssueTime                 0-1
            #  cbc:CustomerReference         0-1
            #  cbc:OrderTypeCode             0-1
            #  cac:Documentreference         0-1
            OrderRefId = etree.SubElement(OrderRef, ns['cbc'] + 'ID')
            OrderRefId.text = self.ubl_order_ref
            parent_node.insert(idx, OrderRef)


        if self.ubl_buyer_ref:
            BuyerRef = etree.Element(ns['cbc'] + 'BuyerReference')
            BuyerRef.text = self.ubl_buyer_ref
            parent_node.insert(idx, BuyerRef)

    @api.model
    def _ubl_get_tax_scheme_dict_from_tax(self, tax):
        tax_scheme_dict = super(AccountInvoice, self).\
            _ubl_get_tax_scheme_dict_from_tax(tax=tax)
        tax_scheme_dict['type_code'] = tax.unece_categ_id.name or False  # tax.unece_type_code or False
        # tax_scheme_dict['name'] = tax.unece_categ_id.name or False
        return tax_scheme_dict

    @api.model
    def _ubl_get_nsmap_namespace(self, doc_name, version='2.1'):
        """
        Croatia specific UBL extensions
        """
        nsmap, ns = super(AccountInvoice, self)._ubl_get_nsmap_namespace(
            doc_name, version=version)
        if self.company_id.croatia:
            nsmap.update({
                'ext': 'urn:oasis:names:specification:ubl:' 
                       'schema:xsd:CommonExtensionComponents-2',
            #    'xsi': "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
            })
            ns.update({
                'ext': '{urn:oasis:names:specification:ubl:' 
                       'schema:xsd:CommonExtensionComponents-2}'
            })
            if self.env.context.get('schema') == 'HRINVOICE1':
            #     # NE :u modulu  moj eračun, # DA : HT
                nsmap['exthr'] = 'urn:invoice:hr:schema:'\
                                 'xsd:CommonExtensionComponents-1'
                ns['exthr'] = '{urn:invoice:hr:schema:' \
                              'xsd:CommonExtensionComponents-1}'
        # register_namespaces(nsmap)
        return nsmap, ns

    @api.multi
    def _get_croatia_xsd_schema(self):
        schema = self.env.context.get('schema')
        schema_files = {
            'EN19631': 'l10n_hr_eracun/schema/UBL-2.1-' 
                       'EN16931/maindoc/UBL-Invoice-2.1.xsd',
            'HRINVOICE1': 'l10n_hr_eracun/schema/UBL-2.1-' 
                       'HRINVOICE1/maindoc/HRInvoice.xsd'
        }
        xsd_file = schema and schema_files.get(schema) or False
        return xsd_file

    @api.multi
    def _ubl_check_hrinvoice_schema(self, xml_string, document, version='2.1'):
        """
        First level of validation - local xsd
        Inherit in edi module and validate on peppol if needed
        """
        if version != '2.1':
            # validiram samo 2.1!
            _logger.info('XML Schema is %s, not validated!' % version)
            return True
        return True  # For now just skip internal tests
        xsd_file = self._get_croatia_xsd_schema()
        if not xsd_file:
            _logger.info('No validation schema found')
            return True
        xsd_etree_obj = etree.parse(tools.file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            t = etree.parse(StringIO(xml_string))
            official_schema.assertValid(t)
        except Exception as  e:
            # if the validation of the XSD fails, we arrive here
            _logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            _logger.warning(xml_string)
            _logger.warning(e)
            raise Warning(
                _("The generated XML file is not valid against the official "
                    "XML Schema Definition. The generated XML file and the "
                    "full error have been written in the server logs. "
                    "Here is the error, which may give you an idea on the "
                    "cause of the problem : %s.")
                % repr(e))
        return True

    @api.model
    def _ubl_check_xml_schema(self, xml_string, document, version='2.1'):
        if self.company_id.croatia:
            return self._ubl_check_hrinvoice_schema(
                xml_string, document, version=version)
        return super(AccountInvoice, self)._ubl_check_xml_schema(
            xml_string=xml_string, document=document, version=version)

    @api.multi
    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        parent_node = super(AccountInvoice, self).generate_invoice_ubl_xml_etree(
            version=version)

        """
        TODO provjera: odobrenje je Invoice ili CreditNote
        originalna metoda ne provjerava:
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        """
        ns = {}
        if self.company_id.croatia:
            nsmap, ns = self._ubl_get_nsmap_namespace(
                'Invoice-2', version=version)
            if self.env.context.get('schema') == 'HRINVOICE1':
                parent_node = self.update_hrinvoice_data(parent_node, ns)
            else:  # B2G
                parent_node = self.update_hr_en19631_data(parent_node, ns)
            """
            TODO : provjeri element InvoiceTypeCode
            puni se u _ubl_add_header()
              - originalni modul ima opcije:
                380 - out_invoice
                381 - out_refund
                
            HP specka: 
            BT-3 - ŠIFRA VRSTE RAČUNA: UNTDID 1001 - 
            http://www.unece.org/trade/untdid/d98a/uncl/uncl1001.htm
                # 82 – Račun za mjerene usluge
                # 325 – Predračun
                # 326 – Parcijalni račun
                # 380 – Komercijalni račun                TREBA
                # 381 – Odobrenje                         TREBA
                # 383 – Terećenje
                # 384 – Korektivni račun                  TREBA
                # 386 – Račun za predujam                 TREBA
                # 394 – Račun za leasing
            """

        return parent_node


    @api.multi
    def _ubl_add_invoice_line(
            self, parent_node, iline, line_number, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_invoice_line(
            parent_node, iline, line_number, ns, version='2.1')
        AllLineNodes = parent_node.findall('.//%(cac)sInvoiceLine' % ns)
        line_node = AllLineNodes[-1]
        discount_id = 1
        # 1. popusti
        if iline.discount:
            # POPUST NA STAVCI
             # just created in super !
            AllowanceCharge = etree.Element(
                ns['cac'] + 'AllowanceCharge')
            ChargeID = etree.SubElement(
                AllowanceCharge, ns['cbc'] + 'ID')
            ChargeID.text = str(discount_id)
            discount_id += 1
            ChargeIndicator = etree.SubElement(
                AllowanceCharge, ns['cbc'] + 'ChargeIndicator')
            # An indicator that this AllowanceCharge
            # describes a charge (true) or a discount (false).
            ChargeIndicator.text = iline.discount > 0 and 'false' or 'true'
            MultiFactor = etree.SubElement(
                AllowanceCharge, ns['cbc'] + 'MultiplierFactorNumeric')
            MultiFactor.text = str(iline.discount / 100)
            ChargeAmount = etree.SubElement(
                AllowanceCharge, ns['cbc'] + 'Amount',
                currencyID=iline.currency_id.name)
            ChargeAmount.text = str(iline.discount_total)
            BaseAmount = etree.SubElement(
                AllowanceCharge, ns['cbc'] + 'BaseAmount',
                currencyID=iline.currency_id.name)
            BaseAmount.text = str(iline.list_amount)
            self._ubl_insert_element(
                parent_node=line_node,
                find_node='.//%(cbc)sLineExtensionAmount',
                insert_node=AllowanceCharge,
                ns=ns, before=False)

        # 2. check taxes:
        # Original: BaseUbl._ubl_add_item
        # - ne dobije iline object, pa poreze uzima sa proizvoda,
        #   pritom ne shvati ručne promjene ili promjene zbog fiskalne pozicije
        # provjerim i popravim kaj treba

        taxes = [tax for tax in iline.invoice_line_tax_ids]
        if self.ubl_schema == 'EN19631':
            # B2G line/item/ClassifiedTaxcategory
            item_node = line_node.find('.//%(cac)sItem' % ns)
            for tax in taxes:
                self._ubl_add_tax_category(
                   tax, item_node, ns, node_name='ClassifiedTaxCategory',
                        version=version)

        # 3. Price base qty
        # InvoiceLine/Price
        # Original:
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        # Croatia fix: BaseQuantity = 1, price = unit price
        price_amount = line_node.find('.//%(cac)sPrice/%(cbc)sPriceAmount' % ns)
        price_amount.text = '%0.*f' % (2, iline.price_unit)
        price_bq = line_node.find('.//%(cac)sPrice/%(cbc)sBaseQuantity' % ns)
        price_bq.text = '1'

    def _get_ubl_customization(self, schema):
        """
        inherit properly in provider module
        # Fina  : urn:invoice.hr:ubl-2.1-customizations:FinaInvoice
        # HP    : urn:cen.eu:en16931:2017#compliant#urn:mingo.hr:2018:1.0
        # HT EDI:  urn:invoice.hr:ubl-2.1-customizations:HRInvoice
        :return: proper customization string
        """
        customizations = {
            'HRINVOICE1': 'urn:invoice.hr:ubl-2.1-customizations:FinaInvoice',
            'EN19631': 'urn:cen.eu:en16931:2017'
        }
        return customizations.get(schema)

    @api.multi
    def _ubl_set_l10n_hr_customization(self, parent_node, ns):
        schema = self.env.context.get('schema', False)
        if not schema:
            return
        customization = etree.Element(ns['cbc'] + 'CustomizationID')
        customization.text = self._get_ubl_customization(schema)
        self._ubl_insert_element(
            parent_node=parent_node,
            find_node='.//%(cbc)sUBLVersionID',
            insert_node=customization,
            ns=ns, before=False)

    @api.multi
    def update_hr_en19631_data(self, parent_node, ns):
        # 1. customized UBL !
        self._ubl_set_l10n_hr_customization(parent_node, ns)
        # 1. company data:  BT-33
        #    AccountingSupplierParty/Party/PartyLegalEntity/CompanyLegalForm
        supplier = parent_node.find('.//%(cac)sAccountingSupplierParty' % ns)
        legal_entity = supplier.find('.//%(cac)sPartyLegalEntity' % ns)
        company_legal = etree.Element(ns['cbc'] + 'CompanyLegalForm')
        company_legal.text = self.company_id.eracun_memorandum
        legal_entity.append(company_legal)
        self._ubl_set_note_l10n_hr(parent_node, ns)
        self._ubl_set_acc_contact_l10n_hr(parent_node, ns)
        # 3. delivery date : Delivery prije due date!
        self._ubl_set_delivery_date(parent_node, ns)
        # 4. company logo TODO!
        #self._ubl_add_payment_means(parent_node, ns)
        self._ubl_l10n_hr_date_due(parent_node, ns)
        self._ubl_add_invoice_reference(parent_node, ns)
        self._ubl_cleanup_en19631(parent_node, ns)
        self.check_digits(parent_node, ns)
        #self.check_invoice_line_taxes(parent_node, ns)
        return parent_node

    @api.multi
    def _get_eracun_profile(self):
        """
        inherit and customize in provider modules
        :return: profile Id text
        """
        return 'GENERIC HR'

    @api.multi
    def update_hrinvoice_data(self, parent_node, ns):
        """
        Update generated invoice with croatia specific requirements
        :param parent_node: generated Invoice element
        :param ns:
        :return:
        """
        # self._ubl_create_croatia_extensions(parent_node, ns)

        # moj eracun
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance",
                                 "schemaLocation")
        parent_node.attrib[attr_qname] = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 HRInvoice.xsd"
        # /moj eracun

        self._ubl_set_l10n_hr_extensions(parent_node, ns)
        self._ubl_set_l10n_hr_customization(parent_node, ns)
        self._ubl_set_note_l10n_hr(parent_node, ns)
        self._ubl_add_invoice_reference(parent_node, ns)

        profile = etree.Element(ns['cbc'] + 'ProfileID')
        # HP - upisuje vrstu poslovnog procesa : P1 - P12
        profile.text = self._get_eracun_profile()
        self._ubl_insert_element(
            parent_node=parent_node,
            find_node='.//%(cbc)sCustomizationID',
            insert_node=profile,
            ns=ns, before=False)

        # TODO: how to know if it is a copy?
        copy_ind = etree.Element(ns['cbc'] + 'CopyIndicator')
        copy_ind.text = self.env.context.get('copy_indicator') or 'false'
        self._ubl_insert_element(
            parent_node=parent_node,
            find_node='.//%(cbc)sIssueDate',
            insert_node=copy_ind,
            ns=ns, before=True)

        # PARTY LEGAL ENTITY
        legal_entity_check = parent_node.findall('.//%(cac)sPartyLegalEntity' % ns)
        for lec in legal_entity_check:
            if not lec.find('.//%(cbc)sCompanyID' % ns):
                parent = lec.getparent()
                endpoint = parent.find('.//%(cbc)sEndpointID' % ns)
                company_id_node = etree.Element(ns['cbc'] + 'CompanyID')
                company_id_node.text = endpoint.text
                self._ubl_insert_element(
                    parent_node=lec,
                    find_node='.//%(cbc)sRegistrationName',
                    insert_node=company_id_node,
                    ns=ns)  # After RegName

        self._ubl_set_acc_contact_l10n_hr(parent_node, ns)
        self._ubl_set_delivery_date(parent_node, ns)
        # CLEANUP:
        self._ubl_cleanup_hrinvoice1(parent_node, ns)
        self.check_digits(parent_node, ns)
        return parent_node

    def _ubl_set_acc_contact_l10n_hr(self, parent_node, ns):

        # AccountingContact -> not using original method _ubl_add_contact
        contacts = {
            'AccountingSupplierParty': self.company_id.partner_id,
            'AccountingCustomerParty': self.partner_id
        }
        for key in contacts:
            node_tag = './/%(cac)s' + key
            cnode = parent_node.find(node_tag % ns)
            if not cnode.find('.//%(cac)sAccountingContact' % ns):
                contact_node = etree.Element(ns['cac'] + 'AccountingContact')
                cn_name = etree.SubElement(
                    contact_node, ns['cbc'] + 'Name')
                cn_email = etree.SubElement(
                    contact_node, ns['cbc'] + 'ElectronicMail')
                cpartner = contacts[key]
                # BOLE : ispao papak!
                #  e_racun_email na partneru
                #  eracun_email na company!

                mail = cpartner.e_racun_mail and cpartner.e_racun_mail or \
                       cpartner.email and cpartner.email or False

                if not mail:
                    continue
                name = cpartner.name and cpartner.name or '-'
                cn_name.text = name
                cn_email.text = mail
                self._ubl_insert_element(
                    parent_node=cnode,
                    find_node='.//%(cac)sParty',
                    insert_node=contact_node,
                    ns=ns)

    def _ubl_set_delivery_date(self, parent_node, ns):
        """
        BG-13
        BG-15 Dostavna adresa TODO!
        """
        find_nodes = [
            'AccountingCustomerParty',
            'BuyerCustomerParty',
            'SellerSupplierParty',
            'TaxRepresentativeParty',
        ]
        node_tag = './/%(cac)s'
        idx = 0
        for fn in find_nodes:
            ctag = node_tag + fn
            cnode = parent_node.find(ctag % ns)
            if not cnode or cnode is None:
                break
            idx = parent_node.getchildren().index(cnode)
        delivery = etree.Element(ns['cac'] + 'Delivery')
        delivery_date = etree.SubElement(  # BT-72
            delivery, ns['cbc'] + 'ActualDeliveryDate')
        delivery_date.text = fields.Date.to_string(self.date_delivery)
        parent_node.insert(idx + 1, delivery)

    def _ubl_set_note_l10n_hr(self, parent_node, ns):
        """
        Ovdje ide sve čega nema u drugim shemama:
        - Oznaka operatera
        - Mjesto izdavanja
        - Vrijeme izdavanja ( iako ga imam i regularno, HT i HP imaju u dokumentaciji)!
        - Primjena postupka oporezivanja prema naplaćenoj naknadi
        - Na računu obračunavamo zatezne kamate ukoliko račun nije plaćen u roku

        kodovi za označavanje note elementa (peppol):
        https://service.unece.org/trade/untdid/d99a/uncl/uncl4451.htm
        """
        # TODO: Primjena postupka oporezivanja prema naplaćenoj naknadi
        # < cbc:Note > Primjena postupka oporezivanja prema naplaćenoj naknadi < / cbc:Note >
        # < cbc:Note > Na računu obračunavamo zatezne kamate ukoliko račun nije plaćen u roku < / cbc:Note >
        issue_time = self.get_invoice_issue_time()
        try:
            notes = [  # TODO: separate inheritable method!!
                self.fiskal_user_id.partner_id.name + '#Oznaka operatera',
                issue_time + '#Vrijeme izdavanja',
                self.fiskal_uredjaj_id.prostor_id.mjesto_izdavanja + '#Mjesto izdavanja',
                self.fiskal_responsible_id.partner_id.name + '#Odgovorna osoba',
            ]
        except Exception as E:
            # Specifični slučaj kad nema uredjaj id na računu!
            # za ovo moram smisliti od kud uzeti podatak

            notes = [  # TODO: separate inheritable method!!
                self.fiskal_user_id.partner_id.name + '#Oznaka operatera#',
                issue_time + '#Vrijeme izdavanja#',
                self.fiskal_responsible_id.partner_id.name + '#Odgovorna osoba',
            ]


        inv_tc = parent_node.find('.//%(cbc)sInvoiceTypeCode' % ns)
        idx = parent_node.getchildren().index(inv_tc)

        for note in notes:
            cnode = etree.Element(ns['cbc'] + 'Note')
            cnode.text = note
            parent_node.insert(idx + 1, cnode)

    def _ubl_create_extension(self, extensions, ns):
        """
        :param extensions: extensions element
        :param ns: namespace dict
        :return: create extension subelement
        """
        return etree.SubElement(extensions, ns['ext'] + 'UBLExtension')

    def _ubl_set_extension_element(
            self, root, ns_pref, string, el_text, content=False):
        """
        :param root: current extension element
        :param ns_pref: namespace prefix
        :param string: element name
        :param el_text: element text
        :param content: element content
        """
        if content:
            tmp = etree.SubElement(root, ns_pref[0] + 'ExtensionContent')
            tmp_value = etree.SubElement(tmp, ns_pref[1] + string)
            tmp_value.text = el_text
        else:
            tmp = etree.SubElement(root, ns_pref + string)
            tmp.text = el_text

    def _ubl_set_l10n_hr_extensions(self, parent_node, ns):
        """
        Croatia specific extensions
        """
        extensions = parent_node.findall(ns['ext'] + 'UBLExtensions')
        extensions = extensions and extensions[0] or False
        if not extensions:
            ext = etree.Element(ns['ext'] + 'UBLExtensions')
            parent_node.insert(0, ext)
            extensions = parent_node.findall(ns['ext'] + 'UBLExtensions')[0]

        if not self.uredjaj_id.prostor_id.naselje:
            raise Warning(_('Molimo upišite naselje u proslovni prostor %s' %\
                            self.uredjaj_id.prostor_id.name))

        extension_list = [
            [(ns['cbc'], 'ID', 'HRINVOICE1'),
             (ns['cbc'], 'Name', 'InvoiceIssuePlaceData'),
             (ns['ext'], 'ExtensionAgencyID', 'MINGORP'),
             (ns['ext'], 'ExtensionAgencyName', 'MINGORP'),
             (ns['ext'], 'ExtensionURI', 'urn:invoice:hr:issueplace'),
             (ns['ext'], 'ExtensionReasonCode', 'MandatoryField'),
             (ns['ext'], 'ExtensionReason',
              u'Mjesto izdavanja računa prema Pravilniku o PDV-u'),
             ((ns['ext'], ns['exthr']), 'InvoiceIssuePlace', self.uredjaj_id.prostor_id.naselje, True)
             ],
            [(ns['cbc'], 'ID', 'HRINVOICE1'),
             (ns['cbc'], 'Name', 'InvoiceIssuerData'),
             (ns['ext'], 'ExtensionAgencyID', 'FINA'),
             (ns['ext'], 'ExtensionAgencyName', 'FINA'),
             (ns['ext'], 'ExtensionAgencyURI', 'FINA'),
             (ns['ext'], 'ExtensionURI', 'urn:invoice:hr:issuer'),
             (ns['ext'], 'ExtensionReasonCode', 'MandatoryField'),
             (ns['ext'], 'ExtensionReason',
              u'Podaci o izdavatelju prema Zakonu o trgovackim drustvima'),
             ((ns['ext'], ns['exthr']), 'InvoiceIssuer', self.company_id.eracun_memorandum, True)
             ],
            [(ns['cbc'], 'ID', 'HRINVOICE1'),
             (ns['cbc'], 'Name', 'IssuerLogoData'),
             (ns['ext'], 'ExtensionAgencyID', 'FINA'),
             (ns['ext'], 'ExtensionAgencyName', 'FINA'),
             (ns['ext'], 'ExtensionAgencyURI', 'FINA'),
             (ns['ext'], 'ExtensionURI', 'urn:invoice:hr:issuerlogo'),
             (ns['ext'], 'ExtensionReasonCode', 'OptionalField'),
             (ns['ext'], 'ExtensionReason', u'BASE64 logotipa tvrtke'),
             ((ns['ext'], ns['exthr']), 'IssuerLogo', self.company_id.logo, True)
             ]
        ]
        for extension in extension_list:
            ext_obj = self._ubl_create_extension(extensions, ns)
            for ee in extension:
                self._ubl_set_extension_element(
                    ext_obj, ee[0], ee[1], ee[2], len(ee) == 4)
            extensions.append(ext_obj)

    def get_cleanup_dict(self):
        res = {
            # SUPPLIER
            './/%(cac)sAccountingSupplierParty/%(cac)sParty':
                ['%(cbc)sWebsiteURI',                            # [UBL-CR-143]
                 '%(cac)sLanguage'                               # [UBL-CR-146]
                 ],
            './/%(cac)sAccountingSupplierParty/%(cac)sParty/'
               '%(cac)sPostalAddress/%(cac)sCountry':
                ['%(cbc)sName'                                   # [UBL-CR-166]
                 ],
            './/%(cac)sAccountingSupplierParty/%(cac)sParty/'
               '%(cac)sPartyTaxScheme':
                ['%(cbc)sRegistrationName'                       # [UBL-CR-166]
                 ],
            './/%(cac)sAccountingSupplierParty/%(cac)sParty/'
               '%(cac)sPartyLegalEntity': [
                '%(cac)sRegistrationAddress'],                  # [UBL-CR-185]
            './/%(cac)sAccountingSupplierParty/%(cac)sParty/'
               '%(cac)sContact': [
                '%(cbc)sTelefax'],                              # [UBL-CR-190]
            # CUSTOMER
            './/%(cac)sAccountingCustomerParty': [
                '%(cbc)sSupplierAssignedAccountID'],            # [UBL-CR-202]
            './/%(cac)sAccountingCustomerParty/%(cac)sParty': [
                '%(cac)sLanguage'],                             # [UBL-CR-209]
            './/%(cac)sAccountingCustomerParty/%(cac)sParty/'
                '%(cac)sPostalAddress/%(cac)sCountry': [
                '%(cbc)sName'],                                 # [UBL-CR-229]
            './/%(cac)sAccountingCustomerParty/%(cac)sParty/'
                '%(cac)sPartyTaxScheme': [
                '%(cbc)sRegistrationName'],                     # [UBL-CR-232]
            './/%(cac)sAccountingCustomerParty/%(cac)sParty/'
               '%(cac)sPartyLegalEntity': [
                '%(cac)sRegistrationAddress'],                  # [UBL-CR-249]
            # PAYMENT MEANS
            './/%(cac)sPaymentMeans': [
                '%(cbc)sPaymentChannelCode'],                   # [UBL-CR-413]
            './/%(cac)sPaymentMeans/%(cac)sPayeeFinancialAccount/'
               '%(cac)sFinancialInstitutionBranch': [
              '%(cac)sFinancialInstitution'],                   # [UBL-CR-664]
            # TAX TOTAL
            # TODO [UBL-CR-412]-A UBL invoice should not include the PaymentMeans PaymentDueDate
        }
        return res

    def _ubl_cleanup_hrinvoice1(self, parent_node, ns):
        remove_nodes = self.get_cleanup_dict()

        updates = [
            {'key': './/',  # i customer i supplier
             'val': ['%(cac)sPartyTaxScheme', '%(cac)sContact']},
            # {'key': './/%(cac)sAccountingCustomerParty/%(cac)sParty',
            #  'val': '%(cac)sPartyLegalEntity'},
            {'key': './/%(cac)sTaxTotal/%(cac)sTaxSubtotal',
             'val': ['./%(cbc)sPercent']},
            {'key': './/%(cac)sInvoiceLine/%(cac)sItem',
             'val': ['%(cac)sClassifiedTaxCategory']
            }
        ]
        for upd in updates:
            if remove_nodes.get(upd['key']):
                remove_nodes[upd['key']].append(upd['val'])
            else:
                remove_nodes.update({upd['key']: upd['val']})

        self._ubl_cleanup_nodes(parent_node, ns, remove_nodes)

    def _ubl_cleanup_en19631(self, parent_node, ns):
        '''
        Some nodes are not needed ,so cleanup will try to reduce warning count
        for peppol validator
        '''
        # samo za EN16931 ovo!
        # version = parent_node.find(ns['cbc'] + 'UBLVersionID')
        # parent_node.remove(version)  # [UBL-CR-002]
        remove_nodes = self.get_cleanup_dict()
        # BOLE: ipak cu ga ostaviti?
        remove_nodes.update({
            './/%(cac)sInvoiceLine': ['.//%(cac)sTaxTotal']
        })
        self._ubl_cleanup_nodes(parent_node, ns, remove_nodes)

    @api.multi
    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        """
        inherit preko account_invoice-ubl._ubl_add_tax_total

        """
        line_taxes, inv_taxes = False, False
        try:
            super(AccountInvoice, self)._ubl_add_tax_total(
                xml_root=xml_root, ns=ns, version=version)

        except Warning as W:
            if "Missing UNECE" in W.name:
                raise W
            # PPO nema base code pa pukne error
            # dodao je TaxTotal/TaxAmount = 0.0
            # a sada dodati i ostalo

            inv_taxes = [it for it in self.tax_line_ids]
            line_taxes = [il.invoice_line_tax_ids for il in self.invoice_line]
            if set(inv_taxes) == set(line_taxes):
                # isti porezi na stavci i dokumenti
                # ipak nesto nije u redu...
                raise W

            if len(set(line_taxes)) != 1:
                # na stavkama računa mora biti samo jedna vrsta poreza
                # ako ih je više ne hendlam spiku
                # dalje uzimam poreza sa stavke i stavljam ga na račun
                # jer pretpostavljam da je na stavci jedan porez,
                # a na dokumentu childovi od poreza sa stavke
                raise Warning(
                    _('Confusung taxex on document, ask consultant for help! '
                      'User should not see this warning'))
            tax_total_node = xml_root.find('.//%(cac)sTaxTotal' % ns)
            tax_amount_node = tax_total_node.find('.//%(cbc)sTaxAmount' % ns)
            tax_amount = float(tax_amount_node.text)
            if tax_amount != 0.0:
                # popravljam samo ako je iznos poreza 0.0!!!
                raise W

        if not line_taxes:
            return
        self.ensure_one()
        cur_name = self.currency_id.name
        # BOLE: ali pazi na currency!
        base_amount = self.amount_total
        tax = line_taxes[0]
        self._ubl_add_tax_subtotal(
            taxable_amount=base_amount, tax_amount=0.0, tax=tax,
            currency_code=cur_name, parent_node=tax_total_node,
            ns=ns, version=version)

    @api.model
    def _ubl_add_tax_category(self, tax, parent_node, ns,
                              node_name='TaxCategory', version='2.1'):
        super(AccountInvoice, self)._ubl_add_tax_category(
            tax, parent_node, ns, node_name=node_name, version=version)
        tax_percent_node = parent_node.find('.//%(cbc)sPercent' % ns)

        ns['node_name'] = node_name
        categ_node = parent_node.find('.//%(cac)s%(node_name)s' % ns)
        categ_percent_node = categ_node.find('.//%(cbc)sPercent' % ns)
        if float(tax_percent_node.text) == 100.0:
            # GLUPI SLUČAJ U IVETI krive postavke!
            # PPO je bio postavljen za knjiženje kao ulazni račun
            # glavni porez je imao 100% i imao je dva subelementa
            # pa ovdje pokrije taj slučaj...
            # nije ovo dobro ali ostavljam za ako iakd zatreba i samo za ivetu!
            if 'iveta' not in self._cr.dbname.lower():
                _logger.debug("Ušao u metodu namjenjenu samo IVETA bazama a nije trebao!")
                return
            try:
                parent_node.remove(tax_percent_node)
            except:
                pass
            if float(categ_percent_node.text) == 100.0:
                categ_percent_node.text = '0.0'
            reason_node = etree.Element(ns['cbc'] + 'TaxExemptionReason')
            reason = '\n'.join([r.description for r in
                                tax.base_code_id.tax_exemption_ids])
            if not reason:
                raise Warning(_('No tax exemtipn reason set on %s, (%s)' %
                                (tax.name, tax.base_code_id.name)))
            reason_node.text = reason
            # ID, name, percent... reason!
            categ_node.insert(3, reason_node)

        if float(tax_percent_node.text) == 0.0:
            # e ovako treba biti!!!
            # i ako je tax percent 0 mora postojati i exemption reason
            reason_node = etree.Element(ns['cbc'] + 'TaxExemptionReason')
            reason = '\n'.join([r.description for r in
                                tax.base_code_id.tax_exemption_ids])

            if not reason:
                raise Warning(_('No tax exemption reason set on %s, (%s)' %
                                (tax.name, tax.base_code_id.name)))
            reason_node.text = reason
            # ID, name, percent... reason!
            categ_node.insert(3, reason_node)

    @api.multi
    def _ubl_cleanup_nodes(self, parent_node, ns, remove_nodes):
        """
        :param remove_nodes: list of nodes to clean up.
        :return:
        """
        for path in remove_nodes.keys():
            try:
                parent = parent_node.findall(path % ns)
            except Exception as E:
                print(repr(E))
                parent = False
            if not parent:
                _logger.debug("XML_Cleanup-parent not found: %s" % path)
                continue
            for par_elem in parent:
                for key in remove_nodes[path]:
                    if '%' in key:
                        key = key % ns
                    remove_elem = par_elem.findall(key)
                    for rm in remove_elem:
                        try:
                            par_elem.remove(rm)
                        except:
                            _logger.debug(
                                'XML Cleanup : \n%s \nKey not found: %s' % (
                                path, key))
        # for line in parent_node.findall('.//%(cac)sInvoiceLine' % ns):
        #     rm = line.findall('%(cac)sTaxTotal' % ns)
        #     for r in rm:
        #         line.remove(r)

    @api.model  # OK
    def _ubl_add_party_identification(
            self, commercial_partner, parent_node, ns, version='2.1'):
        if self.company_id.croatia and commercial_partner.country_id.code == 'HR':
            # Original method uses SchemaName,
            # for Croatia we need endpointID and schemaID
            endpoint = etree.SubElement(
                parent_node, ns['cbc'] + 'EndpointID', schemeID='9934')
            if not commercial_partner.vat:
                raise Warning(
                    _("Partner: %s - VAT required") % commercial_partner.name)
            endpoint.text = commercial_partner.vat.\
                                replace('HR', '').\
                                replace(' ', '')

            party_ident = etree.SubElement(parent_node, ns['cac'] + 'PartyIdentification')
            party_ID = etree.SubElement(party_ident, ns['cbc'] + 'ID')
            party_ID.text = '9934:' + commercial_partner.vat.\
                                replace('HR', '').\
                                replace(' ', '')
        else:
            # Inserts only SchemaName
            super(AccountInvoice, self)._ubl_add_party_identification(
                commercial_partner, parent_node, ns, version=version)

    @api.model  # OK
    def _ubl_add_customer_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_customer_party(
            partner=partner, company=company, node_name=node_name,
            parent_node=parent_node, ns=ns, version=version)
        if self.company_id.croatia:
            # if self.env.context.get('schema') == 'EN19631' i HRINVOICE1:
            legal = parent_node.find(ns['cac'] + 'PartyLegalEntity')
            if not legal:
                ac_party = parent_node.find(ns['cac'] + 'AccountingCustomerParty')
                party = ac_party.find(ns['cac'] + 'Party')
                contact = party.find(ns['cac'] + 'Contact')
                party.remove(contact)  # easy way to sort them properly!
                self._ubl_add_party_legal_entity(
                    partner, party, ns, version=version)
                #party.append(contact)
            else:
                pass

    @api.model
    def _ubl_add_address(
            self, partner, node_name, parent_node, ns, version='2.1'):
        super(AccountInvoice, self)._ubl_add_address(
            partner, node_name, parent_node, ns, version=version)
        # inherit of original method is hard (abstract class)
        # try inherit base.ubl in v12!!
        if node_name == 'PostalAddress':
            pa_node = parent_node.find(ns['cac'] + 'PostalAddress')
            country_node = pa_node.find(ns['cac'] + 'Country')
            addres_line = etree.Element(ns['cac'] + 'AddressLine')
            add_line = etree.SubElement(addres_line, ns['cbc'] + 'Line')
            line_text = ' '.join([
                partner.street, ',',
                partner.zip, partner.city])
            add_line.text = line_text
            pa_node.insert(pa_node.index(country_node), addres_line)

    @api.model
    def _ubl_add_payment_means(
            self, partner_bank, payment_mode, date_due, parent_node, ns,
            payment_identifier=None, version='2.1'):
        """
        inherit from base_ubl_payment, reason: if payment mode is not selected,
        default payment mode is 31, but for croatia we will default it to 42, IBAN
        and use it no matter if it is set or not...

        Specified my moj eRacun, but seems like it works for all...
        """
        super(AccountInvoice, self)._ubl_add_payment_means(
            partner_bank, payment_mode, date_due, parent_node, ns,
            payment_identifier=payment_identifier, version=version)
        if self.company_id.croatia:
            pm_node = parent_node.find(ns['cac'] + 'PaymentMeans')
            pm_code = pm_node.find(ns['cbc'] + 'PaymentMeansCode')
            if pm_code.text != '42':
                # TODO: mozda i ne hardcoded?
                pm_code.text = '42'
            idx = pm_node.index(pm_code)
            due_date_node = pm_node.find(ns['cbc'] + 'PaymentDueDate')
            if due_date_node is not None:
                # samo provjera dali postoji!
                idx = pm_node.index(due_date_node)
            else:
                if self.date_due:
                    # TODO : ipak dodaj date due, makar nemoguce...
                    pass

            pm_chanel_code = pm_node.find(ns['cbc'] + 'PaymentChannelCode')
            if pm_chanel_code is None:
                pm_chanel_code = etree.Element(ns['cbc'] + 'PaymentChannelCode',
                                           listAgencyName="CEN/BII")
                pm_chanel_code.text = 'IBAN'
                pm_node.insert(idx + 1, pm_chanel_code)
                idx += 1
            else:
                if pm_chanel_code.text != 'IBAN':
                    pm_chanel_code.text = 'IBAN'
                idx = pm_node.index(pm_chanel_code)

            model_pnbr = self.reference.split(' ')
            instruction_node = pm_node.find(ns['cbc'] + 'InstructionID')
            if instruction_node is None:
                # TODO: samo numeric ? poziv na broj ?
                instruction_node = etree.Element(ns['cbc'] + 'InstructionID')
                instruction_node.text = (self.reference.startswith('HR') or \
                                    len(model_pnbr) > 1) and \
                                    model_pnbr[1] or model_pnbr[0]
                pm_node.insert(idx + 1, instruction_node)
                idx += 1
            else:
                idx = pm_node.index(instruction_node)

            instruction_note = pm_node.find(ns['cbc'] + 'InstructionNote')
            if instruction_note is None:
                instruction_note = etree.Element(ns['cbc'] + 'InstructionNote')
                instruction_note.text = u'Plaćanje po računu'
                pm_node.insert(idx + 1, instruction_note)
                idx += 1
            else:
                idx = pm_node.index(instruction_note)

            model_node = pm_node.find(ns['cbc'] + 'PaymentID')
            if model_node is None:
                model_node = etree.Element(ns['cbc'] + 'PaymentID')
                model_node.text = model_pnbr[0]
                pm_node.insert(idx +1, model_node)

    @api.multi
    def check_digits(self, parent_node, ns):
        """
        PEPPOL validator accepts up to 2 decimal digits,
        accounting precision can be set to 3 or more digits,
        so wee need this ugly hack to reduce digits and round amounts
        """
        prec = self.env['decimal.precision'].precision_get('Account')
        if prec == 2:
            return parent_node
        for item in parent_node:
            print(item.tag, item.text)   # BOLE : remove me!
            tag = item.tag.split('}')[1]
            if tag not in ['TaxTotal', 'LegalMonetaryTotal', 'InvoiceLine']:
                continue
            if tag == 'TaxTotal':
                self._digits_correct_tax_total(item, ns)
            elif tag == 'LegalMonetaryTotal':
                for lmt in item:
                    lmt.text = self._digits_correct_decimal(lmt.text)
            elif tag == 'InvoiceLine':
                LineExtensionAmount = item.find(ns['cbc'] + 'LineExtensionAmount')
                LineExtensionAmount.text = self._digits_correct_decimal(
                    LineExtensionAmount.text)
                LineTaxTotal = item.find(ns['cac'] + 'TaxTotal')
                if LineTaxTotal:
                    self._digits_correct_tax_total(LineTaxTotal, ns)

    def _digits_correct_tax_total(self, node, ns):
        TaxAmount = node.find(ns['cbc'] + 'TaxAmount')
        TaxAmount.text = self._digits_correct_decimal(TaxAmount.text)
        TaxSubtotal = node.find(ns['cac'] + 'TaxSubtotal')
        if TaxSubtotal:
            TaxableAmount = TaxSubtotal.find(ns['cbc'] + 'TaxableAmount')
            TaxableAmount.text = self._digits_correct_decimal(
                TaxableAmount.text)
            SubTaxAmount = TaxSubtotal.find(ns['cbc'] + 'TaxAmount')
            SubTaxAmount.text = self._digits_correct_decimal(
                SubTaxAmount.text)

    def _digits_correct_decimal(self, value):
        try:
            val = float(value)
        except:
            return value

        return str(round(val, 2))

    def check_invoice_line_taxes(self, parent_node, ns):
        # BOLE: nemogu se hvatati na name, greške u prevodima
        # taxes = [l.display_name for l in self.tax_line]
        # for line in parent_node.findall(ns['cac'] + 'InvoiceLine'):
        #     litem = line.find(ns['cac'] + 'Item')
        #     for tc in litem.findall(ns['cac'] + 'ClassifiedTaxCategory'):
        #         tc_name = tc.find(ns['cbc'] + 'Name')
        #         if tc_name.text not in taxes:
        #             litem.remove(tc)
        return



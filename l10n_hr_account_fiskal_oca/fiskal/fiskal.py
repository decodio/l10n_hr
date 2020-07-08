# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from uuid import uuid4
from suds.client import Client

from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA, MD5
from Crypto.PublicKey import RSA
from . import soap

def generate_zki(zki_datalist, key_str):
    '''
    as function so it can be called to ckeck generaqted ZKI without
    instanciating Fiskalizacija class
    parameteras are all strings with actual document data
    zki_datalist:
      invoice: oib, datum_vrijeme, br_racuna, oznaka_pp,
                 oznaka_nu, ukupno_iznos
      TODO: PrateciDokumenti!!! broj dokumenta nije fiskalni broj!!!
    :return:
    '''
    sign_string = ''.join(zki_datalist).encode('utf-8')
    key = RSA.importKey(key_str)
    h = SHA.new(sign_string)
    signer = PKCS1_v1_5.new(key)
    signature = signer.sign(h)
    md5h = MD5.new()
    md5h.update(signature)
    return md5h.hexdigest()

def format_decimal(decimal):
    '''Formats float for Fiskal communication'''
    return '%.2f' % decimal

def get_uuid():
    '''recomended for fiscalization is UUID4'''
    return uuid4().hex


class Fiskalizacija():
    """
    Helper class for fiscalization requirement in Croatia
    - generates suds object
    """

    def __init__(self, fiskal_data, odoo_object, **other):
        """

        :param fiskal_data: dict containing basic fiscalization data
                keys: key, cert, wsdl, ca_path, ca_list, url, test...

        :param odoo_object: instance of odoo object for further processing
        :param other: optional variables
        """

        self.default_ns = 'fis'
        self.key_path = fiskal_data['key']
        self.cert_path = fiskal_data['cert']
        self.odoo_object = odoo_object

        xmldsig_plugin = soap.XmlDSigMessagePlugin(fiskal_data)
        xml_message_log_plugin = soap.XmlMessageLogPlugin()
        suds_options = {
            'cache': None,
            'prettyxml': True,
            'timeout': 90,
            'plugins': [xmldsig_plugin, xml_message_log_plugin],
        }

        if fiskal_data.get('test', False) == True:
            suds_options['location'] = 'https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest'

        self.client = Client(fiskal_data['wsdl'], **suds_options)
        self.client.options.transport = soap.CustomHttpTransport(
                                        ca_certs=fiskal_data['ca_path'])
        self.log = xml_message_log_plugin


    def create(self, name):
        '''
        Create instances of suds objects and types defined in WSDL
        '''

        if ':' in name:
            wtype = self.client.factory.create(name)
        else:
            wtype = self.client.factory.create(
                                    "%s:%s" % (self.default_ns, name))
        return wtype

    def generate_header(self):
        '''
        Generate header for Fiskal CIS request
        : DatumVrijeme : datestring formatted as :
        '''

        zaglavlje = self.create('Zaglavlje')
        zaglavlje.IdPoruke = uuid4().urn.split(':')[-1]
        company = self.odoo_object._name == 'res.company' and \
                  self.odoo_object or self.odoo_object.company_id
        datum_vrijeme = company.get_l10n_hr_time_formatted()
        # dohvaćam vrijeme slanja poruke uvjek iznova!
        zaglavlje.DatumVrijeme = datum_vrijeme['datum_vrijeme']
        return zaglavlje

    def send(self, method_name, data, nosend=False, raw_response=False):
        '''Send request'''

        method = getattr(self.client.service, method_name)
        if not method:
            raise ValueError('Unknown method: %s' % method_name)

        if method_name == 'echo':
            response = method(data)
        else:
            header = self.generate_header()

            if hasattr(data, 'OznakaZatvaranja') \
                    and not data.OznakaZatvaranja.value:
                # LEGACY from WSDL 1.0 - 1.2 not needed!
                del data.OznakaZatvaranja

            if nosend:
                pre_nosend = self.client.options.nosend
                self.client.options.nosend = True

            response = method(header, data)

            if nosend:
                self.client.options.nosend = pre_nosend
                response = response.envelope
            if not raw_response:
                response = self.process_response(header, response)

        return response

    def echo(self, msg):
        '''Send and verify Fiskal CIS echo request'''

        reply = self.client.service.echo(msg)
        if reply == msg:
            res = "Echo test successful with reply: %s" % (reply,)
        else:
            res = "Echo test failed with reply: %s" % (reply,)
        return res

    def process_response(self, request_hdr, response):
        '''Process response and return response data in dictionary'''

        response = dict(response)

        # if 'Zaglavlje' not in response:
        #     raise Exception('No header in response')
        # if 'IdPoruke' not in response['Zaglavlje']:
        #     raise Exception('No header id in response')
        # if str(request_hdr.IdPoruke) != str(response['Zaglavlje']['IdPoruke']):
        #     raise Exception('Request and response header id do not match')
        # del response['Zaglavlje']
        response['Success'] = True
        if 'Greske' in response:
            errors = []
            for err in response['Greske']:
                errors.append(dict(err[1][0]))
            raise Exception(errors)

        if 'Signature' in response:
            del response['Signature']



        return response

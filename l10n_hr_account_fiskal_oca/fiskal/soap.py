# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from lxml import etree
import ssl
import http.client as httplib
import urllib.request as urllib2
from backports.ssl_match_hostname import match_hostname
from logging import getLogger
import base64
from OpenSSL import crypto
from signxml import XMLSigner, XMLVerifier

from suds.sax.parser import Parser
from suds.sax.element import Element
from suds.plugin import MessagePlugin
from suds.transport.https import HttpTransport
from suds.bindings.binding import envns as soap_envns

_logger = getLogger(__name__)


class XmlDSigMessagePlugin(MessagePlugin):
    """
    Suds message plugin for generating and verifying XML signatures
    """

    def __init__(self, fiskal_data):
        self.key_path = fiskal_data.get('key')
        self.cert_path = fiskal_data.get('cert')

        self.ca_path = fiskal_data.get('ca_path')
        self.cis_ca_paths = fiskal_data.get('ca_list')
        self.cis_cert_cn = fiskal_data.get('url')

    def sending(self, context):
        '''Signs XML before sending'''

        envelope_element = Parser().parse(string=context.envelope).root()
        body = envelope_element.getChild('Body')
        body.setPrefix('SOAP-ENV')
        envelope_element.clearPrefix('ns0')
        envelope_element.clearPrefix('ns1')
        payload = body[0]

        qname = payload.qname()
        if 'Echo' in qname:
            # Echo ne potpisujemo
            return

        # clear double soap prefix, and generated ns for fiskal
        payload.setPrefix('tns', "http://www.apis-it.hr/fin/2012/types/f73")
        for item in payload.branch():
            if 'Signature' in item.name:
                continue
            item.setPrefix('tns')
        sig_ns = ("ds", "http://www.w3.org/2000/09/xmldsig#")
        sig = Element('Signature', ns=sig_ns)
        sig.set('Id', 'placeholder')
        sig.setText('')
        payload.append(sig)
        payload.applyns(('tns', "http://www.apis-it.hr/fin/2012/types/f73"))
        reference_uri = qname.replace('ns1:', '').replace('ns0:', '')
        envelope_element.clearPrefix('ns1')  # stari f73!

        payload.set('Id', reference_uri)
        payload.refitPrefixes()  # push ds up xml tree

        signer = XMLSigner(
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
        )
        cert = open(self.cert_path).read()
        key = open(self.key_path).read()

        data = etree.fromstring(payload.plain())
        signed_payload = signer.sign(
            data=data, key=key, cert=cert,
            reference_uri=reference_uri
        )

        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        cert_issuer = certificate.get_issuer()
        issuer_name = ','.join(filter(None, [
            cert_issuer.CN and "CN=" + cert_issuer.CN,
            cert_issuer.OU and "OU=" + cert_issuer.OU,
            cert_issuer.O and "O=" + cert_issuer.O,
            cert_issuer.C and "C=" + cert_issuer.C])
                               )
        sig_data = signed_payload.find(".//{" + sig_ns[1] + "}Signature")
        x509_data = sig_data.find(".//{" + sig_ns[1] + "}X509Data")
        isuerserial = etree.SubElement(x509_data, "{%s}X509IssuerSerial" % sig_ns[1])
        name = etree.SubElement(isuerserial, "{%s}X509IssuerName" % sig_ns[1])
        name.text = issuer_name
        serial = etree.SubElement(isuerserial, "{%s}X509SerialNumber" % sig_ns[1])
        serial.text = '{:d}'.format(certificate.get_serial_number())

        sp = etree.tostring(signed_payload)
        signed_data = Parser().parse(string=sp).root()
        #signed_data.updatePrefix('tns', '"http://www.apis-it.hr/fin/2012/types/f73"')

        body.replaceChild(payload, signed_data)
        context.envelope = envelope_element.plain().encode('utf-8')

    def received(self, context):
        '''Verifies XML signature of received message'''

        def _extract_keyinfo_cert(payload):
            '''Extract the signing certificate from KeyInfo.'''

            cert_der = payload.getChild('Signature')
            cert_der = cert_der.getChild('KeyInfo')
            cert_der = cert_der.getChild('X509Data')
            cert_der = cert_der.getChild('X509Certificate').getText().strip()
            cert_der = base64.b64decode(cert_der)
            return cert_der

        def _verify_cn(cert, cis_cert_cn):
            '''Verify signature certificate common name'''

            common_name = cert.get_subject().commonName

            if common_name != cis_cert_cn:
                raise Exception('Invalid certificate common name in response: '
                                '%s != %s' % (cis_cert_cn, common_name))

        def _fault(code, msg):
            '''Generate fault XML'''

            faultcode = Element('faultcode').setText(code)
            faultstring = Element('faultstring').setText(msg)
            fault = Element('Fault').append([faultcode, faultstring])
            body = Element('Body').append(fault)
            envelope = Element('Envelope', ns=soap_envns)
            envelope.append(body)
            envelope.refitPrefixes()

            return envelope.str()


        valid_signature = False
        # return  # TMP!
        try:
            if not self.cis_ca_paths:
                raise Exception('Certificate Authority not defined')

            reply_element = Parser().parse(string=context.reply).root()
            body = reply_element.getChild('Body')
            payload = body[0]
            qname = payload.qname()
            cert_der = _extract_keyinfo_cert(payload)
            cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_der)

            if 'Echo' in qname or 'Fault' in qname:
                _logger.warning('Not verifying certificate for qname: %s', qname)
                return

            if self.cis_cert_cn:
                _verify_cn(cert, self.cis_cert_cn)
            else:
                _logger.warning('CIS certificate common name not configured')

            verifier = XMLVerifier()
            payload_string = etree.fromstring(payload.plain())
            valid_signature = verifier.verify(payload_string, x509_cert=cert)

        except Exception as exc:
            _logger.exception('%s: %s', exc, context.reply)
            context.reply = _fault('Client',
                                   'Invalid response signature: %s' % exc)
        else:
            if not valid_signature:
                _logger.error('Invalid response signature: %s', context.reply)
                context.reply = _fault('Client',
                                       'Invalid response signature')


class CustomHttpTransport(HttpTransport):
    '''
    Class just for adding CustomHTTPErrorProcessor to urllib2
    handlers list
    '''

    def __init__(self, **kwargs):
        if 'ca_certs' in kwargs:
            self.ca_certs = kwargs['ca_certs']
            del kwargs['ca_certs']

        HttpTransport.__init__(self, **kwargs)


    def u2handlers(self):
        '''Adds CustomHTTPErrorProcessor to handlers list'''

        handlers = HttpTransport.u2handlers(self)
        handlers.append(VerifiedHTTPSHandler(ca_certs=self.ca_certs))
        handlers.append(CustomHTTPErrorProcessor())
        return handlers


class CustomHTTPErrorProcessor(urllib2.BaseHandler):
    '''
    Error processor for urllib2 which returns response data (i.e. does not
    raise exception) on HTTP error code 500 (Internal Server Error) because
    Fiskal CIS returns HTTP 500 on all errors
    '''

    def http_error_500(self, request, response, code, msg, hdrs):
        '''Return response data on HTTP error code 500'''

        return response


class CertValidatingHTTPSConnection(httplib.HTTPConnection):
    '''
    HTTP connection class with SSL hostname verification
    https://gist.github.com/schlamar/2993700
    '''

    default_port = httplib.HTTPS_PORT

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 ca_certs=None, strict=None, **kwargs):
        if 'timeout' in kwargs:
            del kwargs['timeout']
        httplib.HTTPConnection.__init__(self, host, port, strict, **kwargs)
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_certs = ca_certs
        if self.ca_certs:
            self.cert_reqs = ssl.CERT_REQUIRED
        else:
            self.cert_reqs = ssl.CERT_NONE

    def connect(self):
        httplib.HTTPConnection.connect(self)
        self.sock = ssl.wrap_socket(self.sock, keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    cert_reqs=self.cert_reqs,
                                    ca_certs=self.ca_certs)
        if self.cert_reqs & ssl.CERT_REQUIRED:
            cert = self.sock.getpeercert()
            hostname = self.host.split(':', 0)[0]
            # Fix for invalid subjectAltName in cis.porezna-uprava.hr certificate
            if 'subjectAltName' in cert:
                del cert['subjectAltName']
            match_hostname(cert, hostname)


class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    '''
    urllib2 handler class which verifies SSL hostname
    https://gist.github.com/schlamar/2993700
    '''

    def __init__(self, **kwargs):
        urllib2.HTTPSHandler.__init__(self)
        self._connection_args = kwargs

    def https_open(self, req):
        def http_class_wrapper(host, **kwargs):
            full_kwargs = dict(self._connection_args)
            full_kwargs.update(kwargs)
            return CertValidatingHTTPSConnection(host, **full_kwargs)

        return self.do_open(http_class_wrapper, req)


class XmlMessageLogPlugin(MessagePlugin):
    '''
    Suds message plugin for logging request and response XML body
    '''

    def __init__(self, sending_log=True, received_log=True):
        self.sending_log = sending_log
        self.received_log = received_log

    def sending(self, context):
        if self.sending_log:
            self.sending_log = context.envelope

    def received(self, context):
        if self.received_log:
            self.received_log = context.reply

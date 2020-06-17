# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
from datetime import datetime
from OpenSSL import crypto as SSLCrypto
# from M2Crypto import BIO, Rand, SMIME, EVP, RSA, X509, ASN1
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CryptoCertificate(models.Model):
    _name = "crypto.certificate"
    _description = "Cryptography certificates"

    @api.depends('state', 'csr', 'crt')
    def _get_status(self):
        for cer in self:
            if cer.type == 'personal_gen':
                if not cer.pairkey_id:
                    cer.status = 'empty'
                else:
                    cer.status = 'key-' + str(cer.pairkey_id.state)
            if 'server' in cer.type:
                if 'gen' in cer.type:
                    if not cer.csr and not cer.crt:
                        cer.status = 'empty'
                    elif cer.csr and not cer.crt:
                        try:
                            req = cer.get_request()[0]
                            pkey = req.get_pubkey()
                            if req.verify(pkey):
                                cer.status = 'valid_request'
                            else:
                                cer.status = 'invalid_request'
                        except:
                            cer.status = 'invalid_request'
                    elif cer.csr and cer.crt:
                        req = cer.get_request()[0]
                        pkey = req.get_pubkey()
                        try:
                            crt = cer.get_certificate()[0]
                            cer.status = 'valid_certificate' if crt.verify() and crt.verify(pkey) else 'invalid_certificate'
                        except:
                            cer.status = 'invalid_certificate'
                elif 'rec' in cer.type:
                    if not cer.cert_file:
                        cer.status = 'no_cert_file'
                        continue
                    if not cer.csr:
                        cer.status = 'cert_not_converted'
                        continue
                    #TODO: more checks?, but it can't be converted if something is wrong...
                    cer.status = 'certificate_converted'
            else:
                cer.status = 'unknown'

    @api.one
    @api.depends('csr', 'crt', 'type')
    def _get_usage(self):
        """
        Inherit in other modules to get specific usage
        remebmer to make proper super call!
        """
        for cer in self:
            cer.usage = _('General use')

    # FIELDS
    name = fields.Char(string='Name', size=256)
    usage = fields.Char(
        compute="_get_usage",
        string="Usage", )#store=True
    type = fields.Selection(
        selection=[
            ('server_gen', 'Server - generated'),
            ('server_rec', 'Server - recived (PFX/P12)'),
            ('person_gen', 'Personal - generated'),
            ('person_rec', 'Personal - recieved (PFX/P12)'),
            ('other', 'Other types'),
            ],
        string="Type",
        default='server_rec')

    csr = fields.Text(
        string='Request / Private',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Certificate Sign Request (csr) in PEM format.'
             'or private key from P12/PFX cert',
                      )
    crt = fields.Text(
        string='Certificate / Public',
        readonly=True,
        states={'draft': [('readonly', False)],
                'waiting': [('readonly', False)]},
        help='Certificate (crt) in PEM format.'
             'or certificate from P12/PFX cert',)

    pairkey_id = fields.Many2one('crypto.pairkey', 'Key pair')
    date_expire = fields.Date('Expire date')
    status = fields.Char(
        compute='_get_status',
        string='Status',
        help='Certificate Status')

    cert_file = fields.Binary(
        string="Original cert file")
    cert_file_name = fields.Char(
        string="Name of attachment")
    cert_password = fields.Char(
        string='Password for cert')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waiting', 'Waiting'),
            ('confirmed', 'Confirmed'),
            ('cancel', 'Cancelled'),
        ],
        sring='State',
        readonly=True,
        default="draft",
        help='* The \'Draft\' state is used when a user is creating a new pair key. Warning: everybody can see the key.\
        \n* The \'Waiting\' state is used when a request has send to Certificate Authority and is waiting for response.\
        \n* The \'Confirmed\' state is used when a certificate is valid.\
        \n* The \'Canceled\' state is used when the key is not more used. You cant use this key again.')

    @api.multi
    def unlink(self):
        for cert in self:
            if cert.state == 'confirmed':
                raise UserError(_('Deleting certificate in confirmed state is not allowed!'))

    def _check_valid(self):
        '''
        Inherit in other modules to extend validation conditions
        remeber to call super for proper inheritance
        '''
        state, msg = False, False
        if self.status == 'valid_request' and self.state == 'draft':
            state = 'waiting'
        elif self.status == 'valid' and self.state in ['draft', 'waiting']:
            state = 'confirmed'
        else:
            msg = _('''Perhaps you want to insert an invalid request or certificate,'''
                    '''or you want to approve an invalid certificate with an valid request.''')
        return {'state': state, 'msg': msg}

    def action_validate(self):
        self.ensure_one()
        valid = self._check_valid()
        if valid['state']:
            self.state = valid['state']
        else:
            raise UserError(valid['msg'])

    @api.multi
    def action_cancel(self):
        for cert in self:
            cert.state = 'cancel'

    # @api.one
    # def get_request(self):
    #     """
    #     Return Request object.
    #     """
    #     return self.csr and X509.load_request_string(self.csr.encode('ascii')) or None


    def button_convert_p12(self):
        self.ensure_one()
        if self.cert_file:
            _password = self.cert_password or ''
            try:
                p12 = SSLCrypto.load_pkcs12(base64.decodestring(self.cert_file), _password)
            except:
                raise UserError('Certificate acces error, check password or file type!')

            csr = SSLCrypto.dump_privatekey(SSLCrypto.FILETYPE_PEM, p12.get_privatekey())    # PEM formatted private key
            crt = SSLCrypto.dump_certificate(SSLCrypto.FILETYPE_PEM, p12.get_certificate())  # PEM formatted certificate

            name = p12.get_friendlyname().decode('utf-8')
            curent_cert = p12.get_certificate()
            cert_not_before = curent_cert.get_notBefore().decode('utf-8')
            cert_not_after = curent_cert.get_notAfter().decode('utf-8')
            def convert_date(date):
                try:
                    dt = datetime.strptime(date, "%Y%m%d%H%M%SZ")
                except Exception as E:
                    print(repr(E))
                    return ""
                return dt.strftime("%d.%m.%Y[%H:%M]")

            cert_valid_str = ' - '.join((convert_date(cert_not_before), convert_date(cert_not_after)))

            if not self.name:
                self.name = ' '.join((name, cert_valid_str))
            self.csr = csr or ''
            self.crt = crt or ''
            self.date_expire = datetime.strptime(cert_not_after, "%Y%m%d%H%M%SZ").strftime("%Y-%m-%d")

    # @api.one
    # def get_certificate(self):
    #     """
    #     Return Certificate object.
    #     """
    #     return self.crt and X509.load_cert_string(self.crt.encode('ascii'))

    # @api.one
    # def generate_certificate(self, issuer, ext=None, serial_number=1, version=2,
    #                          date_begin=None, date_end=None, expiration=365):
    #     """
    #     Generate certificate
    #     """
    #
    #     if self.status in ['empty', 'valid_request']:
    #         # Get request data
    #         pk = self.pairkey_id.as_pkey()[0]
    #         req = self.get_request()[0]
    #         if req is None:
    #             raise
    #         sub = req.get_subject()
    #         pkey = req.get_pubkey()
    #         # Building certificate
    #         cert = X509.X509()
    #         cert.set_serial_number(serial_number)
    #         cert.set_version(version)
    #         cert.set_subject(sub)
    #
    #         now = ASN1.ASN1_UTCTIME()
    #         if date_begin is None:
    #             t = long(time.time()) + time.timezone
    #             now.set_time(t)
    #         else:
    #             now.set_datetime(datetime.strptime(date_begin, "%Y-%m-%d"))
    #
    #         nowPlusYear = ASN1.ASN1_UTCTIME()
    #         if date_end is None:
    #             nowPlusYear.set_time(t + 60 * 60 * 24 * expiration)
    #         else:
    #             nowPlusYear.set_datetime(datetime.strptime(date_end, "%Y-%m-%d"))
    #
    #         cert.set_not_before(now)
    #         cert.set_not_after(nowPlusYear)
    #         cert.set_issuer(issuer)
    #         cert.set_pubkey(pkey)
    #         cert.set_pubkey(cert.get_pubkey())
    #         if ext:
    #             cert.add_ext(ext)
    #         cert.sign(pk, 'sha1')
    #         self.write({'crt': cert.as_pem()})

    # #TODO signer here
    # def smime(self, cr, uid, ids, message, context=None):
    #     """
    #     Sign message in SMIME format.
    #     """
    #     r = {}
    #     for cert in self.browse(cr, uid, ids):
    #         #if cert.status == 'valid': # EXTRANGE: Invalid certificates can be used for sign!
    #         if True:
    #             smime = SMIME.SMIME()
    #             ks = BIO.MemoryBuffer(cert.pairkey_id.key.encode('ascii'))
    #             cs = BIO.MemoryBuffer(cert.crt.encode('ascii'))
    #             bf = BIO.MemoryBuffer(str(message))
    #             out = BIO.MemoryBuffer()
    #             try:
    #                 smime.load_key_bio(ks, cs)
    #             except EVP.EVPError:
    #                 raise osv.except_osv(_('Error in Key and Certificate strings !'), _('Please check if private key and certificate are in ASCII PEM format.'))
    #             sbf = smime.sign(bf)
    #             smime.write(out, sbf)
    #             r[cert.id] = out.read()
    #         else:
    #             raise osv.except_osv(_('This certificate is not ready to sign any message !'), _('Please set a certificate to continue. You must send your certification request to a authoritative certificator to get one, or execute a self sign certification'))
    #     return r




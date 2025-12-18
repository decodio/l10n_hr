# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# Copyright 2025 Ecodica d.o.o (https://www.ecodica.eu)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import datetime
from base64 import b64decode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, pkcs12
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
                            cer.status = 'valid_certificate' if crt.verify() and crt.verify(
                                pkey) else 'invalid_certificate'
                        except:
                            cer.status = 'invalid_certificate'
                elif 'rec' in cer.type:
                    if not cer.cert_file:
                        cer.status = 'no_cert_file'
                        continue
                    if not cer.csr:
                        cer.status = 'cert_not_converted'
                        continue
                    # TODO: more checks?, but it can't be converted if something is wrong...
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
        string="Usage", )  # store=True
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
             'or certificate from P12/PFX cert', )

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

    def button_convert_p12(self):
        self.ensure_one()
        if self.cert_file:
            _password = self.cert_password or ''
            _password = bytes(_password, 'windows-1252', 'strict')
            try:
                private_key, certificate, _dummy = pkcs12.load_key_and_certificates(b64decode(self.cert_file),
                                                                                    _password,
                                                                                    backend=default_backend())
            except Exception as e:
                raise UserError('Certificate acces error, check password or file type!')

            crt = certificate.public_bytes(Encoding.PEM)
            csr = private_key.private_bytes(
                Encoding.PEM,
                format=PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=NoEncryption(),
            )
            cert_not_before = certificate.not_valid_before
            cert_not_after = certificate.not_valid_after

            def convert_date(date):
                try:
                    dt = datetime.strftime(date, "%d.%m.%Y[%H:%M]")
                except Exception as E:
                    print(repr(E))
                    return ""
                return dt

            cert_valid_str = ' - '.join((convert_date(cert_not_before), convert_date(cert_not_after)))

            if not self.name:
                self.name = ' '.join((str(certificate.subject), cert_valid_str))
            self.csr = csr or ''
            self.crt = crt or ''
            self.date_expire = fields.Date.to_date(cert_not_after)
            self.state = 'confirmed'

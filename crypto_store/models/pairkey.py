# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


import os
# from M2Crypto import BIO, Rand, SMIME, EVP, RSA, X509
from OpenSSL import crypto


from odoo import api, fields, models, _
from odoo.exceptions import UserError


STATE_HELP = """
* The 'Draft' state is used when a user is creating a new pair key. Warning: everybody can see the key.
* The 'Confirmed' state is used when the key is completed with public or private key.
* The 'Canceled' state is used when the key is not more used. You cant use this key again.
"""

class CryptoPairkey(models.Model):
    _name = "crypto.pairkey"
    _description = 'Crypto keypair store'


    name = fields.Char('Name')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Owner',
        help='The only who can view, import and export the key.'
    )
    group_id = fields.Many2one(
        comodel_name='res.groups',
        string='User group',
        help='Users group who can use the pairkey.'
    )
    pub = fields.Text(
        string='Public key',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Public key in PEM format.'
    )
    key = fields.Text(
        string='Private key',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Private key in PEM format.'
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('cancel', 'Cancelled'),
        ], string='State',
        readonly=True, default='draft',
        help=STATE_HELP
    )

    def action_validate(self):
        self.ensure_one()
        # Check public key
        pub, key = True, True
        try:
            pub_key = self.pub
            pub_res = crypto.load_publickey(crypto.FILETYPE_PEM, pub_key)
        except:
            pub = False
        # Check private key
        try:
            priv_key = self.key
            priv_res = crypto.load_privatekey(crypto.FILETYPE_PEM, priv_key)
        except:
            key = False
        if not pub or not key:
            raise UserError(_('Key not valid'))
        self.state = 'confirmed'

    def action_cancel(self):
        self.state = 'cancel'

    def action_generate(self):
        self.generate_keys()
        self.action_validate()

    def as_pem(self):
        """
        Return pairkey in pem format.
        """
        private = self.key and self.key.encode('ascii') or ''
        public = self.pub and self.pub.encode('ascii') or ''
        return '\n'.join((private, public))

    # @api.one
    # def as_rsa(self):
    #     """
    #     Return RSA object.
    #     """
    #     return RSA.load_key_string(self.as_pem()[0])

    # @api.one
    # def as_pkey(self):
    #     """
    #     Return PKey object.
    #     """
    #     # def set_key(rsa):
    #     #     pk = EVP.PKey()
    #     #     pk.assign_rsa(rsa)
    #     #     return pk
    #     # return dict((k, set_key(v)) for k, v in self.as_rsa().items())
    #     pk = EVP.PKey()
    #     pk.assign_rsa(self.as_rsa()[0])
    #     return pk


    @api.multi
    def generate_keys(self, key_length=2048, key_gen_number=0x10001):
        """
        Generate key pairs: private and public.
        """
        self.ensure_one()
        key = crypto.PKey()
        key.generate_key(type=crypto.TYPE_RSA, bits=key_length)
        self.key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
        self.pub = crypto.dump_publickey(crypto.FILETYPE_PEM, key)


    def generate_certificate_request(self, x509req, cert_id=False):
        """
        Generate new certificate request for pairkey.
        """
        self.ensure_one()
        if not self.key or not self.pub:
            # possible to generate on the fly?
            raise UserError(_('Missing keys for request generation!'))
        pub = crypto.load_publickey(crypto.FILETYPE_PEM, self.pub)
        x509req.set_pubkey(pub)
        key = crypto.load_privatekey(crypto.FILETYPE_PEM, self.key)
        x509req.sign(key, digest='sha256')


        # Crete certificate object
        cert_obj = self.env['crypto.certificate']
        csr = crypto.dump_certificate_request(crypto.FILETYPE_PEM, x509req)
        if cert_id:
            crt = cert_obj.browse(cert_id)
            crt.write({'csr': csr})
        else:
            cert_obj.create({
                'name': "TODO GET NAME!",
                'csr': csr,
                'pairkey_id': self.id,
            })


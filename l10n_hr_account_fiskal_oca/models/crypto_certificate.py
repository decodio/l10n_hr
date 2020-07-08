# Copyright 2020 Decodio Applications Ltd (https://decod.io)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import os
import OpenSSL
from odoo import api, fields, models, _, tools
from odoo.tools import config as odoo_config


class CryptoCertificate(models.Model):
    _inherit = "crypto.certificate"

    @api.one
    @api.depends('csr', 'crt', 'type')
    def _get_usage(self):
        super(CryptoCertificate, self)._get_usage()
        for crt in self:
            if crt.type != 'server_rec':
                continue
            if not crt.csr:
                continue
            try:
                pp = OpenSSL.crypto.load_certificate(1, crt.crt)
            except Exception as E:
                # what could go wrong? handle better
                raise E
            c_issuer = pp.get_issuer().get_components()
            cert_issuer_ou, cert_issuer_cn = None, None
            for c in c_issuer:
                if c[0] == 'O':
                    cert_issuer_name = c[1]
                elif c[0] == b'CN':
                    cert_issuer_cn = c[1]
                elif c[0] == b'OU':
                    cert_issuer_ou = c[1]

            c_subject = pp.get_subject().get_components()
            cert_subject_cn = None
            for c in c_subject:
                if c[0] == b'CN':
                    cert_subject_cn = c[1]
            usage = False
            if cert_issuer_ou is not None:  # OLD cert, new cert this is None!
                if cert_issuer_ou == b'DEMO':
                    usage = 'Fiskal_DEMO_V1'
                else:
                    usage = 'Fiskal_PROD_V1'
            elif cert_issuer_cn is not None:
                if cert_issuer_cn == b'Fina Demo CA 2014':
                    if cert_subject_cn == b'FISKAL 3':
                        usage = 'Fiskal_DEMO_V3'
                    else:
                        usage = 'Fiskal_DEMO_V2'
                else:
                    if cert_subject_cn == b'FISKAL 3':
                        usage = 'Fiskal_PROD_V3'
                    else:
                        usage = 'Fiskal_PROD_V2'
            crt.usage = usage

    def _get_datastore_path(self):
        return odoo_config.filestore(self._cr.dbname)

    def _get_fiskal_cert_path(self):
        fisk_cert_path = os.path.join(
            self._get_datastore_path(), 'l10n_hr')
        if not os.path.exists(fisk_cert_path):
            os.mkdir(fisk_cert_path, 4600)  # setuid,rw, minimal rights applied
        return fisk_cert_path

    def _get_key_cert_file_name(self):
        key = "{0}-{1}-{2}_key.pem".format(
            self.usage, self.id, self._cr.dbname)
        crt = "{0}-{1}-{2}_crt.pem".format(
            self.usage, self.id, self._cr.dbname)
        return key, crt

    def _disk_check_exist(self, file):
        return os.path.exists(file)

    def _disk_same_content(self, file, content):
        try:
            with open(file, mode="r") as f:
                on_disk = f.read()
                f.close
        except Exception as E:
            on_disk = False
        return not on_disk == content

    def _disk_write_content(self, file, content):
        with open(file, mode="w") as f:
            f.write(content)
            f.flush()

    def get_fiskal_ssl_data(self):
        """
        key and cert are stored on disk because
        ssl and crypto libraries expect them readable on disk or some url.
        so we store both of them in odoo datastore
        :return:
        """
        production = 'PROD' in self.usage
        f_path = self._get_fiskal_cert_path()
        key, cert = self._get_key_cert_file_name()
        for pem in (key, cert):
            file = os.path.join(f_path, pem)
            if pem.endswith('_key.pem'):
                content = self.csr
                key = file
            else:
                content = self.crt
                cert = file

            if self._disk_check_exist(file) or \
                    self._disk_same_content(file, content):
                self._disk_write_content(file, content)


        return key, cert, production

    def _check_valid(self):
        res = super(CryptoCertificate, self)._check_valid()
        if self.state == 'draft' and \
           self.status == 'certificate_converted':
            res['state'] = 'confirmed'
            res['msg'] = False
        return res

    # only to trigger _get_usage call here
    usage = fields.Char(compute="_get_usage", store=True)

    @api.multi
    def action_cancel(self):
        super(CryptoCertificate, self).action_cancel()
        for cert in self:
            if 'Fiskal' in self.usage:
                path = cert._get_fiskal_cert_path()
                key, crt = cert._get_key_cert_file_name()
                for f in (key, crt):
                    file = os.path.join(path, f)
                    if os.path.exists(file):
                        os.remove(file)





# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: l10n_hr_fiskal_lazy
#    Author: Davor Bojkić
#    mail:   bole@dajmi5.com
#    Copyright (C) 2012- Daj Mi 5,
#                  http://www.dajmi5.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields

class account_invoice(osv.Model):
    _inherit = "account.invoice"



    def _get_fiskal_broj(self, cr, uid, ids, field_name, field_value, context=None):
        res={}
        for invoice in self.browse(cr, uid, ids):
            """
                PAZI!! [3:] samo ako je sequence prefiks  %(y)/
                Ukoliko se koristi ova opcija onda ju se nesmije uninstalirati naknadno!  
            """

            res[invoice.id]=(invoice.type in ('out_invoice','out_refund')) and invoice.number and invoice.number[3:].lstrip('0') or False
        return res

    _columns = {
                'fiskal_broj':fields.function(_get_fiskal_broj, type="char", string="Fiskalizirani broj", readonly=True , store=True)
                }

    def invoice_validate(self, cr, uid, ids, context=None):
        assert len(ids)==1,'Jedna po jedna molim lijepo'
        inv_check=self.browse(cr, uid, ids[0])
        if inv_check.type in ('out_invoice','out_refund'):
            if  not inv_check.uredjaj_id:
                raise osv.except_osv('NIJE MOGUCE!', 'Nije unesen naplatni uredjaj')
            #1. provjera po dnevniku/uredjeju
            if inv_check.uredjaj_id.prostor_id.id != inv_check.journal_id.prostor_id.id:
                raise osv.except_osv('NIJE MOGUCE!', 'Ne slazu se podaci o poslovnom prostoru i dokument prodaje')
            #2. provjera po journal/uredjaj
            user = self.pool.get('res.users').browse(cr, uid, uid)
            if user.uredjaji and inv_check.uredjaj_id not in user.uredjaji:
                raise osv.except_osv('NIJE MOGUCE POTVRDITI!', 'Odabrani naplatni Prostor/Blagajana nisu Vam odobreni za koristenje!')
            if user.journals and inv_check.journal_id not in user.journals:
                raise osv.except_osv('NIJE MOGUCE POTVRDITI!', 'Nemate prava pisanja u odabrani Dokument!')


        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        return res

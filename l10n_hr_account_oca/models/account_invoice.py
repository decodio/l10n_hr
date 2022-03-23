from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _default_uredjaj(self):
        user = self.env.user
        inv_type = self.type or self.env.context.get('type', None)
        uredjaj = user.company_id.croatia and \
            inv_type in ('out_invoice', 'out_refund') and user.default_uredjaj \
            or False
        return uredjaj

    croatia = fields.Boolean(related="company_id.croatia")
    date_document = fields.Date(
        string='Document Date',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Date when the document was actually created. "
             "Leave blank for current date",
        copy=False)
    date_delivery = fields.Date(
        string='Delivery Date',
        readonly=True, states={'draft': [('readonly', False)]},
        copy=False,
        help="Date of delivery of goods or service. "
             "Leave blank for current date")

    # DB: namjerno su nazivi polja na hrvatskom!
    # radi potencijalno drugih lokalizacija
    vrijeme_izdavanja = fields.Char(
        # DB: namjerno kao char da izbjegnem timezone problem!
        string="Vrijeme izdavanja",
        help="Fiskal datetime value", copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    fiskalni_broj = fields.Char(
        string="Fiskalni broj", copy=False,
        help="IR-A: Fiskalni broj izlaznog računa\n"
             "UR-A: Broj ulaznog računa (Fiskalni broj za domaće račune).",
        readonly=True, states={'draft': [('readonly', False)]})
    nacin_placanja = fields.Selection(
        selection=[('T', 'TRANSAKCIJSKI RAČUN')],
        string="Način plaćanja", default="T",
        readonly=True, states={'draft': [('readonly', False)]})

    fiskal_uredjaj_id = fields.Many2one(
        comodel_name='fiskal.uredjaj',
        string="Naplatni uređaj",
        readonly=True, states={'draft': [('readonly', False)]},
        default=_default_uredjaj)

    fiskal_responsible_id = fields.Many2one(
        comodel_name='res.partner',
        string="Fiskal responsible",
        domain="[('fiskal_responsible','=',True)]",
        help="Odgovorna osoba za ovaj račun",
        readonly=True, states={'draft': [('readonly', False)]})
    fiskal_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Fiskal validate',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Fiskalizacija. Osoba koja je potvrdila racun',
        copy=False)

    def _get_onchange_create(self):
        res = super()._get_onchange_create()
        if 'fiskal_uredjaj_id' not in res['_onchange_journal_id']:
            res['_onchange_journal_id'].append('fiskal_uredjaj_id')
        return res

    @api.onchange('date_document')
    def _onchange_date_document(self):
        self.date_invoice = self.date_document
        self.date_delivery = self.date_document

    @api.onchange('fiskalni_broj')
    def _onchange_fiskalni_broj(self):
        if self.type in ('in_invoice', 'in_refund'):
            if 'supplier_invoice_number' in self._fields:
                if not self.supplier_invoice_number:
                    self.supplier_invoice_number = self.fiskalni_broj
            if not self.reference:
                self.reference = self.fiskalni_broj

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        type = self.type or self.env.context.get('type', 'out_invoice')
        if type == 'in_invoice' and self.partner_id:
            reference = self.reference or ''
            if self.partner_id.country_id.code == 'HR':
                if not reference.startswith('HR'):
                    self.reference = 'HR00 ' + reference
            else:
                if reference.startswith('HR'):
                    self.reference = self.reference[5:]
        return res


    # TODO: + opcije : sifra, naziv, inicijali...
    #  negdje na company ili na accounting
    # racun_potvrdio = fields.Char

    @api.constrains('fiskalni_broj', 'partner_id', 'date_invoice')
    def _check_double_documents(self):
        if self.fiskalni_broj and self.date_invoice:
            self._cr.execute("""
            SELECT count(id) from account_invoice
             where partner_id = %(partner)s
               and fiskalni_broj = %(fisbr)s
               and extract(year from date_invoice) = %(year)s
            """, {'partner': self.partner_id.id,
                  'fisbr': self.fiskalni_broj,
                  'year': self.date_invoice.year})
            res = self._cr.fetchone()
            res = res and res[0] or 0
            if res > 1:
                msg = _('Document from partner %s with number %s already existing') % (
                    self.partner_id.name, self.fiskalni_broj)
                raise UserError(msg)

    def _get_fiskal_responsible(self):
        fiskal_responsible = self.journal_id.fiskal_responsible_id \
                and self.journal_id.fiskal_responsible_id.id \
                or self.journal_id.company_id.fiskal_responsible_id \
                and self.journal_id.company_id.fiskal_responsible_id.id \
                or False
        if self.croatia and not fiskal_responsible:
            msg = _("Mising fiskal responsible person!\n")
            msg += _("Please select fiskal responsible partner and set it")
            msg += _("on company and/or on journal settings")
            raise UserError(msg)
        return fiskal_responsible

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        res = super(AccountInvoice, self)._onchange_journal_id()
        if res is None:
            res = {}
        res['domain'] = res.get('domain', {})
        if self.journal_id and self.type in ('out_invoice', 'out_refund'):
            self.fiskal_uredjaj_id = self.journal_id.fiskal_uredjaj_ids and \
                                     self.journal_id.fiskal_uredjaj_ids[0] or False
            self.nacin_placanja = self.journal_id.default_nacin_placanja
            res['domain'].update({
                'fiskal_uredjaj_id': [
                    ('prostor_id', '=', self.journal_id.prostor_id.id)]
            })
        # if self.journal_id and self.journal_id.fiscal_position_control_ids:
        #     fp_ids = [x.id for x in self.journal_id.fiscal_position_control_ids]
        #     res['domain'].update({
        #         'partner_id': [('property_account_position_id', 'in', fp_ids)]
        #     })
            self.fiskal_responsible_id = self.journal_id.fiskal_responsible_id \
                        and self.journal_id.fiskal_responsible_id.id \
                        or self.journal_id.company_id.fiskal_responsible_id \
                        and self.journal_id.company_id.fiskal_responsible_id.id \
                        or False
            if not self.fiskal_responsible_id:
                self.fiskal_responsible_id = self._get_fiskal_responsible()
        return res

    @api.onchange('fiskal_uredjaj_id')
    def _onchange_fiskal_uredajaj_id(self):
        if self.fiskal_uredjaj_id:
            allowed_uredjaji = [x.id for x in self.env.user.uredjaj_ids]
            if self.fiskal_uredjaj_id.id not in allowed_uredjaji:
                raise UserError(_('Selected uredjaj is not in your allowed list!'))
            journal_id = self.fiskal_uredjaj_id.journal_ids and \
                            self.fiskal_uredjaj_id.journal_ids[0] or \
                            self.journal_id and self.journal_id.id or False
            return {'value': {'journal_id': journal_id}}

    @api.onchange('payment_term_id', 'date_invoice', 'date_document')
    def _onchange_payment_term_date_invoice(self):
        super(AccountInvoice, self)._onchange_payment_term_date_invoice()
        date = self.date_document or self.date_invoice
        if not date:
            date = fields.Date.context_today(self)
        if not self.payment_term_id:
            # When no payment term defined
            self.date_due = self.date_due or self.date_document or \
                            self.date_invoice
        else:
            pterm = self.payment_term_id
            pterm_list = pterm.with_context(
                currency_id=self.company_id.currency_id.id).compute(
                    value=1, date_ref=date)[0]
            self.date_due = max(line[0] for line in pterm_list)

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        #DB: only check poslovni_prostor if company is from croatia!
        company_id = res.get('company_id', False)
        if not company_id:
            company_id = self.env.context.get('company_id', False)
        company = company_id and self.env['res.company'].browse(
                    company_id) or False
        if company and company.croatia and res.get('journal_id', False) and \
            res.get('type', 'out_invoice') in ('out_invoice', 'out_refund'):
            user = self.env.user
            if not user.prostor_ids:
                msg = "Nije Vam omogućeno izdavanje računa!\n" \
                      "Potrebno je upisati dozvoljene prostore i "\
                      "naplatne uređaje na trenutnom korisniku"
                raise UserError(msg)
            res['fiskal_uredjaj_id'] = self.env.user.default_uredjaj.id
            journal = self.env['account.journal'].browse(res['journal_id'])
            fiskal_responsinle = journal.fiskal_responsible_id and \
                                 journal.fiskal_responsible_id.id or \
                                 company.fiskal_responsible_id and \
                                 company.fiskal_responsible_id.id or False
            if fiskal_responsinle:
                res['fiskal_responsible_id'] = fiskal_responsinle
        return res

    @api.multi
    def action_date_assign(self):
        res = super(AccountInvoice, self).action_date_assign()
        if not self.croatia:
            return res
        for inv in self:
            if not inv.date_invoice:
                inv.date_invoice = fields.Date.context_today(self)
            # ira = self.type in ('out_invoice', 'out_refund')
            # if ira and not inv.vrijeme_izdavanja:
            if not inv.vrijeme_izdavanja:
                # DB: treba li korisniku omogućiti odabir vremena izdavanja?
                time_now = self.company_id.get_l10n_hr_time_formatted()
                inv.vrijeme_izdavanja = time_now['datum_racun']
            # DB: za sada nisu required, samo zapišem trenutni date ako su prazni!
            if not inv.date_document:
                inv.date_document = inv.date_invoice or fields.Date.context_today(self)
            if not inv.date_delivery:
                inv.date_delivery = inv.date_invoice or fields.Date.context_today(self)
            if not self.fiskal_user_id:
                # trenutno onaj koji potvrđuje račun
                self.fiskal_user_id = self.env.user.id
            if not self.fiskal_responsible_id:
                self.fiskal_responsible_id = self._get_fiskal_responsible()
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):
        res = super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if res['type'] == 'form':
            # sve stavke svih vrsta računa otvoriti u popupu
            # slozeno ovdje da se ne ubije ako neki modul napravi slicnu stvar kroz xml...
            # TODO: move functionality to separate module!
            arch = res['fields']['invoice_line_ids']['views']['tree']['arch'].\
                replace('editable="bottom"', '')
            res['fields']['invoice_line_ids']['views']['tree']['arch'] = arch
            pass

        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice=invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        if invoice.type in ('out_invoice', 'out_refund'):
            values['fiskal_uredjaj_id'] = invoice.fiskal_uredjaj_id.id
            values['nacin_placanja'] = invoice.nacin_placanja
            # DB: mozda prvo provjjeriti postoji li jos koji storno,
            # u biti ovjde će se upisati broj kad se potvrđuje ulazno odobrenje
            # ili storno ulzaog računa!
            # values['fiskalni_broj'] = 'Storno - ' + invoice.fiskalni_broj
        return values


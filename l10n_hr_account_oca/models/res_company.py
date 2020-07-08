
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    fiskal_prostor_ids = fields.One2many(
        comodel_name='fiskal.prostor',
        inverse_name='company_id',
        string='Business premises')
    fiskal_separator = fields.Selection(
        selection=[
            ('/', '/'),
            ('-', '-')],
        string="Invoice number separator",
        default='/',  # required=True,    -> multicompany, move required to view
        help="Only '/' or '-' are legaly defined as allowed"
    )
    fiskal_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string="Default Fiskal responsible person",
        help="Default company fiskal responsible person"
             # BOLE: one more override per journal?
    )
    # obracun_poreza = fields.Selection(
    #     selection=[
    #         ('none', 'Nije u sustavu PDV'),
    #         ('r2', 'Po naplaćenom računu (R2)'),
    #         ('r1', 'Po izdanom računu (R1)')],
    #     string='Obračun poreza',
    #     help="Odabir utiče na izgled i sadržaj ispisanog računa") #, required=True) -> move to view

    def check_journal_sequence(self):
        """ TODO:
        Provjerava:
         sve prostore i uređaje, te dnevnike prodaje i sekvence.
         1. sljed_racuna == P:  ( prostor )
            - sekvenca sa prostora je i sekvenca na dnevnicima za taj prostor
         2. sljed_racuna == N:  ( uredjaj )
            - sekvenca se smije koristiti samo za taj jedan uredjaj


        :return:
        """
        return True

class FiskalProstor(models.Model):
    _name = 'fiskal.prostor'
    _description = 'Poslovni prostori - fiskalizacija'

    lock = fields.Boolean(
        string="Lock",
        help="Jednom kad se napravi prvi račun oznaka prostora i sljed računa"
             " se više nesmiju mijenjati"
    )
    name = fields.Char(
        string='Name', size=128)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required="True",
        default=lambda self: self.env['res.company']._company_default_get(
            'fiskal.prostor'))
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='fiskal_prostor_res_users_rel',
        column1='prostor_id', column2='user_id',
        string='Allowed users')

    oznaka_prostor = fields.Char(
        string='Fiscal Code',
        required="True", size=20,
        help="Will be used as second part of fiscal invoice number"
    )
    sljed_racuna = fields.Selection(
        selection=[
            ('N', 'Na nivou naplatnog uredjaja'),
            ('P', 'Na nivou poslovnog prostora')],
        string='Sequence by',
        required="True",
        default='P')
    mjesto_izdavanja = fields.Char(
        string="Place of invoicing", required="True",
        help="It will be used as place of invoicing for this premise, "
             " as a legaly required element"
    )
    uredjaj_ids = fields.One2many(
        comodel_name='fiskal.uredjaj',
        inverse_name='prostor_id',
        string='Uredjaji')
    state = fields.Selection(
        selection=[
            ('draft', 'Nacrt'),
            ('active', 'Aktivan'),
            ('closed', 'Zatvoren')],
        string='State',
        default='draft')
    journal_ids = fields.One2many(
        comodel_name='account.journal',
        inverse_name='prostor_id',
        string="Journals",
        help="Allowed invoicing journals for this business premisse")
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        name="Sequence",
        help="Is invoicing sequence is premisse based, (P)"
             "this is number sequence is used as first part of "
             "invoice fiscal number"
    )

    _sql_constraints = [
            ('fiskal_prostor_uniq',
             'unique (oznaka_prostor,company_id)',
             'The code of the business premise must be unique per company !')
        ]

    @api.one
    def button_activate_prostor(self):
        if '-' in self.oznaka_prostor or '/' in self.oznaka_prostor:
            raise Warning(
                _('Fiscal code contains invalid characters (- or /)')
            )
        self.state = 'active'
        if self.sljed_racuna == 'P':
            if not self.journal_ids:
                raise Warning(
                    _('Activate not possible : no journals assigned!'))
            for journal in self.journal_ids:
                if journal.sequence_id != self.sequence_id:
                    msg = _("Sequence mismatch:")
                    msg += "\n" + _("Premise sequence : %s") % \
                           self.sequence_id.name
                    msg += "\n" + _("Journal sequence : %s") % \
                           journal.sequence_id.name
                    raise Warning(_('Sequence mismatch '))
        else:  # sljed_racuna == 'N'
            if self.sequence_id:
                self.sequence_id = False
            for uredjaj in self.uredjaj_ids:
                # TODO: provjera po uređaju!
                pass


    @api.one
    def button_deactivate_prostor(self):
        self.state = 'closed'
        if self.env.get('l10n_hr_account_fiskal'):
            return self._log_prijava_odjava('odjava')

    @api.model
    def unlink(self):
        for ured in self:
            if ured.lock:
                raise ValidationError('Nije moguće brisati uređaj u kojem je izdan račun!')
        return super(FiskalProstor, self).unlink()

    """
    TODO: 
    create i write - provjera:
    
    1. sljed_racuna == P
       -  
    
    """




class FiskalUredjaj(models.Model):
    _name = 'fiskal.uredjaj'
    _description = 'Podaci o naplatnim uredjajima'

    lock = fields.Boolean(
        string="Lock", default=False,
        help="Jednom kad se napravi prvi račun oznaka uređaja se više nesmije mijenjati"
    )
    name = fields.Char(
        string='Naziv naplatnog uredjaja')
    prostor_id = fields.Many2one(
        comodel_name='fiskal.prostor',
        string='Prostor',
        help='Prostor naplatnog uredjaja',
        ondelete="restrict")
    sljed_racuna = fields.Selection(
        selection=[
            ('N', 'Na nivou naplatnog uredjaja'),
            ('P', 'Na nivou poslovnog prostora')],
        string='Sequence by',
        related='prostor_id.sljed_racuna')
    oznaka_uredjaj = fields.Char(     # -> kad se šalje xml onda strict integer!
        string='Oznaka naplatnog uredjaja',
        size=6, required="True")
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='fiskal_uredjaj_res_users_rel',
        column1='uredjaj_id', column2='user_id',
        string='Korisnici s pravom knjiženja')
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='fiskal_uredjaj_account_journal_rel',
        column1='uredjaj_id', column2='journal_id',
        string='Dnevnici',
        domain="[('type', 'in', ['sale','sale_refund'])]")
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        name="Sequence",
    )
    aktivan = fields.Boolean(
        string='Aktivan',
        default=True)

    _sql_constraints = [
        ('fiskal_uredjaj_uniq',
         'unique (oznaka_uredjaj,prostor_id)',
         'The code of the payment register must be unique per business premise !')
    ]

    # Methods
    @api.multi
    def name_get(self):
        res = []
        for ured in self:
            res.append((ured.id, "%s-%s" % (ured.prostor_id.name, ured.name)))
        return res

    @api.model
    def unlink(self):
        for ured in self:
            if ured.lock:
                raise ValidationError('Nije moguće brisati uređaj na kojem je izdan račun!')
        return super(FiskalUredjaj, self).unlink()

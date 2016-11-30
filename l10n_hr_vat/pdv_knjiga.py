# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Authors:  Goran Kliska @ Slobodni-programi.hr Milan Tribuson @Infokom.hr
#    mail:   
#    Copyright: 
#    Contributions: Marko Carević @Infokom.hr
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

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _

JOURNAL_INVOICES = ('sale','sale_refund','purchase','purchase_refund')
JOURNAL_PAYMENTS = ('cash','bank')


class l10n_hr_pdv_knjiga(osv.osv):
    _name = 'l10n_hr_pdv.knjiga'
    _description = 'Porezne knjige'
   
   
    _columns = {
        'code': fields.char('Code', size=32,  ),
        'name': fields.char('Description', size=64,  ),
        'type': fields.selection([('ira','Knjiga I-RA')
                                 , ('ura' ,'Knjiga U-RA')
                                 , ('ura_tu', 'Knjiga U-RA Tuzemni prijenos')
                                 , ('ura_st', 'Knjiga U-RA Stjecanje EU')
                                 , ('ura_uvoz', 'Knjiga U-RA Uvoz')
                                 , ('ura_nerezident', 'Knjiga U-RA Nerezidenti')
                                 ],'Type', required=True ),
        'based_on': fields.selection([
                                          ('invoice','Periodu racuna'),
                                          ('payment','Periodu placanja'),
                                        ], 
                                                 'Porezni period prema',
                                                 required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'sequence': fields.integer('Sequence', required=True, help="Poredak knjiga u prikazu"),
#        'exclude_tax_code_ids': fields.many2many('account.tax.code', 'l10n_hr_pdv_knjiga_tax_exclude_rel',
#                                      'pdv_knjiga_id','tax_code_id', 
#                                      'Iskljuci poreze iz ispisa',
#                                      help="Ovdje navedene porezne grupe se nece uzimati u obzir prilikom ispisa."),

    }
    _order = "sequence"
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            return user.company_id.id
        return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]

    
    _defaults = {
        'based_on': 'invoice',
        'company_id': _default_company,
        'sequence': 10,
    }


class l10n_hr_pdv_knjiga_stavka(osv.osv):
    _name = 'l10n_hr_pdv.knjiga.stavka'
    _description = 'Stavke porezne knjige'
    _order = 'id desc'
    
    def _get_totals_vat_base(self, cr, uid, ids, name, args, context=None):
        res = {}
        if context is None:
            context = {}
        # TODO IF needed
        return res
            

    _columns = {
        'name': fields.char('Description', size=64, select=True, ),
        'l10n_hr_pdv_knjiga_id': fields.many2one('l10n_hr_pdv.knjiga','Porezna knjiga', select=1),
        'rbr': fields.integer('Redni broj', help="Redni broj u knjizi URA/IRA za poslovnu godinu" ),
        'datum_upisa': fields.date('Datum upisa'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', select=1),
        'move_id': fields.many2one('account.move', 'Move', select=1),
        'move_date': fields.related('move_id', 'date', type='date', readonly=True, relation='account.move', store=True, string='Datum knjizenja' ),
        'period_id': fields.related('move_id', 'period_id', type='many2one', relation='account.period', readonly=True, store=True, string='Period' ),
        'company_id': fields.related('move_id', 'company_id', readonly=True, type='integer', store=True, string='Company' ),
        'invoice_number': fields.related('invoice_id','number', type='char', readonly=True, size=64, relation='account.invoice', string='Broj racuna'),
        'invoice_date_invoice': fields.related('invoice_id', 'date_invoice', type='date', readonly=True, relation='account.invoice', store=True, string='Datum racuna' ),
        'invoice_partner_name': fields.related('invoice_id','partner_id','name', type='char', readonly=True, size=64, relation='account.invoice', store=True, string='Naziv partnera'),
        'invoice_partner_oib': fields.related('invoice_id','partner_id','vat', type='char', readonly=True, size=64, relation='account.invoice', store=True, string='Porezni broj'),
        'reconcile_id'     : fields.many2one('account.move.reconcile', 'Reconcile ID', select=1),
        'reconcile_move_id': fields.many2one('account.move', 'Preknjizavanje kod zatvaranja', select=1),
        'invoice_partner_street': fields.related('invoice_id','partner_id','street', type='char', readonly=True, size=64, relation='account.invoice', store=True, string='Adresa'),
        'invoice_partner_city': fields.related('invoice_id','partner_id','city', type='char', readonly=True, size=64, relation='account.invoice', store=True, string='Sjediste'),
        
        #TO DO Sve u funkciju koja računa po move line-ovima a ne po računu osnovica prema porezima?
        # zadnj dogovor marko-Goran K: Sume retka ćemo zbrajati na reportu!
        #'invoice_amount_untaxed': fields.related('invoice_id','amount_untaxed', readonly=True, size=64, relation='account.invoice', store=True, string='Iznos racuna'),
        #'invoice_amount_base'   : fields.related('invoice_id','amount_untaxed', readonly=True, size=64, relation='account.invoice', store=True, string='Osnovica'),
        #'invoice_amount_tax'    : fields.related('invoice_id','amount_tax'    , readonly=True, size=64, relation='account.invoice', store=True, string='Porez'),
        #'invoice_amount_total'  : fields.related('invoice_id','amount_total'  , readonly=True, size=64, relation='account.invoice', store=True, string='Uk. iznos'),
        #'invoice_tax_line'      : fields.related('invoice_id','tax_line',type='one2many', readonly=True, relation='account.invoice.tax', string='Porezi' ),

        #'vat_position_ids':fields.one2many( 'account.vat.position.by.invoice','invoice_id', 'PDVpozicije', readonly=True) 
        #'vat_position_ids':fields.function( _get_vat_position_lines, 'invoice_id','id',relation='account.vat.position.by.invoice','invoice_id', string='PDVpozicije', readonly=True)
         
        #'vat_position_ids':fields.function(_get_vat_position_lines, readonly=True, method=True,
        #                                    type='one2many', relation='account.vat.position.by.invoice', string='PDVpozicije' ),          
    }


    def write(self, cr, uid, ids, vals, context={}):
        res = super(l10n_hr_pdv_knjiga_stavka, self).write(cr, uid, ids, vals, context)
        return res

    def create(self, cr, uid, vals, context={}):
        #obj_invoice =  self.pool.get('account.invoice').browse(cr, uid, vals['invoice_id'])
        #period_id = obj_invoice.period_id.id
        #if not period_id:
        #    raise osv.except_osv(_('Ne postoji fiskalni period !'), _("Ne postoji otvoreni fiskalni period za račune od %s") % (obj_invoice.date_invoice))
        res=[]    #raise osv.except_osv(_('No Analytic Journal !'),_("You must define an analytic journal of type '%s' !") % ("tt",))
        vals['rbr'] = self.next_knjiga_rbr(cr, uid, vals['period_id'], vals['l10n_hr_pdv_knjiga_id'])
        res.append( super(l10n_hr_pdv_knjiga_stavka, self).create(cr, uid, vals, context) )
        
        return res 
       
        
        for val in vals:
            val['rbr'] = self.next_knjiga_rbr(cr, uid, val['period_id'], val['l10n_hr_pdv_knjiga_id'])
            res.append( super(l10n_hr_pdv_knjiga_stavka, self).create(cr, uid, val, context) )
        #self.update_knjiga_rbr(cr, uid, res, context)
        return res 

    def unlink(self, cr, uid, ids, context={}):
        res = super(l10n_hr_pdv_knjiga_stavka, self).unlink(cr, uid, ids, context)
        #self.update_knjiga_rbr(cr, uid, ids, context)
        return res

    def next_knjiga_rbr(self, cr, uid, period_id, pdv_knjiga_id):
        if not period_id:
            raise osv.except_osv(_('Ne postoji fiskalni period !'), _('Ne postoji otvoreni fiskalni period'))
        
        cr.execute(' '\
                   'SELECT max(pks.rbr) + 1          '\
                   '  FROM l10n_hr_pdv_knjiga_stavka pks       '\
                   '  JOIN account_period  p on (p.id = pks.period_id)  '\
                   ' WHERE pks.l10n_hr_pdv_knjiga_id = %s      '\
                   '   AND p.fiscalyear_id =          '\
                   '       (SELECT p1.fiscalyear_id FROM account_period p1  '\
                   '         WHERE p1.id= %s    )     '\
                   ,(pdv_knjiga_id, period_id ) )
        for r in cr.fetchall():
            res = r[0] or 1
        return res
         
    
    def update_knjiga_rbr(self, cr, uid, ids=[], context=None):
        fiscal_year_ids=[]
        pdv_knjiga_ids=[]
        #return True         #to do
        cr.execute(' '\
                   'UPDATE l10n_hr_pdv_knjiga_stavka '\
                   '   SET rbr= a.poredak '\
                   '  FROM  '\
                   '     ( SELECT  pks.id, '\
                   '               row_number() '\
                   '               OVER( PARTITION BY  p.fiscalyear_id, pks.l10n_hr_pdv_knjiga_id '\
                   '                         ORDER BY /* p.date_start, i.date,*/ pks.move_id  '\
                   '                                  /*pocetak perioda, datum knjiženja, redoslijed knjiženja*/ '\
                   '                   ) '\
                   '               as poredak '\
                   '         FROM l10n_hr_pdv_knjiga_stavka pks '\
                   '         JOIN account_period  p on (p.id = pks.period_id) '\
                   '        WHERE  1=1 '\
                   '        ) a  '\
                   ' WHERE l10n_hr_pdv_knjiga_stavka.id = a.id  '\
                   '   AND coalesce(l10n_hr_pdv_knjiga_stavka.rbr,-1) <> a.poredak  ' 
                   ,)
        return True
    

#                   '          -- AND p.fiscalyear_id in %s '\
#                   '          -- AND pks.l10n_hr_pdv_knjiga_id in %s '\
#                   ,(fiscal_year_ids, pdv_knjiga_ids ) )



class account_move(osv.osv):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(account_move,self).post(cr, uid, ids, context)
        if res:
            line_obj = self.pool.get('l10n_hr_pdv.knjiga.stavka')
            invoice = context.get('invoice', False)
            for move in self.browse(cr, uid, ids):
                if move.journal_id.type not in JOURNAL_INVOICES:
                    invoice = False #Samo račune na post metodi?
                if not invoice:
                    continue    
                #Find invoice looking at reconciliation TODO remove this
                if not invoice:
                    for move_line in move.line_id:
                        if move_line.reconcile_id:
                            for rml in move_line.reconcile_id.line_id:
                                invoice = rml.invoice or invoice
                                if invoice:
                                    break
                        if invoice:
                            break

                pdv_knjiga_ids = move.journal_id.l10n_hr_pdv_knjiga_ids
                if pdv_knjiga_ids:
                    for pdv_knjiga_id in pdv_knjiga_ids:  
                        pdv_knjiga_line = {'name': move.name or '/',
                                           'l10n_hr_pdv_knjiga_id' : pdv_knjiga_id.id,
                                           'move_id': move.id,
                                           'period_id': move.period_id.id,
                                           'invoice_id':invoice and invoice.id
                                     }
                        pdv_knjiga_line_id = line_obj.create(cr, uid, pdv_knjiga_line, context=context)

                # check for exceptions in examining tax codes in lines
                '''
                #TB-20140326 +
                for move_line in move.line_id:
                    if move_line.tax_code_id.contra_side_posting and \
                    move_line.tax_code_id.l10n_hr_pdv_knjiga_id:
                        pdv_knjiga_line = {'name': move.name or '/',
                                           'l10n_hr_pdv_knjiga_id' : move_line.tax_code_id.l10n_hr_pdv_knjiga_id and \
                                           move_line.tax_code_id.l10n_hr_pdv_knjiga_id.id or False,
                                           'move_id': move.id,
                                           'period_id': move.period_id.id,
                                           'invoice_id':invoice and invoice.id,
                                     }
                        pdv_knjiga_line_id = line_obj.create(cr, uid, pdv_knjiga_line, context=context)
                #TB-20140326 -   
                '''               
        return res

    def button_cancel(self, cr, uid, ids, context=None):
        obj_pdv_knjiga_stavka = self.pool.get('l10n_hr_pdv.knjiga.stavka')
        for move_id in ids:
            pdv_knjiga_stavka_ids = obj_pdv_knjiga_stavka.search(cr,uid,[('move_id','=',move_id)])
            obj_pdv_knjiga_stavka.unlink(cr,uid, pdv_knjiga_stavka_ids)
        res = super(account_move,self).button_cancel(cr, uid, ids, context)
        #fix rbr in knjiga
        obj_pdv_knjiga_stavka.update_knjiga_rbr(cr, uid)
        return res


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        res = super(account_move_line, self).reconcile(cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=context)

        reconcile_id = res
        knjiga_stavka_obj = self.pool.get('l10n_hr_pdv.knjiga.stavka')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')

        lines = self.browse(cr, uid, ids, context=context)

        payments_list = []
        invoices_list = []
        for line in lines:
            if (line.partner_id and line.journal_id.type in JOURNAL_INVOICES):
                knjiga_stavka_ids = knjiga_stavka_obj.search(cr, uid, [('move_id' , '=', line.move_id.id),])
                for knjiga_stavka in knjiga_stavka_obj.browse(cr, uid, knjiga_stavka_ids, context=context):
                    if knjiga_stavka.l10n_hr_pdv_knjiga_id.based_on == 'payment':
                        pdv_knjiga_line = {'name': line.name or '/',
                                           'move_line': line,
                                           'move_id': line.move_id.id,
                                           'period_id': line.period_id.id,
                                           'invoice_id': knjiga_stavka.invoice_id and knjiga_stavka.invoice_id.id,
                                           }
                        invoices_list.append(pdv_knjiga_line) #this invoice should go in some book
                        break 
            if (line.partner_id and line.journal_id.type in JOURNAL_PAYMENTS):
                payments_list.append({'move_id': line.move_id.id,
                                      'period_id' : line.move_id.period_id.id ,
                                      'ammount': line.debit + line.credit,
                                      }
                                     )
            if line.journal_id.type not in JOURNAL_PAYMENTS + JOURNAL_INVOICES:
                tax_payment_move_id = line.move_id.id
        new_knjiga_stavka = []
        for invoice_mv in invoices_list:
            for payment in payments_list:
                tax_payment_journal = invoice_mv['move_line'].journal_id.tax_payment_journal_id
                for pdv_knjiga_id in tax_payment_journal.l10n_hr_pdv_knjiga_ids:
                    new_knjiga_stavka.append( {
                               'name': invoice_mv['name'] or '/',
                               'l10n_hr_pdv_knjiga_id' : pdv_knjiga_id.id,
                               'move_id'   : tax_payment_move_id, #payment['move_id'],
                               'period_id' : payment['period_id'],
                               'invoice_id': invoice_mv['invoice_id']
                             })
        for stavka in new_knjiga_stavka:
            #if len(new_knjiga_stavka)>0:
            pdv_knjiga_line_id = knjiga_stavka_obj.create(cr, uid, stavka, context=context)
        return res

    def _remove_move_reconcile(self, cr, uid, move_ids=[], context=None):
        # Part of the job is done in module account_tax_payment - dependency!
        # Function remove move rencocile ids related with moves
        obj_move_line = self.pool.get('account.move.line')
        obj_move_rec = self.pool.get('account.move.reconcile')
        unlink_ids = []
        if not move_ids:
            return True
        recs = obj_move_line.read(cr, uid, move_ids, ['reconcile_id', 'reconcile_partial_id'])
        full_recs = filter(lambda x: x['reconcile_id'], recs)
        rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
        part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
        part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
        unlink_ids += rec_ids
        unlink_ids += part_rec_ids
        rec_move_ids = []
        if len(unlink_ids) > 0:
            obj_rec_move = self.pool.get('account.move.reconcile.move')
            obj_move     = self.pool.get('account.move')
            rec_move_ids = obj_rec_move.search(cr, uid, [('reconcile_id','in', unlink_ids),
                                                         ('type','in', ['tax_payment',])
                                                          ])
        
        #call super account_tax_payment - dependency!
        res = super(account_move_line, self)._remove_move_reconcile(cr, uid, move_ids, context)
        
        #remove additional pdv_knjiga stavka (better to reverse them? if period is closed?)
        obj_pdv_knjiga_stavka = self.pool.get('l10n_hr_pdv.knjiga.stavka')
        for move_id in rec_move_ids:
            pdv_knjiga_stavka_ids = obj_pdv_knjiga_stavka.search(cr,uid,[('move_id','=',move_id)])
            obj_pdv_knjiga_stavka.unlink(cr,uid, pdv_knjiga_stavka_ids)
            #fix rbr in knjiga
            obj_pdv_knjiga_stavka.update_knjiga_rbr(cr, uid)
        return res


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    #TODO DELETE (TEMP SOLUTION)
    _columns = {
        'tax_exemption_ids': fields.many2many('tax.exemption','tax_invoice_rel','invoice_id',
                                              'tax_exemption_id', 'Oslobodenja poreza'),

    }

    def action_move_create(self, cr, uid, ids, *args):
        #update period_id before move_create
        for inv in self.browse(cr, uid, ids):
            period_id = inv.period_id and inv.period_id.id or False
            # get first draft period
            if not period_id:
                period_ids = self.pool.get('account.period').search(cr, uid, 
                                                                    [ ('date_stop','>=',inv.date_invoice or time.strftime('%Y-%m-%d'))
                                                                     ,('state','=','draft')]
                                                                    , order = 'date_start'
                                                                    )
                if len(period_ids) > 0:
                    self.write(cr, uid, [inv.id], {'period_id': period_ids[0] })
        res = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        return res

    # logic moved on button_cancel on accoun_move
    #def action_cancel(self, cr, uid, ids, *args):

    def copy(self, cr, uid, id, default={}, context=None):
        if 'period_id' not in default:
            default.update({
                'period_id':False
            })
        return super(account_invoice, self).copy(cr, uid, id, default, context)



class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'l10n_hr_pdv_knjiga_ids' : fields.many2many('l10n_hr_pdv.knjiga','l10n_hr_pdv_knjiga_rel','journal_id','l10n_hr_pdv_knjiga_id','Porezne knjige URA,IRA'),
    }


class tax_exemption(osv.osv):
    _name = "tax.exemption"
    _columns = {
        'name': fields.char('Naziv', size=64, translate=True, required=True),
        'description': fields.text('Description', size=1024, help='Description', translate=True, required=True)
                }


class account_tax_code(osv.osv):
    _inherit = "account.tax.code"
    _columns = {
        'tax_exemption_ids': fields.many2many('tax.exemption','tax_exemption_rel','tax_code_id',
                                                'tax_exemption_id', 'Oslobodenja poreza'),
        'l10n_hr_pdv_knjiga_id': fields.many2one('l10n_hr_pdv.knjiga','Porezne knjige URA,IRA', select=1), #TB

    }

# to do dodati na init nekog view-a ili na SAVE metodi move linea MILAN-GORAN
"""
        cr.execute('''
                CREATE OR REPLACE FUNCTION debit_credit2tax_amount() RETURNS trigger AS 
                $debit_credit2tax_amount$
                BEGIN
                   NEW.tax_amount := CASE when NEW.tax_code_id is not null
                                           then coalesce(NEW.credit, 0.00)+coalesce(NEW.debit, 0.00)
                                           else 0.00
                                      END;      
                   RETURN NEW;
                END;
                $debit_credit2tax_amount$ LANGUAGE plpgsql;
                
                ALTER FUNCTION debit_credit2tax_amount() OWNER TO %s;
                
                DROP TRIGGER IF EXISTS move_line_tax_amount ON account_move_line;
                CREATE TRIGGER move_line_tax_amount BEFORE INSERT OR UPDATE ON account_move_line
                    FOR EACH ROW EXECUTE PROCEDURE debit_credit2tax_amount();
        '''%(tools.config['db_user'],))

"""



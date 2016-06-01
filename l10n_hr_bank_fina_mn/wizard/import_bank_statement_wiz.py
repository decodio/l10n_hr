# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014- Slobodni programi (<http://www.slobodni-programi.hr>).
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsability of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs
#    End users who are looking for a ready-to-use solution with commercial
#    garantees and support are strongly adviced to contract a Free Software
#    Service Company
#
#    This program is Free Software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
import base64
from datetime import datetime
import time


#_row_types = ('900', '903', '905', '907', '909', '999')
#_row_length = 1000


def str2date(date_str):
    return time.strftime('%Y-%m-%d', time.strptime(date_str, '%Y%m%d'))


def str2float(float_str):
    try:
        return float(float_str)
    except:
        return 0.0


def format_amount(amount):
    sign = '-' if amount < 0 else ''
    amount = str(abs(amount)).split('.')
    if len(amount[1]) == 1:
        amount[1] += '0'
    dec = '' if len(amount) == 1 else ',' + amount[1]
    amount = amount[0]
    m = len(amount)
    return sign + ('.'.join([amount[0: m % 3]] + [amount[i:i + 3] for i in range(m % 3, m, 3)])).lstrip('.') + dec


def format_reference(reference):
    if reference[:2] == 'HR' and len(reference) >= 4:
        reference = reference[:4] + ' ' + reference[4:]
    return reference.strip()


class import_bank_statement_wiz(orm.TransientModel):
    _name = 'import.bank.statement.wiz'
    _description = "Import Bank Statement file"
    _rec_name = "file_name"

    _row_defs = {
        '900': {
            'IZ900DVBDIPOS':      ('VBDI – pošiljatelja (banke)',                        'M', 'N',    1,    7,    7, 'Upisuje se VBDI banke'),
            'IZ900NAZBAN':        ('Naziv banke',                                        'M', 'C',    8,   57,   50, 'Upisuje se naziv banke'),
            'IZ900OIBBNK':        ('OIB banke',                                          'M', 'N',   58,   68,   11, 'Upisuje se OIB banke'),
            'IZ900VRIZ':          ('Vrsta izvatka',                                      'O', 'N',   69,   72,    4, 'Upisuje se 1000 i označava duljinu sloga odnosno poziciju na koji se nalazi tip sloga (IZ900TIPSL)'),
            'IZ900DATUM':         ('Datum obrade – tekući datum GGGGMMDD',               'M', 'C',   73,   80,    8, 'Upisuje se datum kreiranja izvatka na elektronskom mediju u formatu GGGGMMDD'),
            'IZ900REZ2':          ('Rezerva',                                            'O', 'C',   81,  997,  917, ''),
            'IZ900TIPSL':         ('Tip sloga',                                          'M', 'N',  998, 1000,    3, ''),
        },
        '903': {
            'IZ903VBDI':          ('Vodeći broj banke',                                  'M', 'N',    1,    7,    7, ''),
            'IZ903BIC':           ('BIC - Identifikacijska šifra banke',                 'O', 'C',    8,   18,   11, ''),
            'IZ903RACUN':         ('Transakcijski račun klijenta',                       'M', 'C',   19,   39,   21, ''),
            'IZ903VLRN':          ('Valuta transakcijskog računa',                       'M', 'C',   40,   42,    3, ''),
            'IZ903NAZKLI':        ('Naziv klijenta',                                     'M', 'C',   43,  112,   70, ''),
            'IZ903SJEDKLI':       ('Sjedište klijenta',                                  'M', 'C',  113,  147,   35, ''),
            'IZ903MB':            ('Matični broj',                                       'O', 'N',  148,  155,    8, ''),
            'IZ903OIBKLI':        ('OIB klijenta',                                       'O', 'N',  156,  166,   11, ''),
            'IZ903RBIZV':         ('Redni broj izvatka',                                 'M', 'N',  167,  169,    3, ''),
            'IZ903PODBR':         ('Podbroj izvatka',                                    'M', 'N',  170,  172,    3, ''),
            'IZ903DATUM':         ('Datum izvatka',                                      'M', 'N',  173,  180,    8, 'Prikazuje se u formatu GGGGMMDD'),
            'IZ903BRGRU':         ('Redni broj grupe paketa',                            'M', 'N',  181,  184,    4, ''),
            'IZ903VRIZ':          ('Vrsta izvatka',                                      'M', 'N',  185,  188,    4, 'Upisuje se oznaka 1000'),
            'IZ903REZ':           ('Rezerva',                                            'O', 'C',  189,  997,  809, ''),
            'IZ903TIPSL':         ('Tip sloga',                                          'M', 'N',  998, 1000,    3, ''),
        },
        '905': {
            'IZ905OZTRA':         ('Oznaka transakcije',                                 'M', 'N',    1,    2,    2, 'upisuje se podatak 10 ili 20 kao oznaka vrste transakcije čime se imatelju transakcijskog računa daje objašnjenje oznake vrste transakcije'),
            'IZ905RNPRPL':        ('Račun primatelja-platitelja',                        'O', 'C',    3,   36,   34, 'Ukoliko se prikazuje račun prema NKS konstrukciji računa- VBDI(7)-broj računa (10), račun se popunjava u slijedu, bez razmaka i posebnih znakova'),
            'IZ905NAZPRPL':       ('Naziv primatelja-platitelja',                        'O', 'C',   37,  106,   70, ''),
            'IZ905ADRPRPL':       ('Adresa primatelja-platitelja',                       'O', 'C',  107,  141,   35, ''),
            'IZ905SJPRPL':        ('Sjedište primatelja-platitelja',                     'O', 'C',  142,  176,   35, ''),
            'IZ905DATVAL':        ('Datum valute (GGGGMMDD)',                            'M', 'C',  177,  184,    8, 'Prikazuje se u formatu GGGGMMDD'),
            'IZ905DATIZVR':       ('Datum izvršenja (GGGGMMDD)',                         'M', 'C',  185,  192,    8, 'Prikazuje se u formatu GGGGMMDD'),
            'IZ905VLPL':          ('Valuta pokrića',                                     'O', 'C',  193,  195,    3, ''),
            'IZ905TECAJ':         ('Tečaj/koeficijent',                                  'O', 'N',  196,  210,   15, '9+6 znakova – 6 su decimale'),
            'IZ905PREDZNVL':      ('Predznak je „+“, a u slučaju storna upisuje se „-„', 'O', 'C',  211,  211,    1, ''),
            'IZ905IZNOSPPVALUTE': ('Iznos u valuti pokrića',                             'O', 'N',  212,  226,   15, ''),
            'IZ905PREDZN':        ('Predznak je „+“, a u slučaju storna upisuje se „-„', 'M', 'C',  227,  227,    1, ''),
            'IZ905IZNOS':         ('Iznos',                                              'M', 'N',  228,  242,   15, 'Iznos u valuti transakcijskog računa iz polja IZ903VLRN. Dozvoljeno je najviše 15 znakova – cijeli broj 13 znakova + 2 decimale (bez delimitera)'),
            'IZ905PNBPL':         ('Poziv na broj platitelja',                           'O', 'C',  243,  268,   26, ''),
            'IZ905PNBPR':         ('Poziv na broj primatelja',                           'O', 'C',  269,  294,   26, ''),
            'IZ905SIFNAM':        ('Šifra namjene',                                      'O', 'C',  295,  298,    4, 'Prikazuje se šifra namjene transakcije prema ISO standardu 20022'),
            'IZ905OPISPL':        ('Opis plaćanja',                                      'O', 'C',  299,  438,  140, ''),
            'IZ905IDTRFINA':      ('Identifikator transakcije – inicirano u FINI',       'O', 'C',  439,  480,   42, 'Upisuje se identifikator transakcije inicirane u FINI - broj za reklamaciju'),
            'IZ905IDTRBAN':       ('Identifikator transakcije – inicirano izvan FINE',   'M', 'C',  481,  515,   35, 'Upisuje se identifikator transakcije banke '),
            'IZ905REZ2':          ('Rezerva',                                            'O', 'N',  516,  997,  482, ''),
            'IZ905TIPSL':         ('Tip sloga',                                          'M', 'N',  998, 1000,    3, ''),
        },
        '907': {
            'IZ907RAČUN':         ('Transakcijski račun klijenta',                       'M', 'C',    1,   21,   21, ''),
            'IZ907VLRN':          ('Valuta transakcijskog računa',                       'M', 'C',   22,   24,    3, ''),
            'IZ907NAZKLI':        ('Naziv klijenta',                                     'M', 'C',   25,   94,   70, ''),
            'IZ907RBIZV':         ('Redni broj Izvatka',                                 'M', 'N',   95,   97,    3, ''),
            'IZ907PRRBIZV':       ('Redni broj prethodnog Izvatka',                      'O', 'N',   98,  100,    3, ''),
            'IZ907DATUM':         ('Datum izvatka',                                      'M', 'N',  101,  108,    8, 'Prikazuje se u formatu GGGGMMDD GGGGMMDD'),
            'IZ907DATPRSAL':      ('Datum prethodnog stanja (GGGGMMDD)',                 'O', 'C',  109,  116,    8, 'Prikazuje se u formatu GGGGMMDD'),
            'IZ907PPPOS':         ('Predznak prethodnog stanja',                         'O', 'C',  117,  117,    1, ''),
            'IZ907PRSAL':         ('Prethodno stanje',                                   'M', 'N',  118,  132,   15, ''),
            'IZ907PREREZ':        ('Predznak rezervacije',                               'O', 'C',  133,  133,    1, ''),
            'IZ907IZNREZ':        ('Iznos rezervacije',                                  'O', 'N',  134,  148,   15, ''),
            'IZ907DATOKV':        ('Datum dozvoljenog prekoračenja (GGGMMDD)',           'O', 'C',  149,  156,    8, ''),
            'IZ907IZNOKV':        ('Dozvoljeno prekoračenje (okvirni kredit)',           'O', 'N',  157,  171,   15, ''),
            'IZ907IZNZAPSR':      ('Iznos zaplijenjenih sredstava',                      'O', 'C',  172,  186,   15, ''),
            'IZ907PRASPSTA':      ('Predznak raspoloživog stanja',                       'O', 'C',  187,  187,    1, ''),
            'IZ907IZNRASP':       ('Iznos raspoloživog stanja',                          'O', 'N',  188,  202,   15, ''),
            'IZ907PDUGU':         ('Predznak ukupnog dugovnog prometa',                  'O', 'C',  203,  203,    1, ''),
            'IZ907KDUGU':         ('Ukupni dugovni promet',                              'M', 'N',  204,  218,   15, ''),
            'IZ907PPOTR':         ('Predznak ukupnog potražnog prometa',                 'O', 'C',  219,  219,    1, ''),
            'IZ907KPOTR':         ('Ukupni potražni promet',                             'M', 'N',  220,  234,   15, ''),
            'IZ907PRNOS':         ('Predznak novog stanja',                              'O', 'C',  235,  235,    1, ''),
            'IZ907KOSAL':         ('Novo stanje',                                        'M', 'N',  236,  250,   15, ''),
            'IZ907BRGRU':         ('Redni broj grupe u paketu',                          'O', 'N',  251,  254,    4, ''),
            'IZ907BRSTA':         ('Broj stavaka u grupi',                               'O', 'N',  255,  260,    6, ''),
            'IZ907TEKST':         ('Tekstualna poruka',                                  'O', 'C',  261,  680,  420, 'Upisuje u jednom retku'),
            'IZ907REZ2':          ('Rezerva',                                            'O', 'C',  681,  997,  317, ''),
            'IZ907TIPSL':         ('Tip sloga',                                          'M', 'N',  998, 1000,    3, ''),
        },
        '909': {
            'IZ909DATUM':         ('Datum obrade',                                       'M', 'N',    1,    8,    8, 'Upisuje se u formatu: GGGGMMDD'),
            'IZ909UKGRU':         ('Ukupan broj grupa/paket',                            'M', 'N',    9,   13,    5, ''),
            'IZ909UKSLG':         ('Ukupan broj slog/paket',                             'M', 'N',   14,   19,    6, 'Ukupan broj slogova u datoteci uključuje tip sloga 900 + tip sloga 903 + ukupan broj slogova tipa 905 + tip sloga 907 + tip sloga 909'),
            'IZ909REZ3':          ('Rezerva',                                            'O', 'C',   20,  997,  978, ''),
            'IZ909TIPSL':         ('Tip sloga',                                          'M', 'N',  998, 1000,    3, ''),
        },
        '999': {
            'IZ999REZ1':          ('Rezervirana mjesta',                                 'O', 'C',    1,  997,  997, ''),
            'IZ999TIPSL':         ('Tip sloga – oznaka 999',                             'M', 'C',  998, 1000,    3, ''),
        },
    }
    _row_types = ('900', '903', '905', '907', '909', '999')
    _row_length = 1000

    def _get_default_receivable_account_id(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        data = False
        if company_id:
            data = self.pool.get('res.company').read(cr, uid, company_id, ['receivable_account_id'], context=context)
        return data and data['receivable_account_id'] and data['receivable_account_id'][0] or False

    def _get_default_payable_account_id(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        data = False
        if company_id:
            data = self.pool.get('res.company').read(cr, uid, company_id, ['payable_account_id'], context=context)
        return data and data['payable_account_id'] and data['payable_account_id'][0] or False
    _columns = {
        'file_name': fields.char('File Name', size=128, required=True),
        'file_data': fields.binary('File Data', required=True),
        'import_log': fields.text('Import Log', readonly=True),
        'receivable_account_id': fields.many2one('account.account', 'Default Receivable Account',
                                  domain=[('type', '=', 'receivable')], required=True,
                                  help='Set here the receivable account that will be used, by default, if the partner is not found',),
        'payable_account_id': fields.many2one('account.account', 'Default Payable Account',
                                  domain=[('type', '=', 'payable')], required=True,
                                   help='Set here the payable account that will be used, by default, if the partner is not found'),        
    }

    _defaults = {
        'file_name': lambda *a: '',
        'receivable_account_id': _get_default_receivable_account_id,
        'payable_account_id': _get_default_payable_account_id,
    }

    def parse_file(self, cr, uid, ids, context=None, batch=False, filedata=None, filename=None):

        def parse_row(cr, uid, row_number, row_type, row, strip=False, check=False, context=None):
            if not row_type in self._row_defs:
                raise orm.except_orm(_('Error!'), _('Unknown row type: %s!') % (row_type,))
            row_def = self._row_defs.get(row_type)
            res = {}.fromkeys(row_def, None)
            for key in row_def.keys():
                res[key] = row[row_def[key][3] - 1: row_def[key][4]]
                if strip:
                    res[key] = res[key].strip()
                if check and row_def[key][1] == 'M':
                    if not res[key]:
                        raise orm.except_orm(_('Error!'), _('Row: %d\nRow type: %s\nMissing data in the mandatory field %s "%s".') % (row_number, row_type, key, row_def[key][0],))
            return res

        if context is None:
            context = {}
        data = self.browse(cr, uid, ids)[0]
        if batch:
            filedata = str(filedata)
            filename = filename
        else:
            try:
                filedata = data.file_data
                filename = data.file_name
            except:
                raise orm.except_orm(_('Error!'), _('Wizard in incorrect state. Please hit the Cancel button!'))
                return {}

        bank_st_import_obj = self.pool.get('account.bank.statement.imports')
        bank_st_obj = self.pool.get('account.bank.statement')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        period_obj = self.pool.get('account.period')
        company_obj = self.pool.get('res.company')
        currency_obj = self.pool.get('res.currency')
        partner_bank_obj = self.pool.get('res.partner.bank')
        journal_obj = self.pool.get('account.journal')
        lang_obj = self.pool.get('res.lang')
        mod_obj = self.pool.get('ir.model.data')

        lang_id = lang_obj.search(cr, uid, [('code', '=', context.get('lang', 'en_US'))], limit=1, context=context)
        if lang_id:
            lang = lang_obj.browse(cr, uid, lang_id, context=context)[0]
            date_format = lang.date_format
        else:
            date_format = '%d/%m/%Y'

        err_string = ''
        err_code = ''
        err_log = ''
        err_no = 0
        import_statement_vals = {}
        statements = []
        prev_row_type = False
        row_number = 0
        row_number_in_group = 0
        ctx = context.copy()
        ctx.update({'import_bank_statement_from_file': True})   # For create/write bank statement, currency rate

        recordlist = unicode(base64.decodestring(filedata), 'windows-1250', 'strict').split('\n')

        # Parse file
        for record in recordlist:
            if len(record) == 0:
                continue

            if self._row_length and len(record) != self._row_length + 1:
                if self._row_length and len(record) != self._row_length:
                    err_string = _('Incorrect row length.\n%s') % (record,)
                    err_code = 'E0001'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)

            row_type = record[997:1000]

            if not row_type in self._row_types:
                err_string = _('Unknown row type: %s!') % (row_type,)
                err_code = 'E0002'
                if batch:
                    return (err_code, err_string)
                raise orm.except_orm(_('Error!'), err_string)
            if (not prev_row_type and row_type != self._row_types[0]) or (prev_row_type and \
              prev_row_type == row_type and row_type != self._row_types[2]):
                err_string = _('Invalid file "%s"!') % (filename,)
                err_code = 'E0003'
                if batch:
                    return (err_code, err_string)
                raise orm.except_orm(_('Error!'), err_string)
            if prev_row_type and prev_row_type == row_type and row_type != self._row_types[2]:
                err_string = _('Invalid file "%s"!') % (filename,)
                err_code = 'E0003'
                if batch:
                    return (err_code, err_string)
                raise orm.except_orm(_('Error!'), err_string)
            if prev_row_type and self._row_types.index(prev_row_type) > self._row_types.index(row_type):
                if prev_row_type != self._row_types[3] or row_type != self._row_types[1]:
                    err_string = _('Invalid file "%s"!') % (filename,)
                    err_code = 'E0003'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)

            row_number += 1
            row = parse_row(cr, uid, row_number, row_type, record, True, True, context=context)

            if row_type == self._row_types[0]:   # 900
                # Start of the new bank statement file
                if import_statement_vals:
                    err_string = _('Invalid file "%s"!') % (filename,)
                    err_code = 'E0003'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)
                import_statement_vals = {
                    'name': filename,
                    'statement_file': filedata,
                    'import_log': None,
                    'date_create': str2date(row['IZ900DATUM']),
                    'bank_code': row['IZ900DVBDIPOS'],
                    'bank_name': row['IZ900NAZBAN'],
                    'bank_vat_number': row['IZ900OIBBNK'],
                    'import_date': fields.date.context_today(self, cr, uid, context=context),
                    'user_id': uid,
                }

                statement_file_id = bank_st_import_obj.search(cr, uid, [
                    ('name', '=', import_statement_vals['name']),
                    ('date_create', '=', import_statement_vals['date_create']),
                    ('bank_code', '=', import_statement_vals['bank_code']),
                    ('bank_vat_number', '=', import_statement_vals['bank_vat_number'])
                ], context=context)

                if statement_file_id:
                    err_string = _('\nFile "%s" with Create Date "%s" has already been imported!') \
                        % (filename, datetime.strptime(import_statement_vals['date_create'], \
                        '%Y-%m-%d').strftime(date_format))
                    err_code = 'E0004'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)

            elif row_type == self._row_types[1]:   # 903
                # Bank statement start
                row_number_in_group = 0
                statements.append({
                    'st_start': row.copy(),
                    'st_lines': [],
                    'st_end': None,
                })

            elif row_type == self._row_types[2]:   # 905
                # Bank statement line
                row_number_in_group += 1
                row.update({'sequence': row_number_in_group})
                statements[-1]['st_lines'].append(row.copy())

            elif row_type == self._row_types[3]:   # 907
                # Bank statement end
                statements[-1]['st_end'] = row.copy()

            elif row_type == self._row_types[4]:   # 909
                # End of the new bank statement file
                if len(statements) != int(row['IZ909UKGRU']):
                    err_string = _('Number of imported groups (%s) is different from number of groups in the file (%s)!') % (len(statements), int(row['IZ909UKGRU']),)
                    err_code = 'E0005'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)
                if import_statement_vals.get('bank_code') == '2390001':   # Hrvatska poštanska banka prijavljuje jedan redak manje u polju 'IZ909UKSLG'
                    allowed_diff = 1
                else:
                    allowed_diff = 0
                if row_number < int(row['IZ909UKSLG']) or row_number - int(row['IZ909UKSLG']) > allowed_diff:
                    err_string = _('Number of imported rows (%s) is different from number of rows in the file (%s)!') % (row_number, int(row['IZ909UKSLG']),)
                    err_code = 'E0006'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)

            elif row_type == self._row_types[5]:   # 999
                # End of file
                pass

            prev_row_type = row_type
        # end for

        if row_type != self._row_types[5]:   # 999
            err_string = _('Invalid file "%s"!') % (filename,)
            err_code = 'E0003'
            if batch:
                return (err_code, err_string)
            raise orm.except_orm(_('Error!'), err_string)

        company_id = company_obj._company_default_get(cr, uid, 'account.bank.statement.em.import', context=context)
        company = company_obj.browse(cr, uid, company_id, context=context)
        company_currency_code = company.currency_id.name
        statement_ids = []

        # Create bank statements
        for statement in statements:
            statement_line_ids = []
            journal_id = False
            bank_bic = statement['st_start']['IZ903BIC'].replace(' ', '')            # BIC - Identifikacijska šifra banke
            bank_acc_number = statement['st_start']['IZ903RACUN'].replace(' ', '')   # Transakcijski račun klijenta
            if len(bank_acc_number) == 10:
                bank_acc_number = statement['st_start']['IZ903VBDI'].replace(' ', '') + \
                                  statement['st_start']['IZ903RACUN'].replace(' ', '')
            currency_code = statement['st_start']['IZ903VLRN']                       # Valuta transakcijskog računa

            if currency_code and currency_code != company_currency_code:
                currency_ids = currency_obj.search(cr, uid, [('name', '=', currency_code)], context=context)
                if currency_ids:
                    currency_id = currency_ids[0]
                else:
                    err_string = _('You must define currency "%s"!') % (currency_code,)
                    err_code = 'E0010'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)
            else:
                currency_id = False

            partner_bank_ids = partner_bank_obj.search(cr, uid, [('company_id', '=', company_id),
                                                        ('currency_id', '=', currency_id)])
            if partner_bank_ids:
                for partner_bank in partner_bank_obj.browse(cr, uid, partner_bank_ids, context=context):
                    if not journal_id:
                        if partner_bank.acc_number.replace(' ', '').replace('-', '') == bank_acc_number:
                            if not partner_bank.journal_id:
                                err_string = _('You must define journal for company bank account number "%s"!') % (partner_bank.acc_number,)
                                err_code = 'E0011'
                                if batch:
                                    return (err_code, err_string)
                                raise orm.except_orm(_('Error!'), err_string)
                            journal_id = partner_bank.journal_id.id
                            if bank_bic and partner_bank.bank_bic and \
                              bank_bic != partner_bank.bank_bic.replace(' ', ''):
                                err_string = _('BIC "%s" for company bank account "%s" is different from BIC "%s" in the file!') \
                                    % (partner_bank.bank_bic, partner_bank.acc_number, bank_bic,)
                                err_code = 'E0012'
                                if batch:
                                    return (err_code, err_string)
                                raise orm.except_orm(_('Error!'), err_string)
            if not journal_id:
                err_string = _('You must define company bank account for account number "%s". \nCurrency: %s') % (bank_acc_number, currency_code,)
                err_code = 'E0013'
                if batch:
                    return (err_code, err_string)
                raise orm.except_orm(_('Error!'), err_string)
            journal = journal_obj.browse(cr, uid, journal_id, context=context)

            statement_date = str2date(statement['st_start']['IZ903DATUM'])   # Datum izvatka
            period_id = period_obj.search(cr, uid, [('date_start', '<=', statement_date),
                                          ('date_stop', '>=', statement_date)], context=context)[0]
            ctx.update({'date': statement_date})

            balance_start = str2float(statement['st_end']['IZ907PRSAL']) / 100.0   # Prethodno stanje
            if statement['st_end']['IZ907PPPOS'] == '-':
                balance_start *= -1.0
            balance_end_real = str2float(statement['st_end']['IZ907KOSAL']) / 100.0   # Novo stanje
            if statement['st_end']['IZ907PRNOS'] == '-':
                balance_end_real *= -1.0
            total_lcy_amount = 0.0

            # Šifra temeljnice/Godina iz datuma izvatka/Redni broj izvatka-Podbroj izvatka
            if not company.use_journal_seq:
                name = journal.code + '/' + \
                    statement['st_start']['IZ903DATUM'][:4] + '/' + \
                    statement['st_start']['IZ903RBIZV'] + '-' + statement['st_start']['IZ903PODBR']
            else:
                name = bank_st_obj._compute_default_statement_name(cr, uid, journal_id, context=dict(ctx, period_id=period_id))

            statement_id = bank_st_obj.search(cr, uid, [('name', '=', name)], context=context)
            '''
            if statement_id:
                err_string = _('Bank statement "%s" already exists!') % (name,)
                err_code = 'E0014'
                if batch:
                    return (err_code, err_string)
                raise orm.except_orm(_('Error!'), err_string)
            '''
            statement_vals = {
                'name': name,
                'date': statement_date,
                'period_id': period_id,
                'journal_id': journal_id,
                'balance_start': balance_start,
                'balance_end_real': balance_end_real,
                'state': 'draft',
            }
            statement_id = False
            if context.get('active_model') == 'account.bank.statement' and context.get('active_id'):
                active_statement = bank_st_obj.browse(cr, uid, context.get('active_id', 0), context=context)
                if active_statement.name == '/' and active_statement.state == 'draft' and \
                  (not active_statement.line_ids):
                    statement_id = active_statement.id
            if statement_id:
                bank_st_obj.write(cr, uid, [statement_id], statement_vals, context=ctx)
            else:
                statement_id = bank_st_obj.create(cr, uid, statement_vals, context=ctx)
            statement_ids.append(statement_id)

            for st_line in statement['st_lines']:
                name = st_line['IZ905OPISPL']
                if st_line['IZ905PNBPR'][:2] == 'HR' and len(st_line['IZ905PNBPR']) >= 4:
                    ref = st_line['IZ905PNBPR'][:4] + ' ' + st_line['IZ905PNBPR'][4:]
                else:
                    ref = st_line['IZ905PNBPR']
                partner_bank_acc_number = st_line['IZ905RNPRPL']
                fina_branch_code = st_line['IZ905IDTRFINA'][7:12]
                amount_original = str2float(st_line['IZ905IZNOS']) / 100.0
                correction = st_line['IZ905PREDZN'] == '-'
                if st_line['IZ905OZTRA'] in ['10', ]:
                    note = 'NA TERET'
                    type = 'supplier'
                    debit = 0.0
                    credit = amount_original
                elif st_line['IZ905OZTRA'] in ['20', ]:
                    note = 'U KORIST'
                    if not partner_bank_acc_number or partner_bank_acc_number == '0000000000':
                        type = 'general'
                    else:
                        type = 'customer'
                    debit = amount_original
                    credit = 0.0
                else:
                    err_string = _('Unknown transaction type "%s"!') % (st_line['IZ905OZTRA'],)
                    err_code = 'E0015'
                    if batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)
                #amount = debit - credit
                amount = credit - debit

                if currency_code != company_currency_code:
                    if st_line['IZ905VLPL'] == company_currency_code:
                        lcy_amount = str2float(st_line['IZ905IZNOSPPVALUTE']) / 100.0
                    else:
                        lcy_amount = 0.0
                    if not lcy_amount:
                        lcy_amount = currency_obj.compute(cr, uid, currency_id, 
                                          company.currency_id.id, amount, round=True, context=ctx)
                else:
                    lcy_amount = amount
                total_lcy_amount += lcy_amount

                partner_res = bank_st_line_obj.search_partner(cr, uid, {
                    'name': name,
                    'ref': ref,
                    'bank_acc_number': partner_bank_acc_number,
                    'fina_branch_code': fina_branch_code,
                    'type': type,
                    'amount': amount_original,
                    'force_account_id': journal.force_account and \
                                        journal.force_account.id or False
                }, context=context)
                partner_id = partner_res['value'].get('partner_id')
                account_id = partner_res['value'].get('account_id')
                if not partner_id and account_id and partner_res['value'].get('type'):
                    type = partner_res['value'].get('type')
                warning = partner_res.get('warning')
                if not account_id:
                    account_id = (type == 'customer' and data.receivable_account_id.id) or \
                      (type == 'supplier' and data.payable_account_id.id) or data.receivable_account_id.id

                note += u'\nRačun primatelja-platitelja: ' + partner_bank_acc_number \
                    + u'\nPartner: ' + st_line['IZ905NAZPRPL'] \
                    + u'\nAdresa: ' + st_line['IZ905ADRPRPL'] \
                    + u'\nSjedište: ' + st_line['IZ905SJPRPL'] \
                    + u'\nPoziv na broj platitelja: ' + st_line['IZ905PNBPL'] \
                    + u'\nPoziv na broj primatelja: ' + st_line['IZ905PNBPR'] \
                    + u'\nŠifra namjene: ' + st_line['IZ905SIFNAM'] \
                    + u'\nIdentifikator transakcije banke: ' + st_line['IZ905IDTRBAN']
                if fina_branch_code:
                    note += u'\nOznaka FINA poslovnice: ' + fina_branch_code

                statement_line_id = bank_st_line_obj.create(cr, uid, {
                    'name': name,
                    'ref': ref,
                    'date': str2date(st_line['IZ905DATIZVR']),
                    'type': type,
                    'partner_id': partner_id,
                    'account_id': account_id,
                    'statement_id': statement_id,
                    'sequence': st_line['sequence'],
                    'amount': amount,
                    'debit': debit,
                    'credit': credit,
                    'lcy_amount': lcy_amount,
                    'correction': correction,
                    'note': note,
                    'bank_acc_number': partner_bank_acc_number,
                    'fina_branch_code': fina_branch_code,
                }, context=ctx)
                statement_line_ids.append(statement_line_id)

                if (not partner_id and type != 'general') or (type == 'general' and \
                  account_id == data.receivable_account_id.id):
                    err_no += 1
                    err_log += u'\n\nIzvadak: ' + statement['st_start']['IZ903RBIZV'] + '-' + \
                      statement['st_start']['IZ903PODBR'] \
                        + u' (' + currency_code + u')' \
                        + u'\nGreška: Nepoznat partner u retku ' + str(st_line['sequence']) \
                        + u'\n    Partner: ' + st_line['IZ905NAZPRPL'] \
                        + u'\n    Adresa: ' + st_line['IZ905ADRPRPL'] \
                        + u'\n    Sjedište: ' + st_line['IZ905SJPRPL'] \
                        + u'\n    Račun ' + ((type == 'supplier' and u'primatelja: ') or \
                         (type == 'customer' and u'platitelja: ') or u'primatelja-platitelja: ') + \
                         partner_bank_acc_number \
                        + u'\n    Poziv na broj platitelja: ' + format_reference(st_line['IZ905PNBPL']) \
                        + u'\n    Poziv na broj primatelja: ' + format_reference(st_line['IZ905PNBPR']) \
                        + u'\n    Šifra namjene: ' + st_line['IZ905SIFNAM'] \
                        + u'\n    Iznos: ' + format_amount(amount_original) \
                        + u'\n    Identifikator transakcije banke: ' + st_line['IZ905IDTRBAN']
                    if fina_branch_code:
                        err_log += u'\n    Oznaka FINA poslovnice: ' + fina_branch_code
                    if warning:
                        err_log += warning
            # end for

            if statement_line_ids:
                pass
                #bank_st_line_obj.create_voucher(cr, uid, statement_line_ids, context=ctx)
            #balance_start_lvt = bank_st_obj.browse(cr, uid, statement_id, context=ctx).balance_start_lvt or 0.0
            #bank_st_obj.write(cr, uid, [statement_id], {'balance_end_lvt': balance_start_lvt + \
                                                        #total_lcy_amount}, context=ctx)

        # end for

        import_log = u'Uvezeno izvadaka: ' + str(len(statement_ids))
        if err_no:
            import_log += u'\nBroj grešaka: ' + str(err_no) + err_log
        import_statement_vals.update({'import_log': import_log})
        statement_file_id = False
        err_string = ''
        err_code = ''

        try:
            if context.get('active_model') == 'account.bank.statement.imports' and context.get('active_id'):
                if not bank_st_import_obj.browse(cr, uid, context.get('active_id', 0), context=context).name:
                    statement_file_id = context.get('active_id')
            if statement_file_id:
                bank_st_import_obj.write(cr, uid, statement_file_id, import_statement_vals, context=context)
            else:
                statement_file_id = bank_st_import_obj.create(cr, uid, import_statement_vals, context=context)
            bank_st_obj.write(cr, uid, statement_ids, {'statement_file_id': statement_file_id}, context=ctx)

            context.update({'statement_file_id': statement_file_id, 'statement_ids': statement_ids})

            model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'),
                       ('name', '=', 'view_bank_statement_import_result_form')], context=context)
            resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'],
                            context=context)[0]['res_id']
        except orm.except_orm, e:
            cr.rollback()
            err_string = _('\nApplication Error: ') + str(e)
        except Exception, e:
            cr.rollback()
            err_string = _('\nSystem Error: ') + str(e)
        except:
            cr.rollback()
            err_string = _('\nUnknown Error: ') + str(e)

        if err_string:
            err_code = 'G0001'
            if batch:
                return (err_code, err_string)
            raise orm.except_orm(_('File import failed!'), err_string)

        self.write(cr, uid, ids, {'import_log': import_log}, context=context)

        return {
            'name': _('Import bank statement file result'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.bank.statement.wiz',
            'view_id': False,
            'target': 'new',
            'views': [(resource_id, 'form')],
            'context': context,
            'type': 'ir.actions.act_window',
        }

    def action_open_bank_statement_file(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        module, xml_id = 'l10n_hr_bank_fina_mn', 'action_bank_statement_import'
        res_model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
        action = self.pool.get('ir.actions.act_window').read(cr, uid, res_id, context=context)
        domain = eval(action.get('domain') or '[]')
        domain += [('id', '=', context.get('statement_file_id', False))]
        action.update({'domain': domain})
        return action

    def action_open_bank_statements(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        module, xml_id = 'account', 'action_bank_statement_tree'
        res_model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
        action = self.pool.get('ir.actions.act_window').read(cr, uid, res_id, context=context)
        domain = eval(action.get('domain') or '[]')
        domain += [('id', 'in', context.get('statement_ids', False))]
        action.update({'domain': domain})
        return action
#import_bank_statement_wiz()

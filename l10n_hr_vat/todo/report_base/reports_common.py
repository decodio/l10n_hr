# -*- coding: utf-8 -*-
import pytz
from datetime import datetime
from openerp.osv import osv, fields

def get_current_datetime():
    #DB: Server mora biti na UTC time... ovo vraća točan local time za XML, fiskalizaciju isl...
    zg = pytz.timezone('Europe/Zagreb')
    return zg.normalize(pytz.utc.localize(datetime.utcnow()).astimezone(zg)).strftime("%Y-%m-%dT%H:%M:%S")

def get_izvjesce_sastavio(self, cr, uid, context=None):
    """ ZA XML
    return: {'naziv': ime_prezime,
             'ime': ime
             'prezime':prezime}
    """
    res={}
    cr.execute("select state from ir_module_module where name='hr'")
    hr = cr.fetchone()
    
    if hr and hr[0]=='installed':
        department = self.pool.get('hr.department')
        main_id = department.search(cr, uid, [('parent_id','=',False)])
        
        if len(main_id)>1:
            raise osv.except_osv((u'Greška!'),(u'Vaša tvrtka ima više glavnih odjela'))
        elif len(main_id)==0:
            raise osv.except_osv((u'Greška!'),(u'Vaša tvrtka nema definirane odjele'))
        else:
            department = department.browse(cr, uid, main_id[0])
            if not department.manager_id :
                raise osv.except_osv((u'Greška!'),(u'Vaša tvrtka nema definiranu odgovornu osobu (manager)'))
            manager_name = department.manager_id.name_related
            name = manager_name.split()
            res['naziv']=manager_name
            if len(name) == 2:
                res['ime']=name[0]
                res['prezime']=name[1]
            elif len(name)>2:
                #TODO: dialog sa odabirom "ime ime"+"prezime" ili "ime"+"prezime prezime"... 
                raise osv.except_osv((u'Greška!'),('Imate dva imena i/ili dva prezimena, spojite ih znakom "-" bez razmaka'))
            elif len(name)==1:
                raise osv.except_osv((u'Greška!'),('Ime odgovorne osobe nije ispravno (nedostaje ime ili prezime)'))
    else:
        raise osv.except_osv(u'Greška!',u'Nije instaliran modul HR - nije moguće dohvatiti osobu koja je sastavila izvješće')
    return res


def check_valid_phone(self,phone):
    """Za PDV obrazac:
    Broj telefona, počinje sa znakom + nakon kojeg slijedi 8-13 brojeva, npr +38514445555
    """
    if not phone:
        return False
    phone = phone.replace(" ","").replace("/","").replace(",","").replace("(","").replace(")","")
    
    if phone.startswith('00'):
        phone = '+' + phone[2:]
    if not phone.startswith('+'):
        phone = '+' + phone
    
    if 14 < len(phone) < 7:
        raise osv.except_osv(u'Greška u postavkama!',u'Unešeni broj telefona/faxa : %s u postavkama tvrtke nije ispravan\nOčekivani format je +385xxxxxxxx , (dozvoljno je korištenje znakova za razdvajanje i grupiranje (-/) i razmaka' % phone)
    
    return phone


def get_company_data(self, cr, uid, report_type, context=None, hr_only=True):
    """
    Dohvat podataka za Tvrtku, sa provjerom svih obaveznih podataka i njihove strukture
    
    @report_type : PDV, 
            todo: JOPPD ... 
    """
    company_id = context.get('company_id', 1)
    
    company = self.pool.get('res.company').browse(cr, uid, company_id)
    res = {}
    if hr_only and company.country_id.code != 'HR':
        raise osv.except_osv('Error!','This report is for CROATIA companies only!')
    
    #provjera company podataka
    if not company.city:
        raise osv.except_osv(u'Nedostaju podaci!',u'U adresi poduzeća nije upisan grad!')
    if not company.street:
        raise osv.except_osv(u'Nedostaju podaci!',u'U adresi poduzeća nije upisana ulica!')
    if company.street2:
        #TODO : provjeriti dali je ispravan kućni broj 
        pass
    if not company.vat:
        raise osv.except_osv(u'Nedostaju podaci!',u'U postavkama poduzeća nedostaje OIB!')
    oib = company.vat
    if oib.startswith('HR'): 
        oib = oib[2:]
    
    
    res = {
        'naziv': company.name,
        'ulica': company.street,
        'kbr': company.street2 and company.street2 or False,
        'mjesto': company.city,
        'posta':company.zip,
        'email': company.partner_id.email and company.partner_id.email or False,
        'oib': oib,
        'tel': check_valid_phone(self, company.partner_id.phone), 
        'fax': check_valid_phone(self, company.partner_id.fax),
    }
    
    #2. Porezna ispostava
    if report_type=='PDV': 
        if not company.porezna_code:
            raise osv.except_osv(u'Nedostaju podaci!',u'U postavkama poduzeća unesite broj porezne ispostave!')
        res['porezna_code'] = company.porezna_code 
        if not company.porezna:
            raise osv.except_osv(u'Nedostaju podaci!',u'U postavkama poduzeća unesite naziv porezne ispostave!')
        res['porezna']=company.porezna
    
    return res
    
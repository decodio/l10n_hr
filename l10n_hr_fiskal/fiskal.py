#!/usr/bin/python
#coding:utf-8

import sys, time
import os, StringIO, uuid, base64, hashlib, datetime

try:
    import libxml2  # http://www.upfrontsystems.co.za/Members/hedley/my-random-musings/compile-and-install-libxml2-python
except ImportError:
    libxml2 = None
try:
    import xmlsec
except ImportError:
    xmlsec = None
try:
    import suds
    from suds.client import Client
    from suds.plugin import MessagePlugin, PluginContainer
except ImportError:
    suds = None
    Client = None
    MessagePlugin, PluginContainer = object, None
try:
    from M2Crypto import RSA
except ImportError:
    RSA = None

import logging

from openerp.osv import fields, osv, orm
from openerp.tools import config
from datetime import datetime
from pytz import timezone

#Globals
keyFile = certFile = "" 


def received(self, context):
    self.poruka_odgovor = context.reply

    libxml2.initParser()
    libxml2.substituteEntitiesDefault(1)

    xmlsec.init()
    xmlsec.cryptoAppInit(None)
    xmlsec.cryptoInit()

    mngr = xmlsec.KeysMngr()
    xmlsec.cryptoAppDefaultKeysMngrInit(mngr)
    mngr.certLoad(certFile, xmlsec.KeyDataFormatPem, xmlsec.KeyDataTypeTrusted)

    doc = libxml2.parseDoc(context.reply)
    xmlsec.addIDs(doc, doc.getRootElement(), ['Id'])
    node = xmlsec.findNode(doc.getRootElement(), xmlsec.NodeSignature, xmlsec.DSigNs)
    dsig_ctx = xmlsec.DSigCtx(mngr)
    dsig_ctx.verify(node)
    if(dsig_ctx.status == xmlsec.DSigStatusSucceeded):
        self.valid_signature = 1

    xmlsec.cryptoShutdown()
    xmlsec.cryptoAppShutdown()
    xmlsec.shutdown()
    libxml2.cleanupParser()
    return context


# Override failed metode zbog XML cvora koji fali u odgovoru porezne
def failed(self, binding, error):
    return _failed(self, binding, error)


def _failed(self, binding, error):
    status, reason = (error.httpcode, str(error))
    reply = error.fp.read()
    if status == 500:
        if len(reply) > 0:
            reply, result = binding.get_reply(self.method, reply)
            self.last_received(reply)
            plugins = PluginContainer(self.options.plugins)
            ctx = plugins.message.unmarshalled(reply=result)
            result = ctx.reply
            return (status, result)
        else:
            return (status, None)
    if self.options.faults:
        raise Exception((status, reason))
    else:
        return (status, None)
try:
    suds.client.SoapClient.failed = _failed
except AttributeError:  #suds is not installed
    suds = None


def zagreb_now():
    return datetime.now(timezone('Europe/Zagreb'))


def fiskal_num2str(num):
    return "{:-.2f}".format(num)

class DodajPotpis(MessagePlugin):

    def sending(self, context):
        msgtype = "RacunZahtjev"
        if "PoslovniProstorZahtjev" in context.envelope: msgtype = "PoslovniProstorZahtjev"

        doc2 = libxml2.parseDoc(context.envelope)

        zahtjev = doc2.xpathEval('//*[local-name()="%s"]' % msgtype)[0]
        doc2.setRootElement(zahtjev)

        x = doc2.getRootElement().newNs('http://www.apis-it.hr/fin/2012/types/f73', 'tns')

        for i in doc2.xpathEval('//*'):
            i.setNs(x)

        libxml2.initParser()
        libxml2.substituteEntitiesDefault(1)

        xmlsec.init()
        xmlsec.cryptoAppInit(None)
        xmlsec.cryptoInit()

        doc2.getRootElement().setProp('Id', msgtype)
        xmlsec.addIDs(doc2, doc2.getRootElement(), ['Id'])

        signNode = xmlsec.TmplSignature(doc2, xmlsec.transformExclC14NId(), xmlsec.transformRsaSha1Id(), None)

        doc2.getRootElement().addChild(signNode)

        refNode = signNode.addReference(xmlsec.transformSha1Id(), None, None, None)
        refNode.setProp('URI', '#%s' % msgtype)
        refNode.addTransform(xmlsec.transformEnvelopedId())
        refNode.addTransform(xmlsec.transformExclC14NId())

        dsig_ctx = xmlsec.DSigCtx()
        key = xmlsec.cryptoAppKeyLoad(keyFile, xmlsec.KeyDataFormatPem, None, None, None)
        dsig_ctx.signKey = key

        xmlsec.cryptoAppKeyCertLoad(key, certFile, xmlsec.KeyDataFormatPem)
        key.setName(keyFile)

        keyInfoNode = signNode.ensureKeyInfo(None)
        x509DataNode = keyInfoNode.addX509Data()
        xmlsec.addChild(x509DataNode, "X509IssuerSerial")
        xmlsec.addChild(x509DataNode, "X509Certificate")

        dsig_ctx.sign(signNode)

        if dsig_ctx is not None: dsig_ctx.destroy()
        context.envelope = """<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
        <soapenv:Body>""" + doc2.serialize().replace('<?xml version="1.0" encoding="UTF-8"?>','') + """</soapenv:Body></soapenv:Envelope>""" # Ugly hack

        # Shutdown xmlsec-crypto library, ako ne radi HTTPS onda ovo treba zakomentirati da ga ne ugasi prije reda
        xmlsec.cryptoShutdown()
        xmlsec.shutdown()
        libxml2.cleanupParser()

        return context


def SetFiskalFilePaths(key, cert):
    global keyFile, certFile
    keyFile, certFile = key, cert


class Fiskalizacija():

    def __init__(self, msgtype, wsdl, key, cert, cr, uid, oe_obj=None):
        self.set_start_time()
        self.wsdl = wsdl
        self.key = key
        self.cert = cert
        self.msgtype = msgtype
        self.oe_obj = oe_obj
        self.oe_id = oe_obj and oe_obj.id or 0 #openerp id racuna ili pprostora ili 0 za echo i ostalo
        self.cr = cr            #openerp cursor radi log-a 
        self.uid = uid          #openerp cursor radi log-a 
        SetFiskalFilePaths(key, cert)
        self.client2 = Client(wsdl, cache=None, prettyxml=True, timeout=15, faults=False, plugins=[DodajPotpis()]) 
        self.client2.add_prefix('tns', 'http://www.apis-it.hr/fin/2012/types/f73')
        self.zaglavlje = self.client2.factory.create('tns:Zaglavlje')
        if msgtype in ('echo'):
            pass
        elif msgtype in ('prostor_prijava', 'prostor_odjava', 'PoslovniProstor'):
            #self.zaglavlje = self.client2.factory.create('tns:Zaglavlje')
            self.prostor = self.client2.factory.create('tns:PoslovniProstor')
        elif msgtype in ('mp_racun', 'racun', 'racun_ponovo', 'Racun'):
            #self.zaglavlje = self.client2.factory.create('tns:Zaglavlje')
            self.racun = self.client2.factory.create('tns:Racun')
        self.greska = ''

    def time_formated(self):
        tstamp = zagreb_now()
        v_date='%02d.%02d.%02d' % (tstamp.day, tstamp.month, tstamp.year)
        v_datum_vrijeme='%02d.%02d.%02dT%02d:%02d:%02d' % (tstamp.day, tstamp.month, tstamp.year, tstamp.hour, tstamp.minute, tstamp.second)
        v_datum_racun='%02d.%02d.%02d %02d:%02d:%02d' % (tstamp.day, tstamp.month, tstamp.year, tstamp.hour, tstamp.minute, tstamp.second)
        vrijeme={'datum':v_date,                    # vrijeme SAD
                 'datum_vrijeme':v_datum_vrijeme,   # format za zaglavlje XML poruke
                 'datum_racun':v_datum_racun,       # format za ispis na računu
                 'time_stamp':tstamp}               # timestamp, za zapis i izračun vremena obrade
        return vrijeme

    def set_start_time(self):
        self.start_time = self.time_formated()

    def set_stop_time(self):
        self.stop_time = self.time_formated()

    def log_fiskal(self):
        fiskal_prostor_id = invoice_id = pos_order_id = None
        if self.msgtype in ('echo'):
            fiskal_prostor_id = self.oe_id
        elif self.msgtype in ('prostor_prijava', 'prostor_odjava', 'PoslovniProstor'):
            fiskal_prostor_id = self.oe_id

        elif self.msgtype in ('racun', 'racun_ponovo', 'Racun'):
            invoice_id = self.oe_id
        elif self.msgtype in ('mp_racun', 'mp_racun_ponovo', 'MP Racun'):
            pos_order_id = self.oe_id            
        company_id = self.oe_obj and self.oe_obj.company_id and self.oe_obj.company_id.id or 1

        self.set_stop_time()
        t_obrada = self.stop_time['time_stamp'] - self.start_time['time_stamp']
        time_obr='%s.%s s'%(t_obrada.seconds, t_obrada.microseconds)

        self.cr.execute("""
            INSERT INTO fiskal_log(
                         user_id, create_uid, create_date
                        ,name, type, time_stamp
                        ,sadrzaj, odgovor, greska
                        ,fiskal_prostor_id, invoice_id, pos_order_id, time_obr
                        ,company_id )
                VALUES ( %s, %s, %s,  %s, %s, %s,  %s, %s, %s,  %s, %s, %s, %s, %s );
            """, ( self.uid, self.uid, datetime.now(),
                   self.zaglavlje.IdPoruke, self.msgtype, datetime.now(),
                   str(self.poruka_zahtjev), str(self.poruka_odgovor), self.greska,
                   fiskal_prostor_id, invoice_id, pos_order_id, time_obr,
                   company_id
                  ) 
        )

    def echo(self):
        try:
            odgovor = self.client2.service.echo('TEST PORUKA')
            poruka_zahtjev =  self.client2.last_sent().str()
            self.poruka_zahtjev =  self.client2.last_sent()
            self.poruka_odgovor = odgovor
        except:
            return 'No ECHO reply','TEST PORUKA'
            poruka_zahtjev='TEST PORUKA' #TODO pitat suds di je zapelo...
            self.greska ='Ostale greske - Nema Odgovor! '
        finally:
            self.log_fiskal()
        return self.poruka_odgovor

    def posalji_prostor(self):
        res=False
        try:
            odgovor=self.client2.service.poslovniProstor(self.zaglavlje, self.prostor)
            self.poruka_zahtjev =  self.client2.last_sent()
            self.poruka_odgovor = odgovor
            if odgovor[0] == 200:
                res = True
            elif odgovor[0] == 500:
                self.greska = '=>'.join(( odgovor[1]['Greske'][0][0]['SifraGreske'],
                                          odgovor[1]['Greske'][0][0]['PorukaGreske'].replace('http://www.apis-it.hr/fin/2012/types/','')
                                       ))
        except:
            self.greska ='Nepoznata vrsta odgovora!'  #odgovor[0] not in (200,500)
            return 'Error - no reply!', self.poruka
        finally:
            self.log_fiskal()
        return self.poruka_odgovor

    def izracunaj_zastitni_kod(self):
        self.racun.ZastKod = self.get_zastitni_kod(self.racun.Oib,
                                                  self.racun.DatVrijeme,
                                                  str(self.racun.BrRac.BrOznRac),
                                                  self.racun.BrRac.OznPosPr,
                                                  self.racun.BrRac.OznNapUr,
                                                  str(self.racun.IznosUkupno)
                                                  )

    def get_zastitni_kod(self, Oib, DatVrijeme, BrOznRac, OznPosPr, OznNapUr, IznosUkupno):    
        medjurezultat = ''.join((Oib, DatVrijeme, BrOznRac, OznPosPr, OznNapUr, IznosUkupno)) 
        pkey = RSA.load_key(keyFile)
        signature = pkey.sign(hashlib.sha1(medjurezultat).digest())
        return hashlib.md5(signature).hexdigest()

    def posalji_racun(self):
        res = False
        try:
            odgovor = self.client2.service.racuni(self.zaglavlje, self.racun)
            self.poruka_zahtjev = self.client2.last_sent()
            self.poruka_odgovor = odgovor
            if odgovor[0] == 200:
                res = True
                self.greska = ''
            elif odgovor[0] == 500:
                self.greska = '=>'.join((odgovor[1]['Greske'][0][0]['SifraGreske'],
                                         odgovor[1]['Greske'][0][0]['PorukaGreske'].replace('http://www.apis-it.hr/fin/2012/types/', '')
                                       ))
            else:
                self.greska = 'Nepoznata vrsta odgovora!'  # odgovor[0] not in (200,500)
        except Exception, Argument:
            self.poruka_zahtjev = self.client2.last_sent()
            self.poruka_odgovor = Argument
            self.greska = u'Ostale greške - Nema Odgovor! '
        finally:
            self.log_fiskal()
        return res

    def generiraj_poruku(self):
        self.client2.options.nosend = True
        poruka = str(self.client2.service.racuni(self.zaglavlje, self.racun).envelope)
        self.client2.options.nosend = False
        return poruka

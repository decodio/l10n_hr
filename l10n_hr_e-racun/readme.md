E-račun postavke

Extension of OCA/account_invoice_ubl intended and applyed only to companies
from Croatia .
Appled diferences are:
- change of original uom unece categroy
    - UNIT : C62 -> H87 
    - KILOMETER: KTM -> KMT
    - note : IF NOT APPLIED plese check manualy! 
             most e-invoice service providers will not show/recognize if not set correctly
         
- Added support for muktiple schemas and customizations:
    - UBL-2.1-EN19631-B2G - required for all government budged funded companies
    - UBL-2.1-HRINVOICE1-B2B - intended for all other business subjects
   
    - manual selection on document before generating XML file
   
- Added Document type on invoice model 
    - original only knows 380 (Invoice) and 381(CreditNote) 
    added: 82, 325, 383, 384, 386, 387
    - supported document types:
       - Invoice (B2G / B2B)
       - Credit Note (B2G / B2B)
       - Reminder (B2G / B2B)
       
    - manual selection on document before generating XML file    
    
- 

 
Porezi: postaviti UNECE Tax Type, UNECE Tax Category
 - Taxes: 
    - 25%, 13% i 5%  -> Tax type = VAT [Value added tax], Tax Category= S[standard rate]
	- Tuzemni prijenos porezne obveze (reverse charge) 
		- Tax Type= VAT [Value added tax], Tax category= E [exempt from tax] 
		- set-up prema HT-ovoj logici (nestandardizirana postavka, ovisi o vendoru)
																  
-Tvrtka : 
 - tab UBL-EDI: Memorandum data - svi podaci iz zaglavlja/podnožja 
 
   Podaci : telefon, fax, OIB, PDV ID, Bankovni račun, MBS, Članovi uprave, Osnivački kapital 

*Postavke kojima upravlja korisnik:	
			 
-Partner : 
  - tab E-invoice - uputiti korisnika da sam upravlja ovim postavkama:
    - UBL Schema - odabrati adekvatnu schemu za generiranje e-računa (B2B or B2G)
	- FINA registar- provjeriti tip poslovnog subjekta u FINA-inom registru
	- Accounting e-mail- postaviti za primanje notifikacije o primljenom e-računu

-Vrste računa [InvoiceTypeCode]-  uputiti korisnika da sam upravlja ovim postavkama: 
  - 380- Komercijalni račun (normalni račun i storno)
  - 381- Odobrenje   ( xml type, TODO: isto na dnevnik!) 
  - 386- Avansni račun (normalni avans i storno avansa)
   - TODO: postaviti default na dnevnik!
			   
-Refreneca na narudžbenciu [Order reference] 
  - TODO: posebna char polja za unos referenci ručno!
     - 9 tipova: 
         - Order
         - Billing
         - Despatch
         - Receipt
         - Statement
         - Originator
         - Contract
         - Additional Document
         - Project
         
*Interni know how:

-Postavke poreza: 
 - HT, moj E račun i dokumentacija prema Europskoj normi različito definira 
   tuzemni prijenos obveze (za sada ćemo implementirati prema HT-ovoj logici)

-Podaci za plaćanje (bitno kod B2G / oba):
  - Šifra plaćanja [PaymentMeansCode]: hardcoded "42" (uplata na bankovni račun)
  - Kanal [PaymentChannelCode]: hardcoded "IBAN"
  - Poziv na broj [InstructionID]: iz polja reference na računu (oblik se definira na journalu)
  - Opis plaćanja [InstructionNote]: hardcoded "Plaćanje po računu"

-Atribut CurrencyID: 
 - za sada samo HRK (note: HT nudi i EUR)
 - upisuje se podatak sa računa (provjeriti!)
		   
-Atribut unitCode:
               Unit/komad= H87   ( provjeriti podatak: oca koristi C62 )
			   Kilogram= KGM
			   Kilometar= KMT (KTM je depriciated oznaka, provjeriti !)
			   Gram= GRM
			   Metar= MTR
			   Litra= LTR
			   Tona= TNE
			   Kvadratni metar= MTK
			   Sat= HUR
			   Dan= DAY
    - ukoliko jedinica mjere nema upisanu oznaku, u xml će se dodati H87, 
      što i nije full ispravno, ispravnije bi bilo da se traži taj podatak od korisnika (TODO) !
			   
			   
-Popusti: 
  - Global discount (popust na razini dokumenta) 
  - Line discount (popust na razini stavke računa)

Mogućnost generiranja xml datoteke za E-račun servise prema:
  
  - 1. HR-INVOICE1 UBL2.1 standardu - B2B (beta)
  - 2. UBL-2.1-EN19631 standard - B2G (beta)
  
  - preuzimanje datoteka za upload i potpisivanje na različitim servisima

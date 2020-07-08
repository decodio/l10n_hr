.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3


Partner fiscal responsible
=======================

Technical base module extendig partner model for persons (non company partner)
introducing firstname and lastname fields for storing apropriate data
field name is used for company data, and personal names are recomputed during create/write methods

 
opciju za one koji su označeni kao osobe (is_company=False) da im se omogući fiskalna odgovornost na dokumentima
Za takve partnere dodana su poja Ime i Prezime, koja se popunjavaju posebno,
a ostali podaci uzimaju se iz standardnih polja. 

Ovu funkcionalnost koristimo za generiranje XML datoteka za koje se u starom razvoju
dodavalo na res_company podatke o osobama odgovornim za pojedini izvještaj.
 
Proširiti ovlasti iz drugih modula.

Modul će biti korišten kao osnova za druge module 

Usage
=====

Korisnik mora imati ovlast "Fiskal responsible manager" da bi mogao uređivati ili brisati 
korisnika koji je označen kao fiskalno odgovorna osoba.


Bug Tracker
===========

In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback

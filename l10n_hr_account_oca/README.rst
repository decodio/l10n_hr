===============================
Croatia accounting localisation
===============================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

This module is base accounting localisation for Croatia

Configuration
=============

Companies localized for Croatia needs extra data entered to comply to local laws.

Provjerite i dopunite podatke na postavkama poduzeća:

Croatia company parameters:

``Računovodstvo >> Postava >> Croatia Specific >> Poslovni prostori``
``Računovodstvo >> Postava >> Croatia Specific >> Naplatni uređaji``

Dnevnici <b>izlaznih računa moraju</b> imati postavljeno:
 -  Dozvoljeni prostor
 -  Dozvoljeni naplatni uređaji
 -  Korisnici kojima je dozvoljeno izdavanje računa

Korisnik koji treba izdavati račune mora imati postavljeno:
 - Dozvoljeni prostori
 - Dozvoljeni naplatni uređaji
 - zadani naplatni uređaj

Da bi se mogao potvrditi izlazni račun, poslovni prostor mora biti aktivan

polja:
fiskal_responsible_id - odgovorna osoba za račune
  - 1. označiti partnera ( ne usera!) kao fiskal responsible ( može ih biti više)
    i odabrati mu tag RAČUNI, nakon toga možemo na company postaviti generalno odgovornu osobu,
    ili na pojedinom dnevniku odgovornu osobu za taj dnevnik,





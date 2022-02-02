.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Hrvatska : osnovni podaci
=========================

Podaci o poduzeću u raznim tijelima drzavne uprave:

- Br. obveze mirovinsko
- Br. obveze zdravstveno
- Maticni broj

- dev note:
res_company : dodana metoda 'get_l10n_hr_time_formatted '
              za dohvaćanje lokalno formatiranog vremena
              u svim formatima koji se koriste u HR bez obzira
              koja je time zona postavljena na serveru
res_partner: dodana metoda: 'get_oib' za dohvat oib-a partnera

Šifrarnici i popisi:

- NKD 2007 -> modul: l10n_hr_nkd
- Banke u R.Hrvatskoj ->  modul: l10n_hr_bank

Prijevod base modula sa hrvatskim specifičnostima ("state" status ili država, ovisno o polju)
   ( Ivica Dimjašević < ivica.dimjasevic@storm.hr > )

l10n_hr_xml_common - mixin klasa sa metodama za sve HR time formate xml poruka
(pdv, joppd, eracun...)


Bug Tracker
===========

In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback

Credits
=======

Contributors
------------

Goran Kliska (goran.kliska@ecodica.eu)
Davor Bojkić (davor.bojkic@dajmi5.hr)
Ivica Dimjašević (ivica.dimjasevic@storm.hr)

Icon
----








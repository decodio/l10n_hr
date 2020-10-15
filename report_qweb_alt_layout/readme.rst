.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Report QWEB alternative layouts
===============================

Base qweb modification enabling left or right space for printing Partner data,
depending on "windowed envelope" so printed documents will always be on desired side without need to modifiy
report  - module will be needed to extended to modify reports by application - Sale, Accounting, Stoc, Purchase...

Also, module brigs A4-landscape paper format (used for some reports)
and option not to print taxes if company is not tax eglible

Some usefull hints

Format date : <span t-field="o.date_invoice" t-options ='{"format": "dd.MM.yyyy HH:mm"}'></span>
(if different from general language format)

Naziv ispisanog izvjestaja = Spreni kao prefiks naloga:

IRA : (object.state in ('open','paid')) and ((object.number or '').replace('/','') + "_" +
                                            (object.partner_id.name).replace(' ','').replace('.','') + '.pdf')
SO : 'Ponuda-' + (object.name or '').replace('/','') + "-" + (object.partner_id.name).replace(' ','').replace('.','') + '.pdf'

Bug Tracker
===========

In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback

Credits
=======

Contributors
------------

Davor Bojkić (bole@dajmi5.com)

Icon
----

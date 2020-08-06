
# Currency rate extended


Standard Odoo logic assumes one currency rate for all documents.

This module extends OCA currency_rate_update module
with 2 major functionalities:

1. multiple rates - Currency provider with multi rates, or multi provider 

    - Some currency rate providers (mostly banks) use multiple rates per currency: 
      Ask rate, Mid rate and Sell rate... so this module will provide support for 
      multiple rater per provider, as well as possibility to configure multiple providers
      for currency rates
  
2. Per journal rate setup 

    - Possibility to configure which provider/rate will be used for rate fetch in 
      specific journal
  
3. Inverse currency rate
  - despite having OCA currency_rate_inverted module
  the same functionality is implemented in this module using different approach.
  Original module sets inverse rate boolean flag on res_currency model, 
  which in multi-company/multi localziation environment makes a confusing dataset, 
  as well as it is not realy usable if not installed on database setup and before any rates updated.
  
  In this module se have new field rate_inverse wich holds inverse rate for currency 
  and flag to choose which one is shown is on company... so you can select per company how to show currency rates.


Configure and setup

This module should be installed when database setup is done.

1. Accounting -> Configuration -> Currency rate providers
  - setup and configure at least one currency rate provider
  - if you set more than one rate provider, set main provider on company
  

2. Settings -> users and companies -> Companies
  - set default currency rate provider for company
  
3, Accountung -> Configuration -> Journals
  - set per journal specific rate provider



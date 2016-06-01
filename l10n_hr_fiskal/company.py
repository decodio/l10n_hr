
import os, time
from osv import fields, osv, orm
from tools.translate import _



class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {

        'fina_certifikat': fields.many2one('crypto.certificate', string="Fiskal certifikat",
            domain="[('cert_type', 'in', ('fina_demo','fina_prod') )]", #todo company_id
            help="Aktivni FINA certifikat za fiskalizaciju.",
            ),
        'fiskal_prostor': fields.one2many('fiskal.prostor','company_id', string="Poslovni prostori",
            help="Poslovni prostori (fiskalizacija).",
            ),

    }

res_company()

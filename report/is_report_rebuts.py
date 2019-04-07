# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp




#    _name = 'is.of.declaration'
#    
#    _columns = {
#        'name':fields.datetime("Date Heure",required=True),
#        'of_id': fields.many2one('is.of', u"OF", required=True),
#        'qt_bonne': fields.integer('Qt bonne', required=False),
#        'qt_rebut': fields.integer('Qt rebut', required=False),
#        'defaut_id': fields.many2one('is.type.defaut', u"Type de défaut", required=False),
#    }


#    _name = 'is.of'
#    _description = u"Ordre de fabrication"
#    _rec_name = "name"
#    _order='name desc'    #Ordre de tri par defaut des listes
#    
#    _columns = {
#        'name': fields.char('N°OF' , required=True),
#        'moule': fields.char('Moule' , required=False),
#        'nb_empreintes': fields.integer("Nombre d'empreintes", required=False),
#        'coef_cpi': fields.integer("Coefficient CPI", required=False),
#        'code_article': fields.char('Code article' , required=True),
#        'designation': fields.char('Désignation' , required=False),
#        'uc': fields.integer('Qt par UC', required=False),
#        'cout': fields.float('Coût article', digits=(12,4), required=False),
#        'presse_id': fields.many2one('is.presse', u"Presse", required=False),




class is_report_rebuts(osv.osv):
    _name = "is.report.rebuts"
    _description = "Rapport sur les rebuts"
    _auto = False
    _order='date desc'    #Ordre de tri par defaut des listes
    _columns = {
        'date': fields.datetime('Date'),
        'of_id': fields.many2one('is.of', u"OF"),
        'qt_rebut': fields.integer('Qt rebut'),
        'defaut_id': fields.many2one('is.type.defaut', u"Type de défaut"),
        'moule': fields.char('Moule'),
        'presse_id': fields.many2one('is.presse', u"Presse"),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_report_rebuts')
        cr.execute("""
                CREATE OR REPLACE view is_report_rebuts AS (
                SELECT
                        d.id as id,
                        d.name as date,
                        d.of_id as of_id,
                        d.qt_rebut as qt_rebut,
                        d.defaut_id as defaut_id,
                        o.moule as moule,
                        o.presse_id as presse_id
                    FROM is_of_declaration d, is_of o
                    WHERE d.of_id=o.id and d.qt_rebut>0
               )
        """)

is_report_rebuts()




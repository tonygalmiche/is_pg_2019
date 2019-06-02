# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models,fields,api
from openerp.tools.translate import _
import time
import datetime
import os
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


couleurs=[
    ('blanc','Blanc'),
    ('bleu','Bleu'),
    ('orange','Orange'),
    ('rouge','Rouge'),
    ('vert','Vert')
]

colors=[
    ("blanc"  , "white"),
    ("bleu"   , "#5BC0DE"),
    ("orange" , "#F0AD4E"),
    ("rouge"  , "#D9534F"),
    ("vert"   , "#5CB85C"),
]


class is_etat_presse(models.Model):
    _name = 'is.etat.presse'
    _description = u"État Presse"
    _order='name'    #Ordre de tri par defaut des listes

    name             = fields.Char('Intitulé' , required=True)
    production_serie = fields.Boolean('Production série',help='Cocher cette case si cet état correspond à la production série')
    couleur          = fields.Selection(couleurs, 'Couleur', required=False, help="Couleur affichée dans l'interface à la presse")
    ligne            = fields.Integer('Ligne', required=False)
    colonne          = fields.Char('Colonne', required=False)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u"L'intulé doit être unique !"),
    ]
    _defaults = {}


class is_raspberry(models.Model):
    _name = 'is.raspberry'
    _description = u"raspberry"
    _order='name'
    
    name      = fields.Char('Adresse IP' , required=True)
    presse_id = fields.Many2one('is.presse', u"Presse", required=False)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u"L'adresse IP doit être unique !"),
    ]
    
    _defaults = {}


class is_of(models.Model):
    _name = 'is.of'
    _description = u"Ordre de fabrication"
    _rec_name = "name"
    _order='name desc'

    name              = fields.Char('N°OF' , required=True)
    moule             = fields.Char('Moule' , required=False)
    nb_empreintes     = fields.Integer("Nombre d'empreintes", required=False)
    coef_cpi          = fields.Float("Coefficient Theia", required=False, digits=(14,1))
    code_article      = fields.Char('Code article' , required=True)
    categorie         = fields.Char('Catégorie')
    designation       = fields.Char('Désignation' , required=False)
    uc                = fields.Integer('Qt par UC', required=False)
    cout              = fields.Float('Coût article', digits=(12,4), required=False)
    presse_id         = fields.Many2one('is.equipement', u"Presse",  domain=[('type_id.code','=','PE')], required=False, select=False)
    affecte           = fields.Boolean('OF affecté à la presse', select=True,help="Cocher cette case si l'OF est affecté à la presse")
    ordre             = fields.Integer('Ordre', select=True, required=False)
    qt                = fields.Integer('Qt à produire', required=False)
    nb_cycles         = fields.Integer('Nombre de cycles')
    qt_theorique      = fields.Integer('Qt réalisée théorique', required=False)
    qt_declaree       = fields.Integer('Qt déclarée', required=False)
    qt_restante       = fields.Integer('Qt restante', required=False)
    qt_rebut          = fields.Integer('Qt rebuts')
    qt_rebut_theo     = fields.Integer('Qt rebuts théorique')
    taux_rebut        = fields.Float('Taux rebuts (%)'          , digits=(12,2))
    taux_rebut_theo   = fields.Float('Taux rebuts théorique (%)', digits=(12,2))
    cycle_gamme       = fields.Float('Cycle gamme', digits=(12,1), required=False)
    cycle_moyen       = fields.Float('Cycle moyen (10 derniers cycles)', digits=(12,1), required=False)
    cycle_moyen_serie = fields.Float('Cycle moyen', help=u'Temps de production série / nombre de cycles', digits=(12,1), required=False)
    tps_restant       = fields.Float('Temps de production restant', required=False)
    heure_debut       = fields.Datetime('Heure de début de production', select=True, required=False)
    heure_fin         = fields.Datetime('Heure de fin de production', required=False, select=True)
    heure_fin_planning= fields.Datetime('Heure de fin du planning')
    tps_ids           = fields.One2many('is.of.tps'  , 'of_id', u"Répartition des temps d'arrêt")
    rebut_ids         = fields.One2many('is.of.rebut', 'of_id', u"Répartition des rebuts")
    impression_bilan  = fields.Boolean('Bilan imprimé et envoyé par mail', select=True)
    prioritaire       = fields.Boolean('Ordre de fabrication prioritaire')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', u"Le numéro d'OF doit être unique !"),
    ]
    _defaults = {}


    @api.multi
    def get_id_production_serie(self):
        cr = self._cr
        SQL="""
            select id from is_etat_presse where name='Production série'
        """
        cr.execute(SQL)
        result = cr.fetchall()
        id_etat_presse=0
        for row in result:
            id_etat_presse=row[0]
        return id_etat_presse


    @api.multi
    def get_cycle_moyen_serie(self):
        cr = self._cr
        id_production_serie=self.get_id_production_serie()
        nb=len(self)
        ct=0
        for obj in self:
            if obj.qt_theorique!=0:
                ct=ct+1
                SQL="""
                    select
                        ipa.type_arret_id,
                        sum(ipa.tps_arret)
                    from is_presse_arret ipa inner join is_presse_arret_of_rel ipaof on ipa.id=ipaof.is_of_id
                                             inner join is_of                     io on ipaof.is_presse_arret_id=io.id
                    where 
                        ipaof.is_presse_arret_id="""+str(obj.id)+""" and 
                        io.presse_id=ipa.presse_id and 
                        ipa.type_arret_id="""+str(id_production_serie)+"""
                    group by ipa.type_arret_id
                """
                cr.execute(SQL)
                result = cr.fetchall()
                tps_prod_serie=0
                for row in result:
                    tps_prod_serie=row[1]
                cycle_moyen=tps_prod_serie*3600/obj.qt_theorique
                obj.cycle_moyen_serie=cycle_moyen
                _logger.info(str(ct)+u"/"+str(nb)+u" - Calcul cycle moyen "+obj.name+u' ('+str(cycle_moyen)+u')')


    @api.multi
    def get_qt_rebut(self):
        cr = self._cr
        nb=len(self)
        ct=0
        for obj in self:
            ct=ct+1
            SQL="""
                select sum(iod.qt_rebut) 
                from is_of_declaration iod
                where iod.of_id="""+str(obj.id)+"""
            """
            cr.execute(SQL)
            result = cr.fetchall()
            qt_rebut=0
            for row in result:
                qt_rebut=row[0]
            obj.qt_rebut=qt_rebut
            _logger.info(str(ct)+u"/"+str(nb)+u" - Recalcul Qt Rebut "+obj.name+u' ('+str(qt_rebut)+u')')


    @api.multi
    def bilan_fin_of(self):
        cr = self._cr

        id_etat_presse=self.get_id_production_serie()

        nb=len(self)
        ct=0
        for obj in self:
            ct=ct+1
            _logger.info(str(ct)+u"/"+str(nb)+u" - "+obj.name)

            #** Répartition des temps d'arrêt **********************************
            SQL="""
                select
                    ipa.type_arret_id,
                    sum(ipa.tps_arret)
                from is_presse_arret ipa inner join is_presse_arret_of_rel ipaof on ipa.id=ipaof.is_of_id
                                         inner join is_of                     io on ipaof.is_presse_arret_id=io.id
                where ipaof.is_presse_arret_id="""+str(obj.id)+""" and io.presse_id=ipa.presse_id
                group by ipa.type_arret_id
            """
            cr.execute(SQL)
            result = cr.fetchall()
            obj.tps_ids.unlink()
            tps_prod_serie=0
            for row in result:
                vals={
                    'of_id'         : obj.id,
                    'etat_presse_id': row[0],
                    'tps_arret'     : row[1],
                }
                if id_etat_presse==row[0]:
                    tps_prod_serie=row[1]
                self.env['is.of.tps'].create(vals)
            #*******************************************************************

            #** Temps de cycle moyen série *************************************
            if obj.qt_theorique!=0:
                obj.cycle_moyen_serie=tps_prod_serie*3600/obj.qt_theorique
            #*******************************************************************


            #** Répartition des rebuts *****************************************
            SQL="""
                select defaut_id,sum(qt_rebut)::int
                from is_of_declaration 
                where of_id="""+str(obj.id)+""" and qt_rebut is not null and defaut_id is not null
                group by defaut_id;
            """
            cr.execute(SQL)
            result = cr.fetchall()
            obj.rebut_ids.unlink()
            for row in result:
                vals={
                    'of_id'    : obj.id,
                    'defaut_id': row[0],
                    'qt_rebut' : row[1],
                }
                id=self.env['is.of.rebut'].create(vals)
            #*******************************************************************

            #** Quantité déclarée bonne ****************************************
            SQL="""
                select sum(qt_bonne)::int
                from is_of_declaration 
                where of_id="""+str(obj.id)+""" and qt_bonne is not null
            """
            cr.execute(SQL)
            result = cr.fetchall()
            for row in result:
                obj.qt_declaree=row[0]
            #*******************************************************************


            #** Nombre de cycles ***********************************************
            SQL="""
                SELECT count(*) as nb
                FROM is_presse_cycle a inner join is_presse_cycle_of_rel b on id=b.is_of_id
                WHERE is_presse_cycle_id="""+str(obj.id)+"""
                GROUP BY b.is_presse_cycle_id
            """
            cr.execute(SQL)
            result = cr.fetchall()
            for row in result:
                obj.nb_cycles=row[0]
            #*******************************************************************


            #** Taux de rebuts *************************************************
            self.get_qt_rebut()
            qt_bonne = obj.qt_declaree or 0
            qt_rebut = obj.qt_rebut or 0
            taux_rebut=0
            if (qt_bonne+qt_rebut)!=0:
                taux_rebut=100.0*qt_rebut/(qt_bonne+qt_rebut)
            obj.taux_rebut=taux_rebut

            qt_theorique   = obj.qt_theorique or 0
            qt_rebut_theo  = qt_theorique-qt_bonne
            if qt_rebut_theo<0:
                qt_rebut_theo=0
            taux_rebut_theo=0
            if qt_theorique!=0:
                taux_rebut_theo=100.0*qt_rebut_theo/qt_theorique
            obj.qt_rebut_theo   = qt_rebut_theo
            obj.taux_rebut_theo = taux_rebut_theo
            #*******************************************************************


            #** Envoi par mail *************************************************
            if obj.impression_bilan!=True and obj.heure_fin:
                obj.envoyer_par_mail_action()
                obj.impression_bilan=True
            #*******************************************************************
        return []


    @api.multi
    def envoyer_par_mail_action(self):
        for obj in self:
            user  = self.env['res.users'].browse(self._uid)
            email_to=[]
            for row in user.company_id.is_dest_bilan_of_ids:
                if row.email:
                    email_to.append(row.name+u' <'+row.email+u'>')

            name='bilan-fin-of.pdf'

            #** Génération du PDF **********************************************
            pdf = self.env['report'].get_pdf(obj, 'is_pg_2019.bilan_fin_of_report')

            #** Recherche si une pièce jointe est déja associèe ****************
            model=self._name
            attachment_obj = self.env['ir.attachment']
            attachments = attachment_obj.search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            # ******************************************************************

            #** Creation ou modification de la pièce jointe ********************
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       pdf.encode('base64'),
            }
            attachment_id=False
            if attachments:
                for attachment in attachments:
                    attachment.write(vals)
                    attachment_id=attachment.id
            else:
                attachment = attachment_obj.create(vals)
                attachment_id=attachment.id
            #*******************************************************************

            if len(email_to)>0:
                body_html=u"""
                    <html>
                        <head>
                            <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
                        </head>
                        <body>
                            <p>Bonjour, </p>
                            <p>Ci-joint le bilan de l'OF """+obj.name+"""</p>
                        </body>
                    </html>
                """
                email_vals={
                    'subject'       : "[THEIA] Bilan de l'OF "+obj.name,
                    'email_to'      : ';'.join(email_to), 
                    'email_cc'      : "",
                    'email_from'    : "robot@plastigray.com", 
                    'body_html'     : body_html.encode('utf-8'), 
                    'attachment_ids': [(6, 0, [attachment_id])] 
                }
                email_id=self.env['mail.mail'].create(email_vals)
                self.env['mail.mail'].send(email_id)

                _logger.info(u"Envoi par mail du bilan de l'OF "+obj.name+u' à '+u';'.join(email_to))


class is_of_tps(models.Model):
    _name='is.of.tps'
    _order='of_id,tps_arret desc,etat_presse_id'

    @api.depends('etat_presse_id')
    def _couleur(self):
        for obj in self:
            couleur=""
            for color in colors:
                if obj.etat_presse_id.couleur==color[0]:
                    couleur=color[1]
            obj.couleur=couleur

    of_id          = fields.Many2one('is.of', 'N°OF', required=True, ondelete='cascade', readonly=True)
    etat_presse_id = fields.Many2one('is.etat.presse', u"État Presse", required=True)
    couleur        = fields.Char('Couleur', compute='_couleur')
    tps_arret      = fields.Float('Durée dans cet état (H)', digits=(12,4))


class is_of_rebut(models.Model):
    _name='is.of.rebut'
    _order='of_id,qt_rebut desc,defaut_id'

    of_id      = fields.Many2one('is.of', 'N°OF', required=True, ondelete='cascade', readonly=True)
    defaut_id  = fields.Many2one('is.type.defaut', u"Type de défaut", required=True)
    qt_rebut   = fields.Integer('Qt rebut')


class is_of_declaration(models.Model):
    _name = 'is.of.declaration'
    _description = u"Déclaration des fabrications et des rebuts sur les OF"
    _rec_name = "name"
    _order='name desc'

    name       = fields.Datetime("Date Heure",required=True)
    of_id      = fields.Many2one('is.of', u"OF", required=True)
    num_carton = fields.Integer('N°Carton', required=False)
    qt_bonne   = fields.Integer('Qt bonne', required=False)
    qt_rebut   = fields.Integer('Qt rebut', required=False)
    defaut_id  = fields.Many2one('is.type.defaut', u"Type de défaut", required=False)

    _defaults = {}


class is_presse_cycle(models.Model):
    _name = 'is.presse.cycle'
    _description = u"Cycles des presses"
    _rec_name = "date_heure"
    _order='date_heure desc'

    date_heure = fields.Datetime("Date Heure",required=True, select=True)
    #presse_id  = fields.Many2one('is.presse', u"Presse", required=False, select=True)
    presse_id  = fields.Many2one('is.equipement', u"Presse",  domain=[('type_id.code','=','PE')], required=False, select=True)
    of_ids     = fields.Many2many('is.of', 'is_presse_cycle_of_rel', 'is_of_id', 'is_presse_cycle_id', 'OF', readonly=False, required=False)
    
    _sql_constraints = []
    _defaults = {}


class is_presse_arret(models.Model):
    _name = 'is.presse.arret'
    _description = u"Arrêts des presses"
    _rec_name = "date_heure"
    _order='date_heure desc'

    @api.depends('date_heure')
    def _couleur(self):
        for obj in self:
            couleur=""
            for color in colors:
                if obj.type_arret_id.couleur==color[0]:
                    couleur=color[1]
            obj.couleur=couleur

    date_heure    = fields.Datetime("Date Heure",required=True)

    #presse_id     = fields.Many2one('is.presse', u"Presse", required=True)
    presse_id     = fields.Many2one('is.equipement', u"Presse",  domain=[('type_id.code','=','PE')], required=True, select=True)

    type_arret_id = fields.Many2one('is.etat.presse', u"État de la presse", required=True)
    couleur       = fields.Char('Couleur'            , compute='_couleur')
    origine       = fields.Char("Origine du changement d'état")
    tps_arret     = fields.Float("Durée dans cet état", required=False)
    of_ids        = fields.Many2many('is.of', 'is_presse_arret_of_rel', 'is_of_id', 'is_presse_arret_id', 'OF', readonly=False, required=False)

    _sql_constraints = []
    _defaults = {}


class is_type_defaut(models.Model):
    _name = 'is.type.defaut'
    _description = u"Type de défaut des rebuts"
    _order='name'

    name = fields.Char('Type de défaut' , required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u"Le type de défaut doit être unique !"),
    ]
    _defaults = {}


class is_theia_trs(models.Model):
    _name = 'is.theia.trs'
    _description = u"Table calculée pour optimiser temps de réponse analyse TRS"
    _order='presse,date_heure desc,of'

    date_heure   = fields.Datetime(u'Heure début' , required=True, select=True)
    presse       = fields.Char(u'Presse'          , required=True, select=True)
    presse_id    = fields.Many2one('is.equipement', u"Presse", required=True, select=True)
    ilot         = fields.Char(u'Ilot', select=True)
    etat         = fields.Char(u'État'            , required=True, select=True)
    etat_id      = fields.Many2one('is.etat.presse', u"État", required=True, select=True)
    couleur      = fields.Char(u'Couleur Etat')
    of           = fields.Char(u'OF'              , required=True, select=True)
    of_id        = fields.Many2one('is.of', u"OF" , select=True)
    code_article = fields.Char('Code article', select=True)
    categorie    = fields.Char('Catégorie', select=True)
    moule        = fields.Char(u'Moule'           , required=True, select=True)
    coef_theia   = fields.Float("Coefficient Theia", digits=(14,1), defaut=1)
    duree_etat   = fields.Float("Durée dans cet état")
    duree_of     = fields.Float("Durée par OF")


# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models, fields, api
from openerp.tools.translate import _
from collections import defaultdict
from openerp.exceptions import except_orm, Warning, RedirectWarning
# from pytz import timezone
# import pytz
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import base64


class is_ctrl100_operation_standard(models.Model):
    _name        = 'is.ctrl100.operation.standard'
    _description = u"Opérations standard"
    _order       = 'order,name desc'

    name   = fields.Char(u"Opération standard")
    order  = fields.Integer("Ordre")
    active = fields.Boolean("Active", default=True)


class is_ctrl100_gamme_standard(models.Model):
    _name        = 'is.ctrl100.gamme.standard'
    _description = u"Opérations gamme standard"
    _order       = 'operation_standard_id'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        args += ['|', ('active', '=', True), ('active', '=', False)]
        return super(is_ctrl100_gamme_standard, self).search(args, offset, limit, order, count=count)


    gamme_qualite_id       = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité")
    operation_standard_id  = fields.Many2one('is.ctrl100.operation.standard', u"Opération standard")
    active                 = fields.Boolean("Active", default=True)
    #temps_etape            = fields.Float(u"Temps de l'étape  (Seconde / Pièce) ", digits=(14, 2))


class is_ctrl100_operation_specifique(models.Model):
    _name        = 'is.ctrl100.operation.specifique'
    _description = u"Opérations spécifiques"
    _order       = 'operation'

    operation        = fields.Text(u"Opération spécifique")
    photo            = fields.Binary('Photo')
    temps_etape      = fields.Float(u"Temps de l'étape  (Seconde / Pièce) ", digits=(14, 2))
    gamme_qualite_id = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité")


class is_ctrl100_risque_lie(models.Model):
    _name        = 'is.ctrl100.risque.lie'
    _description = u"Risques liés"
    _order       = 'name'

    name             = fields.Char(u"Risque pour le produit engendré par cette reprise", required=True)
    description      = fields.Char(u"Description du verrou mis en place pour répondre à ce risque", required=True)
    gamme_qualite_id = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité", required=True)


class is_ctrl100_typologie_produit(models.Model):
    _name        = 'is.ctrl100.typologie.produit'
    _description = u"Typologie de produit"
    _order       = 'name desc'

    name   = fields.Char(u"Typologie de produit")


class is_ctrl100_gamme_mur_qualite_formation(models.Model):
    _name        = 'is.ctrl100.gamme.mur.qualite.formation'
    _description = u"Gamme mur qualité - Formation"
    _order       = 'gamme_id desc'
    _rec_name    = 'gamme_id'

    gamme_id              = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"Gamme mur qualité", readonly=True)
    createur_id           = fields.Many2one("res.users", u"Créateur", readonly=True)
    operateur_referent_id = fields.Many2one("res.users", u"Opérateur référent", help=u"Cet opérateur pourra gérer les droits sur les saisies", readonly=True)
    operateur_ids         = fields.Many2many("res.users", "is_ctrl100_gamme_mur_qualite_formation_operateur_rel", "formation_id", "operateur_id", u"Operateurs autorisés en saisie et à faire le contrôle")


class is_ctrl100_gamme_mur_qualite(models.Model):
    _name        = 'is.ctrl100.gamme.mur.qualite'
    _description = u"Gamme mur qualité"
    _order       = 'name desc'

    @api.multi
    def get_defautheque_data(self):
        cr = self._cr
        res = False
        defautheque = []
        rec_dict = defaultdict(list)
        defautheque_obj = self.env['is.ctrl100.defautheque']
        for obj in self:
            SQL = """
                select defautheque.name, defautheque.defaut, defautheque.photo, sum(l.nb_rebuts) 
                from is_ctrl100_defaut_line l inner join is_ctrl100_defaut d on d.id=l.defautid 
                                              inner join is_ctrl100_defautheque defautheque on l.defaut_id=defautheque.id
                where 
                    d.moule_dossierf='"""+str(obj.moule_dossierf)+"""'
                group by defautheque.name, defautheque.defaut, defautheque.photo
                order by defautheque.name
            """
            cr.execute(SQL)
            res_ids = cr.fetchall()
            nb_rebuts = 0
            for res in res_ids:
                recdict = {
                    'name'     : res[0],
                    'defaut'   : res[1],
                    'photo'    : res[2],
                    'nb_rebuts': res[3],
                }
                defautheque.append(recdict)
        return defautheque

    @api.multi
    def get_default_data(self):
        res = False
        default = []
        rec_dict = defaultdict(list)
        defaut_obj = self.env['is.ctrl100.defaut']
        for obj in self:
            default_ids = defaut_obj.search([('gamme_id','=',obj.id)])
            for rec in default_ids:
                rec_dict = defaultdict(list)
                tracabilite_nm = ''
                if rec.tracabilite == 'article':
                    tracabilite_nm = rec.product_id.name
                if rec.tracabilite == 'of':
                    tracabilite_nm = rec.production_id.name
                if rec.tracabilite == 'reception':
                    tracabilite_nm = rec.picking_id.name
                if not rec.defautheque_ids:
                    recdict = {
                        'tracabilite_nm': tracabilite_nm,
                        'date_saisie': rec.date_saisie,
                        'controleur': '',
                        'tps_passe': rec.tps_passe,
                        'nb_pieces_controlees': rec.nb_pieces_controlees,
                        'nb_rebuts': '',
                        'nb_repris': '',
                        'defaut_id': ''
                    }
                    default.append(recdict)
                for data in rec.defautheque_ids:
                    if rec.employe_id:
                        controleur=rec.employe_id.name
                    else:
                        controleur=rec.createur_id.name
                    recdict = {
                        'tracabilite_nm': tracabilite_nm,
                        'date_saisie': rec.date_saisie,
                        'controleur': controleur,
                        'tps_passe': rec.tps_passe,
                        'nb_pieces_controlees': rec.nb_pieces_controlees,
                        'nb_rebuts': data.nb_rebuts,
                        'nb_repris': data.nb_repris,
                        'defaut_id': data.defaut_id.name
                    }
                    default.append(recdict)
        return default

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.gamme.mur.qualite') or ''
        res =  super(is_ctrl100_gamme_mur_qualite, self).create(vals)
        #res.creer_modifier_formation()
        return res


#    @api.multi
#    def write(self, vals):
#        res = super(is_ctrl100_gamme_mur_qualite, self).write(vals)
#        for obj in self:
#            obj.creer_modifier_formation()
#        return res


    @api.model
    def default_get(self, default_fields):
        res = super(is_ctrl100_gamme_mur_qualite, self).default_get(default_fields)
        gamme_standard_obj = self.env['is.ctrl100.gamme.standard']
        operation_standard_obj = self.env['is.ctrl100.operation.standard']
        lst = []
        operation_standardids = operation_standard_obj.search([('active', '=', True)])
        for num in operation_standardids:
            lst.append((0,0, {
                'operation_standard_id': num.id, 
                'active': False,
            }))
        res['operation_standard_ids'] = lst
        return res


    @api.returns('self')
    def _get_cout_ctrl_qualite(self):
        user = self.env['res.users'].browse(self.env.uid)
        cout = 0
        if user:
            cout = user.company_id.is_cout_ctrl_qualite or 0
        return cout


    @api.depends('cout_ctrl_qualite','operation_standard_ids','operation_specifique_ids','product_cout_id')
    def _compute_cout(self):
        for obj in self:
            cout_actualise = 0
            if obj.product_cout_id:
                couts = self.env['is.cout'].search([('name', '=', obj.product_cout_id.id)])
                for cout in couts:
                    cout_actualise = cout.cout_act_total
            obj.cout_actualise = cout_actualise

            tps = 0
            #for line in obj.operation_standard_ids:
            #    if line.temps_etape:
            #        tps+=line.temps_etape
            for line in obj.operation_specifique_ids:
                if line.temps_etape:
                    tps+=line.temps_etape

            cadence_previsionnelle = 0
            if tps>0:
                cadence_previsionnelle = 3600/tps
            cout = obj.cout_ctrl_qualite*tps/3600
            obj.cout_previsionnel      = cout
            obj.cadence_previsionnelle = cadence_previsionnelle

            obj.delta_cout = cout_actualise - cout







    @api.depends('mold_id','dossierf_id','product_id')
    def _compute_moule_dossierf(self):
        for obj in self:
            name=''
            if obj.gamme_sur=='moule' and obj.mold_id:
                name = obj.mold_id.name
            if obj.gamme_sur=='dossier_f' and obj.dossierf_id:
                name = obj.dossierf_id.name
            if obj.gamme_sur=='article' and obj.product_id:
                name = obj.product_id.is_mold_dossierf
            obj.moule_dossierf = name


    @api.depends('operateur_referent_id')
    def _compute_formation_id(self):
        for obj in self:
            formation_id = obj.creer_modifier_formation()
            #formation_id = False
            #formation_obj = self.env['is.ctrl100.gamme.mur.qualite.formation']
            #formations = formation_obj.search([('gamme_id', '=', obj.id)])
            #for formation in formations:
            #    formation_id = formation.id
            obj.formation_id = formation_id


    @api.multi
    def get_couleur(self):
        for obj in self:
            couleur='xx'
            if obj.type_gamme=='qualification_process':
                couleur='tdjaune'
            if obj.type_gamme=='reprise':
                couleur='tdorange'
            if obj.type_gamme=='securisation':
                couleur='tdviolet'
            return couleur


    @api.multi
    def creer_modifier_formation(self):
        for obj in self:
            formation_id = False
            if obj.id:
                formation_obj = self.env['is.ctrl100.gamme.mur.qualite.formation']
                formations = formation_obj.search([('gamme_id', '=', obj.id)])
                vals={
                    'gamme_id'             : obj.id,
                    'createur_id'          : obj.create_uid.id,
                    'operateur_referent_id': obj.operateur_referent_id.id,
                }
                if len(formations)>0:
                    formation = formations[0]
                    formation.write(vals)
                else:
                    formation = formation_obj.create(vals)
                formation_id = formation.id
            return formation_id


    @api.onchange('dossierf_id','mold_id')
    def _onchange_moule_dossierf(self):
        lst = []
        defautheque_obj = self.env['is.ctrl100.defautheque']
        self._compute_moule_dossierf()
        self.defautheque_ids = False
        defautheque_ids = defautheque_obj.search([('active', '=', True),'|',('moule_dossierf','=',self.moule_dossierf),('moule_dossierf','=','')])
        for defau in defautheque_ids:
            lst.append((0, 0, {
                'defaut_id': defau.id,
            }))
        self.defautheque_ids = lst


    name                     = fields.Char(u"N°de gamme", readonly=True)
    type_gamme               = fields.Selection([
                                    ("qualification_process", "Qualification Process"),
                                    ("securisation", u"Sécurisation"),
                                    ("reprise", "Reprise"),
                                ], "Type de gamme", required=True)
    description_defaut       = fields.Text(u"Description du défaut")
    commentaire              = fields.Char(u"Commentaire", help=u"Pour pouvoir attribuer un nom à la gamme. Il peut y avoir plusieurs gammes sur un même moule (plusieurs incidents différents par exemple). Ce champ commentaire permet de savoir à quoi correspond chaque gamme")
    gamme_sur                = fields.Selection([
                                    ("moule", "Moule"),
                                    ("dossier_f", "Dossier F"),
                                    ("article", "Article"),
                                ], "Gamme sur", required=True)
    mold_id                  = fields.Many2one("is.mold", "Moule")
    dossierf_id              = fields.Many2one("is.dossierf", "Dossier F")
    product_id               = fields.Many2one("product.product", "Article")
    moule_dossierf           = fields.Char(u"Moule / Dossier F", compute="_compute_moule_dossierf", store=True, readonly=True)
    date_creation            = fields.Date(u"Date de création", copy=False, default=fields.Date.context_today)
    typologie_produit_id     = fields.Many2one("is.ctrl100.typologie.produit", "Typologie de produit")
    date_fin_validite        = fields.Date(u"Date du rappel", required=True)
    operation_standard_ids   = fields.One2many('is.ctrl100.gamme.standard'      , 'gamme_qualite_id', u"Opérations standard")
    operation_specifique_ids = fields.One2many('is.ctrl100.operation.specifique', 'gamme_qualite_id', u"Opérations spécifiques")
    risque_lie_ids           = fields.One2many('is.ctrl100.risque.lie'          , 'gamme_qualite_id', u"Risque pour le produit engendré par cette reprise")
    defautheque_ids          = fields.One2many("is.ctrl100.gamme.defautheque.line", "gamme_id", u"Défauthèque")
    product_cout_id          = fields.Many2one("product.product", "Article pour coût")
    cout_actualise           = fields.Float(u"Coût actualisé", digits=(12, 4), compute="_compute_cout", store=True, readonly=True)
    cout_ctrl_qualite        = fields.Float(u"Coût horaire vendu contrôle qualité", digits=(12, 2), default=_get_cout_ctrl_qualite)
    cout_previsionnel        = fields.Float(u"Coût prévisionnel par pièce", digits=(12, 4), compute="_compute_cout", store=True, readonly=True)
    delta_cout               = fields.Float(u"Delta coût", digits=(12, 4), compute="_compute_cout", store=True, readonly=True)
    justification            = fields.Char(u"Justification")
    cadence_previsionnelle   = fields.Float(u"Cadence de contrôle prévisionnelle (pcs/h)", digits=(12, 2), compute="_compute_cout", store=True, readonly=True)
    operateur_referent_id    = fields.Many2one("res.users", u"Opérateur référent", help=u"Cet opérateur pourra gérer les droits sur les saisies")
    formation_id             = fields.Many2one("is.ctrl100.gamme.mur.qualite.formation", u"Formation", compute="_compute_formation_id", store=True, readonly=True)
    active                   = fields.Boolean(u"Gamme active", default=True)



class is_ctrl100_gamme_defautheque_line(models.Model):
    _name        = 'is.ctrl100.gamme.defautheque.line'
    _description = u"Lignes de la défauthèque de la gamme"
    _order       = 'defaut_id desc'

    gamme_id     = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"Gamme")
    defaut_id    = fields.Many2one("is.ctrl100.defautheque", u"N°défauthèque")
    defaut_text  = fields.Text("Défaut" , related="defaut_id.defaut")
    defaut_photo = fields.Binary("Photo", related="defaut_id.photo")


class is_ctrl100_defautheque(models.Model):
    _name        = 'is.ctrl100.defautheque'
    _description = u"Défauthèque"
    _order       = 'name desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.defautheque') or ''
        res = super(is_ctrl100_defautheque, self).create(vals)
        return res


    @api.depends('dossierf_id','mold_id')
    def _compute_moule_dossierf(self):
        for obj in self:
            name=''
            if obj.mold_id:
                name = obj.mold_id.name
            if obj.dossierf_id:
                name = obj.dossierf_id.name
            obj.moule_dossierf = name




    name            = fields.Char(u"N° du défaut", readonly=True)
    defautheque_sur = fields.Selection([
        ("moule"    , "Moule"),
        ("dossier_f", "Dossier F"),
    ], "Défauthèque sur")
    mold_id        = fields.Many2one("is.mold", "Moule")
    dossierf_id    = fields.Many2one("is.dossierf", "Dossier F")
    moule_dossierf = fields.Char(u"Moule / Dossier F", compute="_compute_moule_dossierf", store=True, readonly=True)
    #gamme_id       = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"N°gamme")
    defaut         = fields.Text(u"Défaut")
    photo          = fields.Binary("Photo")
    active         = fields.Boolean("Active", default=True)


class is_ctrl100_defaut(models.Model):
    _name        = 'is.ctrl100.defaut'
    _description = u"Défauts"
    _order       = 'name desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.defaut') or ''
        res = super(is_ctrl100_defaut, self).create(vals)
        for data in res:
            if data.tps_passe <= 0:
                raise Warning("Temps passé obligatoire")
            if data.nb_pieces_controlees <= 0:
                raise Warning("Nombre de pièces contrôlées obligatoire")
            #for line in data.defautheque_ids:
            #    if line.nb_rebuts <= 0 and line.nb_repris <= 0:
            #        raise Warning("Le nombre de rebuts ou de repris doit être supérieur à 0")
        return res

    @api.multi
    def write(self, vals):
        res = super(is_ctrl100_defaut, self).write(vals)
        for data in self:
            if data.tps_passe <= 0:
                raise Warning("Temps passé obligatoire")
            if data.nb_pieces_controlees <= 0:
                raise Warning("Nombre de pièces contrôlées obligatoire")
            #for line in data.defautheque_ids:
            #    if line.nb_rebuts <= 0 and line.nb_repris <= 0:
            #        raise Warning("Le nombre de rebuts ou de repris doit être supérieur à 0")
        return res

    @api.multi
    def get_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1) or False
        if emp_ids:
            return emp_ids and emp_ids[0].id
        else:
            return False

    @api.onchange('gamme_id')
    def _onchange_gamme_id(self):
        lst = []
        #defautheque_obj = self.env['is.ctrl100.defautheque']
        if not self.gamme_id:
            return {'value': {'defautheque_ids': False}}


        for line in self.gamme_id.defautheque_ids:
            lst.append((0, 0, {
                'defaut_id': line.defaut_id.id,
            }))
        self.defautheque_ids = lst


#        defautheque_ids = defautheque_obj.search([('active', '=', True), ('gamme_id','=',self.gamme_id.id)])
#        for defau in defautheque_ids:
#            lst.append((0, 0, {
#                'defaut_id': defau.id,
#            }))
#        self.defautheque_ids = lst

    @api.returns('self')
    def _get_employee(self):
        id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1) or False
        return id


    @api.depends('gamme_id')
    def _compute_moule_dossierf(self):
        for obj in self:
            moule_dossierf=''
            if obj.gamme_id:
                moule_dossierf = obj.gamme_id.moule_dossierf
            obj.moule_dossierf = moule_dossierf


    name                 = fields.Char(u"N° du défaut")
    gamme_id             = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"N°gamme")
    tracabilite                = fields.Selection([
                                    ("article", "Article"),
                                    ("of", "OF"),
                                    ("reception", "Réception"),
                                ], "Traçabilité")
    product_id           = fields.Many2one("product.product", "Article")
    production_id        = fields.Many2one("mrp.production", "OF")
    picking_id           = fields.Many2one("stock.picking", "Réception", domain=[('picking_type_id.code','=','incoming')])
    moule_dossierf       = fields.Char(u"Moule / Dossier F", compute="_compute_moule_dossierf", store=True, readonly=True)
    createur_id          = fields.Many2one("res.users", "Createur", default=lambda self: self.env.user)
    date_saisie          = fields.Date(u"Date saisie", copy=False, default=fields.Date.context_today)
    nb_pieces_controlees = fields.Integer("Nombre de pièces contrôlées")
    tps_passe            = fields.Float(u"Temps passé (H)", digits=(14, 2))
    employe_id           = fields.Many2one("hr.employee", u"Employé") #, default=_get_employee)
    defautheque_ids      = fields.One2many("is.ctrl100.defaut.line", "defautid", u"Défauthèque")


class is_ctrl100_defaut_line(models.Model):
    _name        = 'is.ctrl100.defaut.line'
    _description = u"Défauts Line"
    _order       = 'defaut_id desc'

    defaut_id    = fields.Many2one("is.ctrl100.defautheque", u"N° du défaut")
    defaut_text  = fields.Text("Défaut" , related="defaut_id.defaut", readonly=True)
    defaut_photo = fields.Binary("Photo", related="defaut_id.photo" , readonly=True)
    nb_rebuts    = fields.Integer("Nombre de rebuts")
    nb_repris    = fields.Integer("Nombre de repris")
    ou_et_quand  = fields.Char("Où et quand le défaut a-t-il été détecté")
    defautid     = fields.Many2one("is.ctrl100.defaut", u"N° du défaut")


class is_ctrl100_rapport_controle(models.Model):
    _name        = 'is.ctrl100.rapport.controle'
    _description = u"Rapport de contrôle"
    _order       = 'gamme_id desc'
    _rec_name    = 'gamme_id'


    @api.multi
    def get_tps_passe(self, gamme_id, date_debut, date_fin):
        tps_passe = 0
        self._cr.execute("\
            select sum(tps_passe) \
            from is_ctrl100_defaut \
            where \
                gamme_id=%s and \
                date_saisie > %s and \
                date_saisie <= %s \
            ", (gamme_id.id,date_debut,date_fin))
        res_ids = self._cr.fetchall()
        for res in res_ids:
            tps_passe += (res[0] or 0)
        return tps_passe


    @api.multi
    def get_default_data(self, gamme_id, date_debut, date_fin):
        quantite_controlee_data = self.get_quantite_controlee(gamme_id, date_debut, date_fin)
        sum_nb_rebuts = 0
        if quantite_controlee_data:
            sum_nb_rebuts = quantite_controlee_data['nb_rebuts']
        defautheque_obj = self.env['is.ctrl100.defautheque']
        self._cr.execute("\
            select is_ctrl100_defaut_line.defaut_id, sum(nb_rebuts) \
            from is_ctrl100_defaut_line inner join is_ctrl100_defaut on is_ctrl100_defaut.id=is_ctrl100_defaut_line.defautid \
            where \
                is_ctrl100_defaut.gamme_id=%s and \
                is_ctrl100_defaut.date_saisie > %s and \
                is_ctrl100_defaut.date_saisie <= %s \
            group by is_ctrl100_defaut_line.defaut_id", (gamme_id.id,date_debut,date_fin))
        listdisct = []
        x = []
        res_ids = self._cr.fetchall()
        seq_no = 1
        popularity = []
        for res in res_ids:
            defautheque_data = defautheque_obj.browse(res[0])
            popularity.append(res[1] or 0)
            perc = 0.0
            if sum_nb_rebuts:
                perc = float(res[1] or 0)*100/sum_nb_rebuts
#                 perc = round(perc, 2)
            recdict = {
                'desc': defautheque_data.name + ' - ' + defautheque_data.defaut or '',
                'name': defautheque_data.name,
                'photo': defautheque_data.photo or '',
                'qty': res[1],
                'perc': perc,
            }
            seq_no += 1
            listdisct.append(recdict)
        
        listdisct = sorted(listdisct, key = lambda i: i['qty'], reverse=True)
        for l in listdisct:
            x.append(l['name'])
        popularity.sort(reverse=True)
        plt.rcParams.update({'font.size': 22})
#         my_dpi=96
#         plt.figure(figsize=(900/my_dpi, 600/my_dpi), dpi=my_dpi)
        x_pos = [i for i, _ in enumerate(x)]
        fig, ax = plt.subplots()




        rects1 = ax.bar(x_pos, popularity, align="center", color='#5dade2')
        plt.xticks(x_pos, x)
        plt.subplots_adjust(left=0.04, right=0.98, top=0.98, bottom=0.04)




        for rect in rects1:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., 0.40*height,
                    height, ha='center', va='bottom', color="white")
#         plt.savefig('/tmp/books_read.png',dpi=my_dpi)
        fig = plt.gcf()
        fig.set_size_inches(18.5, 10.5)
        #fig.savefig('test2png.png', dpi=100)
        fig.savefig('/tmp/books_read.png',dpi=46)
        return listdisct

    @api.multi
    def get_chart_img(self):
        #import base64
        file_nm = '/tmp/books_read.png'
        image = open(file_nm, 'rb')
        image_read = image.read()
        image_64_encode = base64.encodestring(image_read)
        return image_64_encode

    @api.multi
    def remove_chart_img(self):
        file_nm = '/tmp/books_read.png'
        os.system("rm -f "+file_nm)
        return ''

    @api.multi
    def get_quantite_controlee(self, gamme_id, date_debut, date_fin):
        self._cr.execute("select is_ctrl100_defaut_line.defaut_id, coalesce(sum(nb_rebuts),0), coalesce(sum(nb_repris),0) from is_ctrl100_defaut_line inner join is_ctrl100_defaut on is_ctrl100_defaut.id=is_ctrl100_defaut_line.defautid \
            where is_ctrl100_defaut.gamme_id=%s and is_ctrl100_defaut.date_saisie > %s and \
            is_ctrl100_defaut.date_saisie <= %s group by is_ctrl100_defaut_line.defaut_id", (gamme_id.id,date_debut,date_fin))
        listdisct = []
        x = []
        res_ids = self._cr.fetchall()
        nb_rebuts = 0
        nb_repris = 0
        for res in res_ids:
            nb_rebuts += res[1]
            nb_repris += res[2]
        x = {'nb_rebuts':nb_rebuts, 'nb_repris': nb_repris}
        return x

    @api.multi
    def get_quantite(self, date_debut, date_fin):
        quantite = 0
        self._cr.execute("select sum(nb_pieces_controlees) from is_ctrl100_defaut \
            where date_saisie > %s and date_saisie <= %s ", (date_debut,date_fin))
        res_ids = self._cr.fetchall()
        for res in res_ids:
            quantite = res[0]
        return quantite


    gamme_id      = fields.Many2one("is.ctrl100.gamme.mur.qualite", string=u"N°gamme", required=True)
    createur_id   = fields.Many2one("res.users", "Createur", default=lambda self: self.env.user, required=True, writeable=True)
    date_debut    = fields.Date(u"Date de début", required=True)
    date_fin      = fields.Date("Date de fin", required=True)
    afficher_cout = fields.Boolean(u"Afficher le coût horaire et le coût total", default=False)


class is_ctrl100_pareto(models.Model):
    _name        = 'is.ctrl100.pareto'
    _description = u"Pareto"
    _order       = 'date_creation desc'
    _rec_name    = 'date_creation'

    date_creation = fields.Date(u"Date de création", default=lambda *a: fields.datetime.now(), readonly=True)
    createur_id   = fields.Many2one("res.users", u"Créateur", default=lambda self: self.env.user, readonly=True)
    gamme_id      = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"N°gamme")
    date_debut    = fields.Date(u"Date de début")
    date_fin      = fields.Date(u"Date de fin")
    moule         = fields.Char(u"Moule / Dossier F")
    code_pg       = fields.Char(u"Code PG (Partiel)")
    of_debut_id   = fields.Many2one("mrp.production", u"OF début")
    of_fin_id     = fields.Many2one("mrp.production", u"OF fin")


    @api.multi
    def get_chart_img(self):
        cr = self._cr
        for obj in self:
            plt.rcParams.update({'font.size': 22})
            SQL="""
                SELECT d.moule_dossierf,sum(d.tps_passe)
                FROM is_ctrl100_defaut d left outer join product_product  pp on d.product_id=pp.id
                                         left outer join product_template pt on pp.product_tmpl_id=pt.id
                                         left outer join mrp_production   mp on d.production_id=mp.id
                WHERE d.id>0
            """
            if obj.date_debut:
                SQL+=" and d.date_saisie>='"+str(obj.date_debut)+"' "
            if obj.date_fin:
                SQL+=" and d.date_saisie<='"+str(obj.date_fin)+"' "
            if obj.gamme_id:
                SQL+=" and d.gamme_id="+str(obj.gamme_id.id)+" "
            if obj.code_pg:
                SQL+=" and pt.is_code ilike '%"+str(obj.code_pg)+"%' "
            if obj.moule:
                SQL+=" and d.moule_dossierf ilike '%"+str(obj.moule)+"%' "
            if obj.of_debut_id:
                SQL+=" and mp.name>='"+str(obj.of_debut_id.name)+"' "
            if obj.of_fin_id:
                SQL+=" and mp.name<='"+str(obj.of_fin_id.name)+"' "
            SQL+="""
                GROUP BY d.moule_dossierf
                ORDER BY sum(d.tps_passe) desc
            """
            cr.execute(SQL)
            result = cr.fetchall()
            labels=[]
            x_pos=[]
            values=[]
            ct=0
            for row in result:
                labels.append(row[0])
                values.append(row[1])
                x_pos.append(ct)
                ct+=1
            fig, ax = plt.subplots()
            rects1 = ax.bar(x_pos, values, align="center", color='#5dade2')
            plt.xticks(x_pos, labels)
            plt.subplots_adjust(left=0.04, right=0.98, top=0.98, bottom=0.04)
            for rect in rects1:
                height = rect.get_height()
                ax.text(
                    rect.get_x() + rect.get_width()/2., 0.40*height,
                    height, 
                    ha='center', 
                    va='bottom', 
                    color="white"
                )
            fig = plt.gcf()
            fig.set_size_inches(18.5, 10.5)
            filename = '/tmp/ctrl100-parent-'+str(obj.id)+'.png'
            fig.savefig(filename,dpi=46)
            image = open(filename, 'rb')
            image_read = image.read()
            image_64_encode = base64.encodestring(image_read)
            return image_64_encode
        return True



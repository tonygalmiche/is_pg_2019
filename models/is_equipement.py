# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import datetime

class is_equipement_type(models.Model):
    _name = 'is.equipement.type'
    _order = 'name'

    name = fields.Char(u"Type d'équipement", required=True)
    code = fields.Char("Code", required=True)


class is_equipement(models.Model):
    _name = "is.equipement"
    _order = 'type_id,numero_equipement,designation'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for equ in self.browse(cr, uid, ids, context=context):
            name="["+equ.numero_equipement+"] "+equ.designation
            res.append((equ.id,name))
        return res

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, ['|',('numero_equipement','ilike', name),('designation','ilike', name)], limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    type_id                              = fields.Many2one("is.equipement.type", u"Type équipement", required=True)
    numero_equipement                    = fields.Char(u"Numéro d'équipement", required=True)
    designation                          = fields.Char(u"Désignation", required=True)
    database_id                          = fields.Many2one("is.database", "Site", required=True)
    constructeur                         = fields.Char("Constructeur")
    constructeur_serie                   = fields.Char(u"N° constructeur/N°série")
    partner_id                           = fields.Many2one("res.partner", "Fournisseur", domain=[('is_company', '=', True), ('supplier', '=', True)])
    date_fabrication                     = fields.Date("Date de fabrication")
    date_de_fin                          = fields.Date("Date de fin")
    maintenance_preventif_niveau1        = fields.Float(u"Maintenance préventif niveau 1 (h)", digits=(14, 1))
    maintenance_preventif_niveau2        = fields.Float(u"Maintenance préventif niveau 2 (h)", digits=(14, 1))
    maintenance_preventif_niveau3        = fields.Float(u"Maintenance préventif niveau 3 (h)", digits=(14, 1))
    maintenance_preventif_niveau4        = fields.Float(u"Maintenance préventif niveau 4 (h)", digits=(14, 1))
    type_presse_commande                 = fields.Char("Type de presse/type de commande/Generation")
    classe_id                            = fields.Many2one("is.presse.classe", "Classe")
    classe_commerciale                   = fields.Char("Classe commerciale")
    force_fermeture                      = fields.Integer("Force de Fermeture (kg)")
    energie                              = fields.Char("Energie")
    dimension_entre_col_h                = fields.Integer("Dimension entre col H (mn)")
    faux_plateau                         = fields.Integer("Faux plateau (mn)")
    dimension_demi_plateau_h             = fields.Integer("Dimension demi plateau H (mn)")
    dimension_hors_tout_haut             = fields.Integer("Dimension hors tout Haut (mn)")
    dimension_entre_col_v                = fields.Integer("Dimension entre col V (mn)")
    epaisseur_moule_mini_presse          = fields.Integer(u"Épaisseur moule Mini presse (mn)")
    epaisseur_faux_plateau               = fields.Integer(u"Épaisseur faux plateau (mn)")
    epaisseur_moule_maxi                 = fields.Integer(u"Épaisseur moule Maxi (mn)")
    dimension_demi_plateau_v             = fields.Integer("Dimension demi plateau V (mn)")
    dimension_hors_tout_bas              = fields.Integer("Dimension hors tout Bas (mn)")
    coefficient_vis                      = fields.Char("Coefficient de vis")
    type_de_clapet                       = fields.Selection([
            ("1", u"à bague à 2 ailettes"),
            ("2", u"à bague à 3 ailettes"),
            ("3", u"à bague à 4 ailettes"),
            ("4", u"à bille"),
        ], "Type de clapet")
    pression_maximum                     = fields.Integer("Pression Maximum (bar)")
    vis_mn                               = fields.Integer("Ø Vis (mn)")
    volume_injectable                    = fields.Integer("Volume injectable (cm3)")
    course_ejection                      = fields.Integer(u"Course éjection (mn)")
    course_ouverture                     = fields.Integer("Course ouverture (mn)")
    centrage_moule                       = fields.Integer("Ø centrage moule (mn)")
    centrage_presse                      = fields.Integer("Ø centrage presse (mn)")
    hauteur_porte_sol                    = fields.Integer("Hauteur porte / sol (mn)")
    bridage_rapide_entre_axe             = fields.Integer("Bridage rapide entre axe (mn)")
    bridage_rapide_pas                   = fields.Integer("Bridage rapide Pas (mn)")
    bridage_rapide                       = fields.Integer("Bridage rapide Ø (mn)")
    type_huile_hydraulique               = fields.Char("Type huile hydraulique")
    volume_reservoir                     = fields.Integer(u"Volume réservoir (L)")
    type_huile_graissage_centralise      = fields.Char(u"Type huile graissage centralisé")
    nbre_noyau_total                     = fields.Integer("Nbre Noyau Total")
    nbre_noyau_pf                        = fields.Integer("Nbre Noyau PF")
    nbre_noyau_pm                        = fields.Integer("Nbre Noyau PM")
    nbre_circuit_eau                     = fields.Integer("Nbre circuit Eau")
    nbre_zone_de_chauffe_moule           = fields.Integer("Nbre de zone de chauffe moule")
    puissance_electrique_installee       = fields.Float("Puissance Electrique Installee (kw)", digits=(14, 2))
    puissance_electrique_moteur          = fields.Float(u"Puissance électrique moteur (kw)", digits=(14, 2))
    puissance_de_chauffe                 = fields.Float("Puissance de chauffe (kw)", digits=(14, 2))
    compensation_cosinus                 = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Compensation cosinus")
    passage_buse = fields.Integer("Ø Passage Buse (mm)")
    option_rotation_r1                   = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Option Rotation R1 (vert/horiz)")
    option_rotation_r2                   = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Option Rotation R2")
    option_arret_intermediaire           = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Option Arrêt Intermédiaire")
    nbre_circuit_vide                    = fields.Integer("Nbre de circuit de vide")
    nbre_circuit_pression                = fields.Integer("Nbre de circuit pression")
    nbre_dentrees_automate_disponibles   = fields.Integer(u"Nbre d'entrées automate disponibles")
    nbre_de_sorties_automate_disponibles = fields.Integer("Nbre de sorties automate disponibles")
    dimension_chambre                    = fields.Integer("Dimension chambre (mm)")
    nbre_de_voie                         = fields.Integer("Nbre de voie")
    capacite_de_levage                   = fields.Integer("Capacite de Levage (kg)")
    dimension_bande                      = fields.Integer("Dimension bande (mm)")
    dimension_cage                       = fields.Integer("Dimension cage (mm)")
    poids_kg                             = fields.Integer("Poids (kg)")
    affectation_sur_le_site              = fields.Char("Affectation sur le site")
    is_mold_ids                          = fields.Many2many("is.mold", "equipement_mold_rel", "equipement_id", "mold_id", u"Moules affectés")
    is_dossierf_ids                      = fields.Many2many("is.dossierf", "equipement_dossierf_rel", "equipement_id", "dossierf_id", "Dossier F")
    type_de_fluide                       = fields.Selection([
            ("eau", "eau"),
            ("huile", "huile"),
        ], "Type de fluide")
    temperature_maximum                  = fields.Integer(u"Température maximum (°C)")
    puissance_de_refroidissement         = fields.Float("Puissance de refroidissement (kw)", digits=(14, 2))
    debit_maximum                        = fields.Float(u"Débit maximum (L/min) (m3/h)", digits=(14, 2))
    volume_l                             = fields.Integer("Volume (L)")
    option_depresssion                   = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Option déprésssion")
    mesure_debit                         = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Mesure débit (L/mn)")
    base_capacitaire                     = fields.Char("Base Capacitaire")
    emplacement_affectation_pe           = fields.Char("Emplacement / affectation PE")


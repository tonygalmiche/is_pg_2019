# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import datetime


class is_equipement_champ_line(models.Model):
    _name = "is.equipement.champ.line"

    name = fields.Many2one("ir.model.fields", "Champ", domain=[
            ('model_id.model', '=', 'is.equipement'),
            ('ttype', '!=', 'boolean')
        ])
    vsb = fields.Boolean("Visible", default=False)
    obligatoire = fields.Boolean("Obligatoire", default=False)
    equipement_type_id = fields.Many2one("is.equipement.type", "Type Equipement")



class is_equipement_type(models.Model):
    _name = 'is.equipement.type'
    _order = 'name'

    name = fields.Char(u"Type d'équipement", required=True)
    code = fields.Char("Code", required=True)
    champ_line_ids = fields.One2many("is.equipement.champ.line", "equipement_type_id", "Champs")


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

    @api.depends('type_id')
    def _compute(self):
        for obj in self:
            for cl in obj.type_id.champ_line_ids:
                if cl.vsb:
                    setattr(obj, cl.name.name + '_vsb', True)
                if cl.obligatoire:
                    setattr(obj, cl.name.name + '_obl', True)


    type_id                                  = fields.Many2one("is.equipement.type", u"Type équipement", required=True)
    numero_equipement                        = fields.Char(u"Numéro d'équipement", required=True)
    designation                              = fields.Char(u"Désignation", required=True)
    database_id                              = fields.Many2one("is.database", "Site", required=True)
    
    constructeur_vsb                         = fields.Boolean("Constructeur", compute='_compute')
    constructeur_obl                         = fields.Boolean("Constructeur", compute='_compute')
    constructeur                             = fields.Char("Constructeur")
    
    constructeur_serie_vsb                   = fields.Boolean(u"N° constructeur/N°série", compute='_compute')
    constructeur_serie_obl                   = fields.Boolean(u"N° constructeur/N°série", compute='_compute')
    constructeur_serie                       = fields.Char(u"N° constructeur/N°série")
    
    partner_id_vsb                           = fields.Boolean("Fournisseur", compute='_compute')
    partner_id_obl                           = fields.Boolean("Fournisseur", compute='_compute')
    partner_id                               = fields.Many2one("res.partner", "Fournisseur", domain=[('is_company', '=', True), ('supplier', '=', True)])
    
    date_fabrication_vsb                     = fields.Boolean("Date de fabrication", compute='_compute')
    date_fabrication_obl                     = fields.Boolean("Date de fabrication", compute='_compute')
    date_fabrication                         = fields.Date("Date de fabrication")
    
    date_de_fin_vsb                          = fields.Boolean("Date de fin", compute='_compute')
    date_de_fin_obl                          = fields.Boolean("Date de fin", compute='_compute')
    date_de_fin                              = fields.Date("Date de fin")
    
    maintenance_preventif_niveau1_vsb        = fields.Boolean(u"Maintenance préventif niveau 1 (h)", compute='_compute')
    maintenance_preventif_niveau1_obl        = fields.Boolean(u"Maintenance préventif niveau 1 (h)", compute='_compute')
    maintenance_preventif_niveau1            = fields.Float(u"Maintenance préventif niveau 1 (h)", digits=(14, 1))
    
    maintenance_preventif_niveau2_vsb        = fields.Boolean(u"Maintenance préventif niveau 2 (h)", compute='_compute')
    maintenance_preventif_niveau2_obl        = fields.Boolean(u"Maintenance préventif niveau 2 (h)", compute='_compute')
    maintenance_preventif_niveau2            = fields.Float(u"Maintenance préventif niveau 2 (h)", digits=(14, 1))
    
    maintenance_preventif_niveau3_vsb        = fields.Boolean(u"Maintenance préventif niveau 3 (h)", compute='_compute')
    maintenance_preventif_niveau3_obl        = fields.Boolean(u"Maintenance préventif niveau 3 (h)", compute='_compute')
    maintenance_preventif_niveau3            = fields.Float(u"Maintenance préventif niveau 3 (h)", digits=(14, 1))
    
    maintenance_preventif_niveau4_vsb        = fields.Boolean(u"Maintenance préventif niveau 4 (h)", compute='_compute')
    maintenance_preventif_niveau4_obl        = fields.Boolean(u"Maintenance préventif niveau 4 (h)", compute='_compute')
    maintenance_preventif_niveau4            = fields.Float(u"Maintenance préventif niveau 4 (h)", digits=(14, 1))
    
    type_presse_commande_vsb                 = fields.Boolean("Type de presse/type de commande/Generation", compute='_compute')
    type_presse_commande_obl                 = fields.Boolean("Type de presse/type de commande/Generation", compute='_compute')
    type_presse_commande                     = fields.Char("Type de presse/type de commande/Generation")
    
    classe_id_vsb                            = fields.Boolean("Classe", compute='_compute')
    classe_id_obl                            = fields.Boolean("Classe", compute='_compute')
    classe_id                                = fields.Many2one("is.presse.classe", "Classe")
    
    classe_commerciale_vsb                   = fields.Boolean("Classe commerciale", compute='_compute')
    classe_commerciale_obl                   = fields.Boolean("Classe commerciale", compute='_compute')
    classe_commerciale                       = fields.Char("Classe commerciale")
    
    force_fermeture_vsb                      = fields.Boolean("Force de Fermeture (kg)", compute='_compute')
    force_fermeture_obl                      = fields.Boolean("Force de Fermeture (kg)", compute='_compute')
    force_fermeture                          = fields.Integer("Force de Fermeture (kg)")
    
    energie_vsb                              = fields.Boolean("Energie", compute='_compute')
    energie_obl                              = fields.Boolean("Energie", compute='_compute')
    energie                                  = fields.Char("Energie")
    
    dimension_entre_col_h_vsb                = fields.Boolean("Dimension entre col H (mn)", compute='_compute')
    dimension_entre_col_h_obl                = fields.Boolean("Dimension entre col H (mn)", compute='_compute')
    dimension_entre_col_h                    = fields.Integer("Dimension entre col H (mn)")
    
    faux_plateau_vsb                         = fields.Boolean("Faux plateau (mn)", compute='_compute')
    faux_plateau_obl                         = fields.Boolean("Faux plateau (mn)", compute='_compute')
    faux_plateau                             = fields.Integer("Faux plateau (mn)")
    
    dimension_demi_plateau_h_vsb             = fields.Boolean("Dimension demi plateau H (mn)", compute='_compute')
    dimension_demi_plateau_h_obl             = fields.Boolean("Dimension demi plateau H (mn)", compute='_compute')
    dimension_demi_plateau_h                 = fields.Integer("Dimension demi plateau H (mn)")
    
    dimension_hors_tout_haut_vsb             = fields.Boolean("Dimension hors tout Haut (mn)", compute='_compute')
    dimension_hors_tout_haut_obl             = fields.Boolean("Dimension hors tout Haut (mn)", compute='_compute')
    dimension_hors_tout_haut                 = fields.Integer("Dimension hors tout Haut (mn)")
    
    dimension_entre_col_v_vsb                = fields.Boolean("Dimension entre col V (mn)", compute='_compute')
    dimension_entre_col_v_obl                = fields.Boolean("Dimension entre col V (mn)", compute='_compute')
    dimension_entre_col_v                    = fields.Integer("Dimension entre col V (mn)")
    
    epaisseur_moule_mini_presse_vsb          = fields.Boolean(u"Épaisseur moule Mini presse (mn)", compute='_compute')
    epaisseur_moule_mini_presse_obl          = fields.Boolean(u"Épaisseur moule Mini presse (mn)", compute='_compute')
    epaisseur_moule_mini_presse              = fields.Integer(u"Épaisseur moule Mini presse (mn)")
    
    epaisseur_faux_plateau_vsb               = fields.Boolean(u"Épaisseur faux plateau (mn)", compute='_compute')
    epaisseur_faux_plateau_obl               = fields.Boolean(u"Épaisseur faux plateau (mn)", compute='_compute')
    epaisseur_faux_plateau                   = fields.Integer(u"Épaisseur faux plateau (mn)")
    
    epaisseur_moule_maxi_vsb                 = fields.Boolean(u"Épaisseur moule Maxi (mn)", compute='_compute')
    epaisseur_moule_maxi_obl                 = fields.Boolean(u"Épaisseur moule Maxi (mn)", compute='_compute')
    epaisseur_moule_maxi                     = fields.Integer(u"Épaisseur moule Maxi (mn)")
    
    dimension_demi_plateau_v_vsb             = fields.Boolean("Dimension demi plateau V (mn)", compute='_compute')
    dimension_demi_plateau_v_obl             = fields.Boolean("Dimension demi plateau V (mn)", compute='_compute')
    dimension_demi_plateau_v                 = fields.Integer("Dimension demi plateau V (mn)")
    
    dimension_hors_tout_bas_vsb              = fields.Boolean("Dimension hors tout Bas (mn)", compute='_compute')
    dimension_hors_tout_bas_obl              = fields.Boolean("Dimension hors tout Bas (mn)", compute='_compute')
    dimension_hors_tout_bas                  = fields.Integer("Dimension hors tout Bas (mn)")
    
    coefficient_vis_vsb                      = fields.Boolean("Coefficient de vis", compute='_compute')
    coefficient_vis_obl                      = fields.Boolean("Coefficient de vis", compute='_compute')
    coefficient_vis                          = fields.Char("Coefficient de vis")
    
    type_de_clapet_vsb                       = fields.Boolean("Type de clapet", compute='_compute')
    type_de_clapet_obl                       = fields.Boolean("Type de clapet", compute='_compute')
    type_de_clapet                           = fields.Selection([
            ("1", u"à bague à 2 ailettes"),
            ("2", u"à bague à 3 ailettes"),
            ("3", u"à bague à 4 ailettes"),
            ("4", u"à bille"),
        ], "Type de clapet")
    
    pression_maximum_vsb                     = fields.Boolean("Pression Maximum (bar)", compute='_compute')
    pression_maximum_obl                     = fields.Boolean("Pression Maximum (bar)", compute='_compute')
    pression_maximum                         = fields.Integer("Pression Maximum (bar)")
    
    vis_mn_vsb                               = fields.Boolean("Ø Vis (mn)", compute='_compute')
    vis_mn_obl                               = fields.Boolean("Ø Vis (mn)", compute='_compute')
    vis_mn                                   = fields.Integer("Ø Vis (mn)")
    
    volume_injectable_vsb                    = fields.Boolean("Volume injectable (cm3)", compute='_compute')
    volume_injectable_obl                    = fields.Boolean("Volume injectable (cm3)", compute='_compute')
    volume_injectable                        = fields.Integer("Volume injectable (cm3)")
    
    course_ejection_vsb                      = fields.Boolean(u"Course éjection (mn)", compute='_compute')
    course_ejection_obl                      = fields.Boolean(u"Course éjection (mn)", compute='_compute')
    course_ejection                          = fields.Integer(u"Course éjection (mn)")
    
    course_ouverture_vsb                     = fields.Boolean("Course ouverture (mn)", compute='_compute')
    course_ouverture_obl                     = fields.Boolean("Course ouverture (mn)", compute='_compute')
    course_ouverture                         = fields.Integer("Course ouverture (mn)")
    
    centrage_moule_vsb                       = fields.Boolean("Ø centrage moule (mn)", compute='_compute')
    centrage_moule_obl                       = fields.Boolean("Ø centrage moule (mn)", compute='_compute')
    centrage_moule                           = fields.Integer("Ø centrage moule (mn)")
    
    centrage_presse_vsb                      = fields.Boolean("Ø centrage presse (mn)", compute='_compute')
    centrage_presse_obl                      = fields.Boolean("Ø centrage presse (mn)", compute='_compute')
    centrage_presse                          = fields.Integer("Ø centrage presse (mn)")
    
    hauteur_porte_sol_vsb                    = fields.Boolean("Hauteur porte / sol (mn)", compute='_compute')
    hauteur_porte_sol_obl                    = fields.Boolean("Hauteur porte / sol (mn)", compute='_compute')
    hauteur_porte_sol                        = fields.Integer("Hauteur porte / sol (mn)")
    
    bridage_rapide_entre_axe_vsb             = fields.Boolean("Bridage rapide entre axe (mn)", compute='_compute')
    bridage_rapide_entre_axe_obl             = fields.Boolean("Bridage rapide entre axe (mn)", compute='_compute')
    bridage_rapide_entre_axe                 = fields.Integer("Bridage rapide entre axe (mn)")
    
    bridage_rapide_pas_vsb                   = fields.Boolean("Bridage rapide Pas (mn)", compute='_compute')
    bridage_rapide_pas_obl                   = fields.Boolean("Bridage rapide Pas (mn)", compute='_compute')
    bridage_rapide_pas                       = fields.Integer("Bridage rapide Pas (mn)")
    
    bridage_rapide_vsb                       = fields.Boolean("Bridage rapide Ø (mn)", compute='_compute')
    bridage_rapide_obl                       = fields.Boolean("Bridage rapide Ø (mn)", compute='_compute')
    bridage_rapide                           = fields.Integer("Bridage rapide Ø (mn)")
    
    type_huile_hydraulique_vsb               = fields.Boolean("Type huile hydraulique", compute='_compute')
    type_huile_hydraulique_obl               = fields.Boolean("Type huile hydraulique", compute='_compute')
    type_huile_hydraulique                   = fields.Char("Type huile hydraulique")
    
    volume_reservoir_vsb                     = fields.Boolean(u"Volume réservoir (L)", compute='_compute')
    volume_reservoir_obl                     = fields.Boolean(u"Volume réservoir (L)", compute='_compute')
    volume_reservoir                         = fields.Integer(u"Volume réservoir (L)")
    
    type_huile_graissage_centralise_vsb      = fields.Boolean(u"Type huile graissage centralisé", compute='_compute')
    type_huile_graissage_centralise_obl      = fields.Boolean(u"Type huile graissage centralisé", compute='_compute')
    type_huile_graissage_centralise          = fields.Char(u"Type huile graissage centralisé")
    
    nbre_noyau_total_vsb                     = fields.Boolean("Nbre Noyau Total", compute='_compute')
    nbre_noyau_total_obl                     = fields.Boolean("Nbre Noyau Total", compute='_compute')
    nbre_noyau_total                         = fields.Integer("Nbre Noyau Total")
    
    nbre_noyau_pf_vsb                        = fields.Boolean("Nbre Noyau PF", compute='_compute')
    nbre_noyau_pf_obl                        = fields.Boolean("Nbre Noyau PF", compute='_compute')
    nbre_noyau_pf                            = fields.Integer("Nbre Noyau PF")
    
    nbre_noyau_pm_vsb                        = fields.Boolean("Nbre Noyau PM", compute='_compute')
    nbre_noyau_pm_obl                        = fields.Boolean("Nbre Noyau PM", compute='_compute')
    nbre_noyau_pm                            = fields.Integer("Nbre Noyau PM")
    
    nbre_circuit_eau_vsb                     = fields.Boolean("Nbre circuit Eau", compute='_compute')
    nbre_circuit_eau_obl                     = fields.Boolean("Nbre circuit Eau", compute='_compute')
    nbre_circuit_eau                         = fields.Integer("Nbre circuit Eau")
    
    nbre_zone_de_chauffe_moule_vsb           = fields.Boolean("Nbre de zone de chauffe moule", compute='_compute')
    nbre_zone_de_chauffe_moule_obl           = fields.Boolean("Nbre de zone de chauffe moule", compute='_compute')
    nbre_zone_de_chauffe_moule               = fields.Integer("Nbre de zone de chauffe moule")
    
    puissance_electrique_installee_vsb       = fields.Boolean("Puissance Electrique Installee (kw)", compute='_compute')
    puissance_electrique_installee_obl       = fields.Boolean("Puissance Electrique Installee (kw)", compute='_compute')
    puissance_electrique_installee           = fields.Float("Puissance Electrique Installee (kw)", digits=(14, 2))
    
    puissance_electrique_moteur_vsb          = fields.Boolean(u"Puissance électrique moteur (kw)", compute='_compute')
    puissance_electrique_moteur_obl          = fields.Boolean(u"Puissance électrique moteur (kw)", compute='_compute')
    puissance_electrique_moteur              = fields.Float(u"Puissance électrique moteur (kw)", digits=(14, 2))
    
    puissance_de_chauffe_vsb                 = fields.Boolean("Puissance de chauffe (kw)", compute='_compute')
    puissance_de_chauffe_obl                 = fields.Boolean("Puissance de chauffe (kw)", compute='_compute')
    puissance_de_chauffe                     = fields.Float("Puissance de chauffe (kw)", digits=(14, 2))
    
    compensation_cosinus_vsb                 = fields.Boolean("Compensation cosinus", compute='_compute')
    compensation_cosinus_obl                 = fields.Boolean("Compensation cosinus", compute='_compute')
    compensation_cosinus                     = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Compensation cosinus")
    
    passage_buse_vsb                         = fields.Boolean("Ø Passage Buse (mm)", compute='_compute')
    passage_buse_obl                         = fields.Boolean("Ø Passage Buse (mm)", compute='_compute')
    passage_buse = fields.Integer("Ø Passage Buse (mm)")
    
    option_rotation_r1_vsb                   = fields.Boolean("Option Rotation R1 (vert/horiz)", compute='_compute')
    option_rotation_r1_obl                   = fields.Boolean("Option Rotation R1 (vert/horiz)", compute='_compute')
    option_rotation_r1                       = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Option Rotation R1 (vert/horiz)")
    
    option_rotation_r2_vsb                   = fields.Boolean("Option Rotation R2", compute='_compute')
    option_rotation_r2_obl                   = fields.Boolean("Option Rotation R2", compute='_compute')
    option_rotation_r2                       = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], "Option Rotation R2")
    
    option_arret_intermediaire_vsb           = fields.Boolean(u"Option Arrêt Intermédiaire", compute='_compute')
    option_arret_intermediaire_obl           = fields.Boolean(u"Option Arrêt Intermédiaire", compute='_compute')
    option_arret_intermediaire               = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Option Arrêt Intermédiaire")
    
    nbre_circuit_vide_vs                     = fields.Boolean("Nbre de circuit de vide", compute='_compute')
    nbre_circuit_vide_obl                    = fields.Boolean("Nbre de circuit de vide", compute='_compute')
    nbre_circuit_vide                        = fields.Integer("Nbre de circuit de vide")
    
    nbre_circuit_pression_vsb                = fields.Boolean("Nbre de circuit pression", compute='_compute')
    nbre_circuit_pression_obl                = fields.Boolean("Nbre de circuit pression", compute='_compute')
    nbre_circuit_pression                    = fields.Integer("Nbre de circuit pression")
    
    nbre_dentrees_automate_disponibles_vsb   = fields.Boolean(u"Nbre d'entrées automate disponibles", compute='_compute')
    nbre_dentrees_automate_disponibles_obl   = fields.Boolean(u"Nbre d'entrées automate disponibles", compute='_compute')
    nbre_dentrees_automate_disponibles       = fields.Integer(u"Nbre d'entrées automate disponibles")
    
    nbre_de_sorties_automate_disponibles_vsb = fields.Boolean("Nbre de sorties automate disponibles", compute='_compute')
    nbre_de_sorties_automate_disponibles_obl = fields.Boolean("Nbre de sorties automate disponibles", compute='_compute')
    nbre_de_sorties_automate_disponibles     = fields.Integer("Nbre de sorties automate disponibles")
    
    dimension_chambre_vsb                    = fields.Boolean("Dimension chambre (mm)", compute='_compute')
    dimension_chambre_obl                    = fields.Boolean("Dimension chambre (mm)", compute='_compute')
    dimension_chambre                        = fields.Integer("Dimension chambre (mm)")
    
    nbre_de_voie_vsb                         = fields.Boolean("Nbre de voie", compute='_compute')
    nbre_de_voie_obl                         = fields.Boolean("Nbre de voie", compute='_compute')
    nbre_de_voie                             = fields.Integer("Nbre de voie")
    
    capacite_de_levage_vsb                   = fields.Boolean("Capacite de Levage (kg)", compute='_compute')
    capacite_de_levage_obl                   = fields.Boolean("Capacite de Levage (kg)", compute='_compute')
    capacite_de_levage                       = fields.Integer("Capacite de Levage (kg)")
    
    dimension_bande_vsb                      = fields.Boolean("Dimension bande (mm)", compute='_compute')
    dimension_bande_obl                      = fields.Boolean("Dimension bande (mm)", compute='_compute')
    dimension_bande                          = fields.Integer("Dimension bande (mm)")
    
    dimension_cage_vsb                       = fields.Boolean("Dimension cage (mm)", compute='_compute')
    dimension_cage_obl                       = fields.Boolean("Dimension cage (mm)", compute='_compute')
    dimension_cage                           = fields.Integer("Dimension cage (mm)")
    
    poids_kg_vsb                             = fields.Boolean("Poids (kg)", compute='_compute')
    poids_kg_obl                             = fields.Boolean("Poids (kg)", compute='_compute')
    poids_kg                                 = fields.Integer("Poids (kg)")
    
    affectation_sur_le_site_vsb              = fields.Boolean("Affectation sur le site", compute='_compute')
    affectation_sur_le_site_obl              = fields.Boolean("Affectation sur le site", compute='_compute')
    affectation_sur_le_site                  = fields.Char("Affectation sur le site")
    
    is_mold_ids_vsb                          = fields.Boolean(u"Moules affectés", compute='_compute')
    is_mold_ids_obl                          = fields.Boolean(u"Moules affectés", compute='_compute')
    is_mold_ids                              = fields.Many2many("is.mold", "equipement_mold_rel", "equipement_id", "mold_id", u"Moules affectés")
    
    is_dossierf_ids_vsb                      = fields.Boolean("Dossier F", compute='_compute')
    is_dossierf_ids_obl                      = fields.Boolean("Dossier F", compute='_compute')
    is_dossierf_ids                          = fields.Many2many("is.dossierf", "equipement_dossierf_rel", "equipement_id", "dossierf_id", "Dossier F")
    
    type_de_fluide_vsb                       = fields.Boolean("Type de fluide", compute='_compute')
    type_de_fluide_obl                       = fields.Boolean("Type de fluide", compute='_compute')
    type_de_fluide                           = fields.Selection([
            ("eau", "eau"),
            ("huile", "huile"),
        ], "Type de fluide")
    
    temperature_maximum_vsb                  = fields.Boolean(u"Température maximum (°C)", compute='_compute')
    temperature_maximum_obl                  = fields.Boolean(u"Température maximum (°C)", compute='_compute')
    temperature_maximum                      = fields.Integer(u"Température maximum (°C)")
    
    puissance_de_refroidissement_vsb         = fields.Boolean("Puissance de refroidissement (kw)", compute='_compute')
    puissance_de_refroidissement_obl         = fields.Boolean("Puissance de refroidissement (kw)", compute='_compute')
    puissance_de_refroidissement             = fields.Float("Puissance de refroidissement (kw)", digits=(14, 2))
    
    debit_maximum_vsb                        = fields.Boolean(u"Débit maximum (L/min) (m3/h)", compute='_compute')
    debit_maximum_obl                        = fields.Boolean(u"Débit maximum (L/min) (m3/h)", compute='_compute')
    debit_maximum                            = fields.Float(u"Débit maximum (L/min) (m3/h)", digits=(14, 2))
    
    volume_l_vsb                             = fields.Boolean("Volume (L)", compute='_compute')
    volume_l_obl                             = fields.Boolean("Volume (L)", compute='_compute')
    volume_l                                 = fields.Integer("Volume (L)")
    
    option_depresssion_vsb                   = fields.Boolean(u"Option déprésssion", compute='_compute')
    option_depresssion_obl                   = fields.Boolean(u"Option déprésssion", compute='_compute')
    option_depresssion                       = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Option déprésssion")
    
    mesure_debit_vsb                         = fields.Boolean(u"Mesure débit (L/mn)", compute='_compute')
    mesure_debit_obl                         = fields.Boolean(u"Mesure débit (L/mn)", compute='_compute')
    mesure_debit                             = fields.Selection([
            ("oui", "oui"),
            ("non", "non"),
        ], u"Mesure débit (L/mn)")
    
    base_capacitaire_vsb                     = fields.Boolean("Base Capacitaire", compute='_compute')
    base_capacitaire_obl                     = fields.Boolean("Base Capacitaire", compute='_compute')
    base_capacitaire                         = fields.Char("Base Capacitaire")
    
    emplacement_affectation_pe_vsb           = fields.Boolean("Emplacement / affectation PE", compute='_compute')
    emplacement_affectation_pe_obl           = fields.Boolean("Emplacement / affectation PE", compute='_compute')
    emplacement_affectation_pe               = fields.Char("Emplacement / affectation PE")


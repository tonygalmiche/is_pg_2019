# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import time
import datetime


class is_mold(models.Model):
    _inherit = 'is.mold'

    largeur   = fields.Integer(u"Largeur (mm)")
    hauteur   = fields.Integer(u"Hauteur (mm)")
    epaisseur = fields.Integer(u"Epaisseur (mm)")

    largeur_hors_tout   = fields.Integer(u"Largeur hors tout (mm)")
    hauteur_hors_tout   = fields.Integer(u"Hauteur hors tout (mm)")
    epaisseur_hors_tout = fields.Integer(u"Epaisseur hors tout (mm)")

    poids = fields.Integer(u"Poids (Kg)")

    recu_de_buse = fields.Selection([
            ("standard"  , u"Standard = cône 90°"),
            ("specifique", u"Spécifique"),
        ], "Reçu de buse")
    recu_de_buse_specifique = fields.Char(u"Reçu de buse spécifique")

    diametre_entree_cheminee = fields.Selection([
            ("01", u"1"),
            ("02", u"2"),
            ("03", u"3"),
            ("04", u"4 = Standard Plastigray"),
            ("05", u"5 = Standard Plastigray"),
            ("06", u"6 = Standard Plastigray"),
            ("07", u"7"),
            ("08", u"8"),
            ("09", u"9"),
            ("10", u"10"),
        ], u"Diamètre entrée cheminée")

    bridage = fields.Selection([
            ("manuel"  , u"manuel"),
            ("auto210" , u"Automatique sur le carré 210 M20 / Automatic on square 210 M20"),
            ("auto310" , u"Automatique sur le carré 310 M30 / Automatic on square 310 M30"),
            ("auto490" , u"Automatique sur le carré 490 M36 / Automatic on square 490 M36"),
            ("magnetic", u"Magnétique / Magnetic"),
        ], "Bridage")

    ejection = fields.Selection([
            ("standard"  , u"Standard Plastigray"),
            ("specifique", u"Spécifique"),
        ], "Ejection")
    ejection_specifique = fields.Char(u"Ejection spécifique")

    rondelle_centrage_fixe = fields.Selection([
            ("standard"  , u"Standard Plastigray : 100"),
            ("specifique", u"Spécifique"),
        ], "Rondelle de centrage - Partie fixe")
    rondelle_centrage_fixe_specifique = fields.Char(u"Rondelle de centrage - Partie fixe spécifique")

    rondelle_centrage_mobile = fields.Selection([
            ("standard"  , u"Standard Plastigray : 100"),
            ("specifique", u"Spécifique"),
        ], "Rondelle de centrage - Partie mobile")
    rondelle_centrage_mobile_specifique = fields.Char(u"Rondelle de centrage - Partie mobile spécifique")

    presse_ids = fields.Many2many("is.equipement", "is_mold_presse_rel", "mold_id", "presse_id", u"Presses", domain=[('type_id.code', '=', 'PE')])

    nb_noyaux_fixe = fields.Selection([
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ], "Nombre de noyaux - Partie fixe")
    nb_noyaux_mobile = fields.Selection([
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ], "Nombre de noyaux - Partie mobile")


    cinematique = fields.Selection([
            ("standard"       , u"Standard"),
            ("avant_ejection" , u"Moule avec noyau, avec sortie avant éjection"),
            ("avant_ouverture", u"Moule avec noyau, avec sortie avant ouverture"),
            ("specifique"     , u"Spécifique"),
        ], "Cinématique")
    cinematique_standard = fields.Selection([
            ("moule_ouvert", "Moule ouvert avec ejection contrôle rentré"),
            ("fermeture"   , "Fermeture puis verrouillage"),
            ("cycle"       , "Cycle injection"),
            ("ouverture"   , "Ouverture"),
            ("sortie"      , "Sortie ejection"),
            ("rentree"     , "Rentrée éjection"),
        ], "Cinématique - Standard")
    cinematique_avant_ejection = fields.Selection([
            ("ouvert"   , "moule ouvert avec éjection contrôle rentrée et noyau sorti"),
            ("fermeture", "fermeture puis verrouillage"),
            ("cycle"    , "cycle injection"),
            ("sortie"   , "sortie noyau avec contrôle sortie"),
            ("ouverture", "ouverture"),
            ("sortie"   , "sortie ejection"),
            ("rentree"  , "rentrée éjection"),
        ], "Cinématique - Moule avec noyau, avec sortie avant éjection")
    cinematique_avant_ouverture = fields.Selection([
            ("ouvert"         , "moule ouvert avec éjection contrôle rentré et noyau 1 rentré"),
            ("fermeture"      , "fermeture puis verrouillage"),
            ("cycle"          , "cycle injection"),
            ("ouverture"      , "ouverture"),
            ("sortie_noyau"   , "sortie noyau 1 avec contrôle sortie"),
            ("sortie_ejection", "sortie éjection puis rentrée éjection avec contrôle rentré"),
            ("rentre_noyau"   , "rentré noyau 1 avec contrôle rentré"),
        ], "Cinématique - Moule avec noyau, avec sortie avant ouverture")
    cinematique_specifique = fields.Char(u"Cinématique - Spécifique")

    fiche_description_commentaire = fields.Text(u"Commentaire")

    fiche_description_indice        = fields.Char(u"Indice")
    fiche_description_createur_id   = fields.Many2one("res.users", "Créateur")
    fiche_description_date_creation = fields.Date(u"Date de création")
    fiche_description_date_modif    = fields.Date(u"Date de modification")


#    • Champs non repris dans la fiche description moule :
#    • Bloc chaud : à reprendre dans fiche implantation des énergies
#    • Diamètre seuil : à reprendre dans la fiche de maintenance
#    • Classe : champ abandonné au profit des presses
#    • Nombre de circuits d'eau : à reprendre dans fiche implantation des énergies
#    • N° de plaquette interne : à reprendre dans la fiche de maintenance


#    • La fiche description moule doit être imprimable en pdf.
#    • On doit pouvoir suivre l'évolution de la fiche comme actuellement :
#        ◦ Indice A à la création
#        ◦ Nom du créateur
#        ◦ Date de la création
#        ◦ Date de la modification
#        ◦ Document référencé : FO-0-PROD-13 : indice 4 actuellement : à revoir à 5 quand ce sera dans Odoo.


























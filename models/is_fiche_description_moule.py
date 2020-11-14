# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import time
import datetime


_CINEMATIQUES={
    'standard':
"""- moule ouvert avec ejection contrôle rentré
- fermeture puis verrouillage
- cycle injection
- ouverture
- sortie ejection
- rentrée éjection
""",
    'avant_ejection':
"""- moule ouvert avec éjection contrôle rentrée et noyau sorti
- fermeture puis verrouillage
- cycle injection
- sortie noyau avec contrôle sortie
- ouverture
- sortie ejection
- rentrée éjection
""",
    'avant_ouverture':
"""- moule ouvert avec éjection contrôle rentré et noyau 1 rentré
- fermeture puis verrouillage
- cycle injection
- ouverture
- sortie noyau 1 avec contrôle sortie
- sortie éjection puis rentrée éjection avec contrôle rentré
- rentré noyau 1 avec contrôle rentré
""",
}

_NB_CIRCUIT_EAU = [
    ("0" , "0"),
    ("1" , "1"),
    ("2" , "2"),
    ("3" , "3"),
    ("4" , "4"),
    ("5" , "5"),
    ("6" , "6"),
    ("7" , "7"),
    ("8" , "8"),
    ("9" , "9"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
]

class IsMoldBridage(models.Model):
    _name = 'is.mold.bridage'
    _description = u"Bridage moule"
    _order='name'
    name = fields.Char(u'Bridage',select=True,required=True)


class is_mold(models.Model):
    _inherit = 'is.mold'

    @api.depends('cinematique')
    def _compute_cinematique(self):
        for obj in self:
            description = ''
            if obj.cinematique in _CINEMATIQUES:
                description = _CINEMATIQUES[obj.cinematique]
            obj.cinematique_description = description

    @api.depends('bridage_ids')
    def _compute_bridage_specifique_vsb(self):
        for obj in self:
            vsb=False
            for line in obj.bridage_ids:
                if line.name=='Spécifique':
                    vsb=True
            obj.bridage_specifique_vsb = vsb

    numero_plaquette_interne = fields.Char(u"N° Plaquette interne client")

    largeur   = fields.Integer(u"Largeur (mm)")
    hauteur   = fields.Integer(u"Hauteur (mm)")
    epaisseur = fields.Integer(u"Epaisseur (mm)")

    largeur_hors_tout   = fields.Integer(u"Largeur hors tout (mm)")
    hauteur_hors_tout   = fields.Integer(u"Hauteur hors tout (mm)")
    epaisseur_hors_tout = fields.Integer(u"Epaisseur hors tout (mm)")

    poids = fields.Integer(u"Poids (Kg)")

    nb_zones_utiles = fields.Char(u"Nombre de zones utiles sur le bloc chaud")

    recu_de_buse = fields.Selection([
            ("standard"  , u"Standard = cône 90°"),
            ("spherique" , u"Standard = sphérique"),
            ("specifique", u"Spécifique"),
        ], "Reçu de buse")
    recu_de_buse_specifique = fields.Char(u"Reçu de buse spécifique")

    diametre_entree_cheminee = fields.Selection([
            ("04"        , u"4.5 = Standard Plastigray"),
            ("05"        , u"5.5 = Standard Plastigray"),
            ("06"        , u"6.5 = Standard Plastigray"),
            ("specifique", u"Spécifique"),
        ], u"Diamètre entrée cheminée")
    diametre_entree_cheminee_specifique = fields.Char(u"Diamètre entrée cheminée spécifique")

#    bridage = fields.Selection([
#            ("manuel"  , u"manuel"),
#            ("auto180" , u"Automatique sur le carré 180 M20 / Automatic on square 180 M20"),
#            ("auto210" , u"Automatique sur le carré 210 M20 / Automatic on square 210 M20"),
#            ("auto310" , u"Automatique sur le carré 310 M30 / Automatic on square 310 M30"),
#            ("auto490" , u"Automatique sur le carré 490 M36 / Automatic on square 490 M36"),
#            ("magnetic", u"Magnétique / Magnetic"),
#        ], "Bridage")

    bridage_ids            = fields.Many2many("is.mold.bridage", "is_mold_bridage_rel", "mold_id", "bridage_id", u"Bridage")
    bridage_specifique_vsb = fields.Text(u"Bridage spécifique vsb", compute='_compute_bridage_specifique_vsb')
    bridage_specifique     = fields.Char(u"Bridage spécifique")

    ejection = fields.Selection([
            ("standard"    , u"Standard Plastigray (queue diam 60)"),
            ("autonome"    , u"Autonome (hydraulique)"),
            ("pas_ejection", u"Pas d'éjection"),
            ("specifique"  , u"Spécifique"),
        ], "Ejection")
    ejection_specifique = fields.Char(u"Ejection spécifique")

    rondelle_centrage_fixe = fields.Selection([
            ("standard"     , u"Standard Plastigray : 100"),
            ("specifique"   , u"Spécifique"),
            ("sans_rondelle", u"Sans rondelle"),
        ], "Rondelle de centrage - Partie fixe")
    rondelle_centrage_fixe_specifique = fields.Char(u"Rondelle de centrage - Partie fixe spécifique")

    rondelle_centrage_mobile = fields.Selection([
            ("standard"     , u"Standard Plastigray : 100"),
            ("specifique"   , u"Spécifique"),
            ("sans_rondelle", u"Sans rondelle"),
        ], "Rondelle de centrage - Partie mobile")
    rondelle_centrage_mobile_specifique = fields.Char(u"Rondelle de centrage - Partie mobile spécifique")

    presse_ids = fields.Many2many("is.equipement", "is_mold_presse_rel", "mold_id", "presse_id", u"Presses", domain=[('type_id.code', '=', 'PE')])

    nb_noyaux_fixe = fields.Selection([
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ], "Nombre de noyaux - Partie fixe")
    nb_noyaux_fixe_commentaire = fields.Char(u"Nombre de noyaux - Partie fixe - Commentaire")
    nb_noyaux_mobile = fields.Selection([
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ], "Nombre de noyaux - Partie mobile")
    nb_noyaux_mobile_commentaire = fields.Char(u"Nombre de noyaux - Partie mobile - Commentaire")

    nb_circuit_eau_fixe = fields.Selection(_NB_CIRCUIT_EAU, "Nombre de circuits d'eau - Partie fixe")
    nb_circuit_eau_fixe_commentaire = fields.Char(u"Nombre de circuits d'eau - Partie fixe - Commentaire")
    nb_circuit_eau_mobile = fields.Selection(_NB_CIRCUIT_EAU, "Nombre de circuits d'eau - Partie mobile")
    nb_circuit_eau_mobile_commentaire = fields.Char(u"Nombre de circuits d'eau - Partie mobile - Commentaire")

    cinematique = fields.Selection([
            ("standard"  , u"Standard : Cycle sans HM"),
            ("specifique", u"Spécifique"),
        ], "Cinématique")
    cinematique_description = fields.Text(u"Cinématique - Description", compute='_compute_cinematique', readonly=True, store=True)
    cinematique_specifique  = fields.Text(u"Cinématique - Spécifique")

    fiche_description_commentaire = fields.Text(u"Commentaire")

    fiche_description_indice        = fields.Char(u"Indice")
    fiche_description_createur_id   = fields.Many2one("res.users", "Créateur")
    fiche_description_date_creation = fields.Date(u"Date de création")
    fiche_description_date_modif    = fields.Date(u"Date de modification")


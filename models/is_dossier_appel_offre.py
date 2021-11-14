# -*- coding: utf-8 -*-
from openerp import models,fields,api


_DAO_RSPLAST=([
    ('A', u'A=Acceptée'),
    ('D', u'D=Déclinée'),
])

_DAO_MOTIF=([
    ("0", ""),
    ("1", "abandon client"),
    ("2", "délai trop long"),
    ("3", "moule et pièce trop chers"),
    ("4", "moule trop cher"),
    ("5", "pièce trop chère"),
    ("6", "autre"),
    ("7", "abandon Plastigray"),
])

_DAO_AVANCEMENT=([
    (u'Développement', u'Développement'),
    (u'Série'        , u'Série'),
])


class is_dossier_appel_offre(models.Model):
    _name = "is.dossier.appel.offre"
    _order = "dao_num"
    _rec_name = 'dao_num'

    dao_num          = fields.Char("Numéro")
    dao_date         = fields.Date("Date consultation")
    dao_annee        = fields.Char("Année consultation")
    dao_client       = fields.Char("Client")
    dao_typeclient   = fields.Char("Type client")
    dao_sectclient   = fields.Char("Section client")
    dao_commercial   = fields.Char("Commercial")
    dao_desig        = fields.Char("Désignation")
    dao_ref          = fields.Char("Référence")
    dao_datedms      = fields.Date("Date DMS")
    dao_ca           = fields.Float("Chiffre d'affaire")
    dao_vacom        = fields.Float("VA commerciale")
    dao_pourcentva   = fields.Float("% VA")
    dao_camoule      = fields.Float("CA Moule")
    dao_be           = fields.Char("Chef de projet")
    dao_dirbe        = fields.Char("Directeur technique")
    dao_daterepbe    = fields.Date("Date réponse BE")
    dao_daterepplast = fields.Date("Date réponse Plastigray")
    dao_rsplast      = fields.Selection(_DAO_RSPLAST, "Rsp Plastigray")
    dao_daterepcli   = fields.Date("Date réponse client")
    dao_rspcli       = fields.Char("Rsp client")
    dao_comment      = fields.Char("Commentaire")
    dao_motif        = fields.Selection(_DAO_MOTIF, "Motif")
    dao_avancement   = fields.Selection(_DAO_AVANCEMENT, "Avancement")
    dynacase_id      = fields.Integer("id Dynacase")

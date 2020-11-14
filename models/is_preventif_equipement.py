# -*- coding: utf-8 -*-

from openerp import models, fields, api
import time
import datetime


class is_preventif_equipement_zone(models.Model):
    _name = 'is.preventif.equipement.zone'
    _order = "name"

    def pgcd(self,a,b):
        """pgcd(a,b): calcul du 'Plus Grand Commun Diviseur' entre les 2 nombres entiers a et b"""
        while b<>0:
            a,b=b,a%b
        return a

    def pgcdn(self,n):
        """Calcul du 'Plus Grand Commun Diviseur' de n valeurs entières (Euclide)"""
        if len(n)==0:
            return 0
        if len(n)==1:
            return n[0]
        p = self.pgcd(n[0], n[1])
        for x in n[2:]:
            p = self.pgcd(p, x)
        return p

    @api.depends('preventif_ids')
    def _compute_frequence(self):
        for obj in self:
            frequences = []
            for line in obj.preventif_ids:
                if line.frequence>0:
                    frequences.append(line.frequence)
            pgcdn = self.pgcdn(frequences)
            obj.frequence = pgcdn

    name           = fields.Char(u"Nom de la zone", required=True, index=True)
    description    = fields.Text(u"Description de la zone")
    equipement_ids = fields.One2many('is.equipement', 'zone_id', u"Equipements de cette zone")
    preventif_ids  = fields.One2many('is.preventif.equipement', 'zone_id', u"Préventifs")
    frequence      = fields.Integer(u"Fréquence préventif zone (H)", compute='_compute_frequence', store=True, readonly=True)
    active         = fields.Boolean(u"Active", default=True)

class is_preventif_equipement(models.Model):
    _name = 'is.preventif.equipement'
    _order = "equipement_id"

    zone_id        = fields.Many2one('is.preventif.equipement.zone', u"Equipement", required=True, ondelete='cascade', readonly=True)
    equipement_id  = fields.Many2one('is.equipement', u"Equipement",required=True)
    type_preventif = fields.Selection([
            ('niveau2'       , u'Niveau 2'),
            ('niveau3'       , u'Niveau 3'),
            ('plastification', u'Plastification'),
            ('constructeur'  , u'Constructeur'),
        ], u"Type de préventif",required=True)
    frequence               = fields.Integer(u"Fréquence du préventif (H)", required=True)
    date_dernier_preventif  = fields.Date(u"Date du dernier préventif"  , readonly=True)
    date_prochain_preventif = fields.Date(u"Date du prochain préventif" , readonly=True)

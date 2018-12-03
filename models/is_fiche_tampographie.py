# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import datetime


class is_fiche_tampographie_constituant(models.Model):
    _name = 'is.fiche.tampographie.constituant'
    _order = 'name'

    name = fields.Char('Constituant')


class is_fiche_tampographie_recette(models.Model):
    _name = 'is.fiche.tampographie.recette'

    name            = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
        ], 'N°encrier', required=True)
    constituant_id  = fields.Many2one('is.fiche.tampographie.constituant', 'Constituant')
    product_id      = fields.Many2one('product.product', u'Référence article')
    poids           = fields.Char('Poids (gr)')
    tampographie_id = fields.Many2one('is.fiche.tampographie', 'Tampographie')


class is_fiche_tampographie_type_reglage(models.Model):
    _name = 'is.fiche.tampographie.type.reglage'
    _order = 'name'

    name = fields.Char(u'Type de réglage de la machine')


class is_fiche_tampographie_reglage(models.Model):
    _name = 'is.fiche.tampographie.reglage'

    name            = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
        ], 'N°encrier', required=True)
    type_reglage_id = fields.Many2one('is.fiche.tampographie.type.reglage', u'Type de réglage de la machine', required=True)
    reglage         = fields.Char(u'Réglage de la machine')
    tampographie_id = fields.Many2one('is.fiche.tampographie', 'Tampographie')


class is_fiche_tampographie(models.Model):
    _name = 'is.fiche.tampographie'

    name                  = fields.Char(u'Désignation', required=True)
    article_injection_id  = fields.Many2one('product.product', u'Référence pièce sortie injection', required=True)
    is_mold_dossierf      = fields.Char('Moule', related='article_injection_id.is_mold_dossierf', readonly=True)
    article_tampo_id      = fields.Many2one('product.product', u'Référence pièce typographiée', required=True)
    temps_cycle           = fields.Integer('Temps de cycle (s)')
    recette_ids           = fields.One2many('is.fiche.tampographie.recette', 'tampographie_id', 'Recette')
    reglage_ids           = fields.One2many('is.fiche.tampographie.reglage', 'tampographie_id', 'Reglage')
    nettoyage_materiel_id = fields.Many2one('product.product', u'Nettoyage du matériel')
    nettoyage_piece_id    = fields.Many2one('product.product', u'Nettoyage de la pièce')
    duree_vie_melange     = fields.Selection([
            ('8h', '8H'),
            ('24', '24'),
        ], u'Durée de vie du mélange')
    image_finale          = fields.Binary('Image Finale')
    image_encrier1        = fields.Binary('Image encrier1')
    image_encrier2        = fields.Binary('Image encrier2')
    image_encrier3        = fields.Binary('Image encrier3')
    image_posage          = fields.Binary('Image posage')
    redacteur_id          = fields.Many2one('res.users', u'Rédacteur', required=True, default=lambda self: self.env.user)
    approbateur_id        = fields.Many2one('res.users', 'Approbateur', required=True)
    date_redaction        = fields.Date(u'Date rédaction', required=True, default=datetime.date.today())
    indice                = fields.Char('Indice', required=True)
    state                 = fields.Selection([
            ('redaction', u'Rédaction'),
            ('approbation', 'Approbation'),
            ('valide', u'Validé'),
        ], u'État', default='redaction')


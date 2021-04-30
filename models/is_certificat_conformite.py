# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import datetime


class is_certificat_conformite(models.Model):
    _name='is.certificat.conformite'
    _order='product_id,client_id'
    _sql_constraints = [('product_id_client_id_uniq','UNIQUE(product_id,client_id)', u'Un certificat existe déjà pour ce client et pour cet article !')] 
    _rec_name = 'product_id'


    # TODO : 
    # - Cachet du fournisseur : Image du cachet
    # - Nom et Signature : nom du responsable qualité du site concerné avec une signature informatique
    # - qt_liv => Champ calculé
    # - Le serive ADV a accès uniquement aux champ order_id, picking_id, num_lot et date_fabrication

    product_id       = fields.Many2one('product.product', u"Article", domain=[('sale_ok','=',True)], required=True, select=True)
    client_id        = fields.Many2one('res.partner', u'Client', domain=[('is_company','=',True),('customer','=',True)], required=True, select=True)
    ref_client       = fields.Char(u"Référence client", related='product_id.is_ref_client', readonly=True)
    ref_plan         = fields.Char(u"Référence plan"  , related='product_id.is_ref_plan'  , readonly=True)
    ind_plan         = fields.Char(u"Indice plan"     , related='product_id.is_ind_plan'  , readonly=True)
    order_id         = fields.Many2one('sale.order'   , u'N° de commande')
    picking_id       = fields.Many2one('stock.picking', u'N°BL', domain=[('picking_type_id','=',2)])
    date_bl          = fields.Date(u"Date d'expédition", related='picking_id.is_date_expedition', readonly=True)
    qt_liv           = fields.Float(u"Quantité livrée")
    num_lot          = fields.Char(u"N° de lot")
    date_fabrication = fields.Date(u"Date de fabrication")
    rsp_qualite      = fields.Many2one('res.users', u'Responsable qualité')
    pourcentage_maxi = fields.Char(u"Pourcentage maxi de broyé", default="0%")
    reference_ids    = fields.One2many('is.certificat.conformite.reference', 'certificat_id', u"Références", copy=True)
    autre_ids        = fields.One2many('is.certificat.conformite.autre'    , 'certificat_id', u"Autre"     , copy=True)
    fabricant_ids    = fields.One2many('is.certificat.conformite.fabricant', 'certificat_id', u"Fabricants", copy=True)
    state            = fields.Selection([
            ('creation', u'Création'),
            ('valide'  , u"Validé"),
        ], "Etat", readonly=True, default="creation")


    @api.multi
    def vers_valide(self):
        for obj in self:
            obj.state='valide'


    @api.multi
    def vers_creation(self):
        for obj in self:
            obj.state='creation'


class is_certificat_conformite_reference(models.Model):
    _name='is.certificat.conformite.reference'
    _order='certificat_id,reference'

    certificat_id = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    reference     = fields.Char(u"Référence", required=True)
    fabricant     = fields.Char(u"Fabricant de la matière de base", required=True)
    ref_precise   = fields.Char(u"Référence précise de la matière de base")
    epaisseur     = fields.Char(u"Epaisseur minimale mesurable sur la pièce")
    classe        = fields.Char(u"Classe d'inflammabilité de la matière dans l'épaisseur mini")


class is_certificat_conformite_autre(models.Model):
    _name='is.certificat.conformite.autre'
    _order='certificat_id,autre_conformite'

    certificat_id         = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    autre_conformite      = fields.Char(u"Autres conformités", required=True)
    epaisseur_mini        = fields.Char(u"Epaisseur mini mesurable sur la pièce")
    classe_inflammabilite = fields.Char(u"Classe d'inflammabilité de la matière dans l'épaisseur mini")


class is_certificat_conformite_fabricant(models.Model):
    _name='is.certificat.conformite.fabricant'
    _order='certificat_id,fabricant'

    certificat_id = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    fabricant   = fields.Char(u"Fabricant de la matière pigmentée", required=True)
    pourcentage = fields.Char(u"% de la matière pigmentée", required=True)


# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import datetime


class is_bon_transfert(models.Model):
    _inherit = "is.bon.transfert"

    @api.multi
    def creation_facture_proforma_action(self):
        for obj in self:
            vals={
                'adresse_liv_id'  : obj.partner_id.id,
                'bon_transfert_id': obj.id,
            }
            proforma=self.env['is.facture.proforma'].create(vals)
            poids_net = poids_brut = 0
            sequence=0
            for line in obj.line_ids:
                sequence += 10
                vals={
                    'proforma_id': proforma.id,
                    'sequence'   : sequence,
                    'product_id' : line.product_id.id,
                    'designation': line.product_id.name,
                    'uom_id'     : line.uom_id.id,
                    'quantite'   : line.quantite,
                }
                res=self.env['is.facture.proforma.line'].create(vals)
                res._onchange_product_id()
            proforma.calcul_poids()
            return {
                'name': "Facture proforma",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.facture.proforma',
                'type': 'ir.actions.act_window',
                'res_id': proforma.id,
                'domain': '[]',
            }


class is_bl_manuel(models.Model):
    _inherit = "is.bl.manuel"

    @api.multi
    def creation_facture_proforma_action(self):
        for obj in self:
            vals={
                'adresse_liv_id': obj.destinataire_id.id,
                'bl_manuel_id'  : obj.id,
                'packaging'     : obj.colisage,
                'informations'  : obj.motif_expedition,
            }
            proforma=self.env['is.facture.proforma'].create(vals)
            poids_net = poids_brut = 0
            for line in obj.line_ids:
                poids_net  += line.poids_net
                poids_brut += line.poids_brut
                vals={
                    'proforma_id': proforma.id,
                    'sequence': line.sequence,
                    'product_id': line.product_id.id,
                    'designation': line.description,
                    'uom_id': line.uom_id.id,
                    'quantite': line.qt_livree,
                }
                res=self.env['is.facture.proforma.line'].create(vals)
                res._onchange_product_id()
            proforma.poids_net  = poids_net
            proforma.poids_brut = poids_brut
            return {
                'name': "Facture proforma",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.facture.proforma',
                'type': 'ir.actions.act_window',
                'res_id': proforma.id,
                'domain': '[]',
            }


class is_facture_proforma(models.Model):
    _name='is.facture.proforma'
    _order='name desc'


    @api.depends('adresse_liv_id')
    def _compute_adresse_fac_id(self):
        for obj in self:
            obj.adresse_fac_id = obj.adresse_liv_id.is_adr_facturation.id or obj.adresse_liv_id.id


    @api.depends('line_ids')
    def _compute(self):
        for obj in self:
            montant = 0
            for line in obj.line_ids:
                montant += line.montant
            obj.montant = montant


    name                 = fields.Char("Facture proforma", readonly=True)
    createur_id          = fields.Many2one('res.users', 'Créateur', required=True)
    date_facture         = fields.Date("Date facture"             , required=True, default=lambda *a: fields.datetime.now())
    adresse_liv_id       = fields.Many2one('res.partner', 'Adresse de livraison'  , required=True, domain=[('is_company','=',True),('customer','=',True)])
    adresse_fac_id       = fields.Many2one('res.partner', 'Adresse de facturation', compute='_compute_adresse_fac_id', readonly=True, store=True)
    pricelist_id         = fields.Many2one('product.pricelist', "Liste de prix"   , related='adresse_liv_id.property_product_pricelist', readonly=True)
    vat                  = fields.Char("Numéro fiscal"                            , related='adresse_liv_id.vat', readonly=True)
    incoterm_id          = fields.Many2one('stock.incoterms', "Incoterm"          , related='adresse_liv_id.is_incoterm', readonly=True)
    lieu                 = fields.Char("Lieu"                                     , related='adresse_liv_id.is_lieu', readonly=True)
    line_ids             = fields.One2many('is.facture.proforma.line', 'proforma_id', u"Lignes", copy=True)
    poids_brut           = fields.Float("Poids brut")
    poids_net            = fields.Float("Poids net")
    packaging            = fields.Char("Packaging")
    informations         = fields.Text("informations complémentaires")
    bon_transfert_id     = fields.Many2one('is.bon.transfert', 'Bon de transfert', readonly=True)
    bl_manuel_id         = fields.Many2one('is.bl.manuel', 'BL manuel', readonly=True)
    montant              = fields.Float("Montant Total", digits=(14,2), compute='_compute', readonly=True, store=True)


    _defaults = {
        'createur_id': lambda self, cr, uid, c: uid,
    }

    
    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_facture_proforma_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        obj = super(is_facture_proforma, self).create(vals)
        return obj


    @api.onchange('line_ids')
    def calcul_poids(self):
        for obj in self:
            poids_brut=poids_net=0
            for l in obj.line_ids:
                poids_net+=l.quantite*l.product_id.weight_net
                poids_brut+=l.quantite*l.product_id.weight
            obj.poids_net  = poids_net
            obj.poids_brut = poids_brut


class is_facture_proforma_line(models.Model):
    _name='is.facture.proforma.line'
    _order='proforma_id,sequence'


    @api.depends('product_id','quantite','prix')
    def _compute(self):
        for obj in self:
            obj.montant=obj.quantite*obj.prix


    @api.onchange('product_id','quantite')
    def _onchange_product_id(self):
        self.nomenclature_douaniere = self.product_id.is_nomenclature_douaniere
        self.designation            = self.product_id.name
        prix = 0
        product_id   = self.product_id.id
        if product_id:
            pricelist_id = self.proforma_id.pricelist_id.id
            partner_id   = self.proforma_id.adresse_liv_id.id
            price = self.proforma_id.pricelist_id.price_get(product_id, self.quantite, partner_id)
            prix = price[pricelist_id]
        self.prix = prix





    proforma_id            = fields.Many2one('is.facture.proforma', "Facture proforma", required=True, ondelete='cascade', readonly=True)
    sequence               = fields.Integer('Ordre')
    product_id             = fields.Many2one('product.product', 'Article', domain=[('segment_id.name','=','ARTICLES COMPTABLES FRAIS GENERAUX')])
    designation            = fields.Char(u'Désignation', required=True)
    ref_client             = fields.Char(u'Référence client', related='product_id.is_ref_client', readonly=True)
    nomenclature_douaniere = fields.Char(u'Nomenclature douanière')
    uom_id                 = fields.Many2one('product.uom', "Unité", related='product_id.uom_id', readonly=True)
    quantite               = fields.Float("Quantité", digits=(14,2), required=True)
    prix                   = fields.Float("Prix"    , digits=(14,4))
    montant                = fields.Float("Montant" , digits=(14,2), compute='_compute', readonly=True, store=True)




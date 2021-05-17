# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import datetime


class is_facture_proforma(models.Model):
    _name='is.facture.proforma'
    _order='name desc'

    name                 = fields.Char("Facture proforma", readonly=True)
#    createur_id          = fields.Many2one('res.users', 'Demandeur', required=True)
#    date_demande         = fields.Date("Date de la demande", required=True        , default=lambda *a: fields.datetime.now())
#    responsable_id       = fields.Many2one('res.users', 'Responsable', required=True, domain=lambda self: [( "groups_id", "=", self.env.ref("is_pg_2019.is_bon_achat_ville_grp").id)])
#    fournisseur_id       = fields.Many2one('res.partner', 'Fournisseur', domain=[('is_achat_ville','=',True)], required=True)
#    pricelist_id         = fields.Many2one('product.pricelist', "Liste de prix", related='fournisseur_id.property_product_pricelist_purchase', readonly=True)
#    objet                = fields.Char("Objet de la demande", required=True)
#    state                = fields.Selection([
#        ('brouillon', 'Brouillon'),
#        ('en_cours' , 'En cours de validation'),
#        ('valide'   , 'Validé'),
#        ('annule'   , 'Annulé'),
#    ], "Etat", default='brouillon')
    line_ids           = fields.One2many('is.facture.proforma.line', 'proforma_id', u"Lignes", copy=True)
#    montant_total      = fields.Float("Montant Total", compute='_compute', readonly=True, store=True)
#    nb_lignes          = fields.Integer("Nombre de lignes", compute='_compute', readonly=True, store=True)
#    vers_brouillon_vsb = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
#    vers_en_cours_vsb  = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
#    vers_valide_vsb    = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
#    vers_annule_vsb    = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)

#    _defaults = {
#        'createur_id': lambda self, cr, uid, c: uid,
#    }

    
    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_facture_proforma_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        obj = super(is_facture_proforma, self).create(vals)
        return obj


class is_facture_proforma_line(models.Model):
    _name='is.facture.proforma.line'
    _order='proforma_id,sequence'


    @api.depends('product_id','quantite','prix')
    def _compute(self):
        for obj in self:
            #if obj.product_id:
            #    obj.uom_id=obj.product_id.uom_po_id
            obj.montant=obj.quantite*obj.prix

    proforma_id      = fields.Many2one('is.facture.proforma', "Facture proforma", required=True, ondelete='cascade', readonly=True)
    sequence    = fields.Integer('Ordre')
    product_id  = fields.Many2one('product.product', 'Article', domain=[('segment_id.name','=','ARTICLES COMPTABLES FRAIS GENERAUX')], required=True)
    designation = fields.Char(u'Désignation', required=True)
#    uom_id      = fields.Many2one('product.uom', "Unité d'achat", compute='_compute', readonly=True, store=True)
    quantite    = fields.Float("Quantité", digits=(14,4), required=True)
    prix        = fields.Float("Prix"    , digits=(14,4))
    montant     = fields.Float("Montant", compute='_compute', readonly=True, store=True)
#    chantier    = fields.Char(u'Chantier', help=u"Chantier sur 5 chiffres")




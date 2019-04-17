# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models, fields, api
from openerp.tools.translate import _


class is_ctrl100_operation_standard(models.Model):
    _name        = 'is.ctrl100.operation.standard'
    _description = u"Opérations standard"
    _order       = 'order,name desc'

    name   = fields.Char(u"Opération standard")
    order  = fields.Integer("Ordre")
    active = fields.Boolean("Active", default=True)


class is_ctrl100_gamme_standard(models.Model):
    _name        = 'is.ctrl100.gamme.standard'
    _description = u"Opérations gamme standard"
    _order       = 'operation_standard_id desc'

    operation_standard_id  = fields.Many2one('is.ctrl100.operation.standard', u"Opérations standard")
    active                 = fields.Boolean("Active")
    gamme_qualite_id       = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité")


class is_ctrl100_operation_specifique(models.Model):
    _name        = 'is.ctrl100.operation.specifique'
    _description = u"Opérations spécifiques"

    operation        = fields.Text(u"Opération")
    photo            = fields.Binary('Photo')
    temps_etape      = fields.Float(u"Temps de l'étape  (Seconde / Pièce) ", digits=(14, 2))
    gamme_qualite_id = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité")


class is_ctrl100_typologie_produit(models.Model):
    _name        = 'is.ctrl100.typologie.produit'
    _description = u"Typologie de produit"
    _order       = 'name desc'

    name   = fields.Char(u"Typologie de produit")


class is_ctrl100_gamme_mur_qualite(models.Model):
    _name        = 'is.ctrl100.gamme.mur.qualite'
    _description = u"Gamme mur qualité"
    _order       = 'name desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.gamme.mur.qualite') or ''
        return super(is_ctrl100_gamme_mur_qualite, self).create(vals)

    @api.model
    def default_get(self, default_fields):
        res = super(is_ctrl100_gamme_mur_qualite, self).default_get(default_fields)
        gamme_standard_obj = self.env['is.ctrl100.gamme.standard']
        operation_standard_obj = self.env['is.ctrl100.operation.standard']
        lst = []
        operation_standardids = operation_standard_obj.search([('active', '=', True)])
        for num in operation_standardids:
            lst.append((0,0, {
                'operation_standard_id': num.id, 
                'active': False,
            }))
        res['operation_standard_ids'] = lst
        return res

    name                     = fields.Char(u"N°de gamme", readonly=True)
    type_gamme               = fields.Selection([
                                    ("qualification_process", "Qualification Process"),
                                    ("securisation", u"Sécurisation"),
                                    ("reprise", "Reprise"),
                                ], "Type de gamme", required=True)
    gamme_sur                = fields.Selection([
                                    ("moule", "Moule"),
                                    ("dossier_f", "Dossier F"),
                                    ("article", "Article"),
                                ], "Gamme sur", required=True)
    mold_id                  = fields.Many2one("is.mold", "Moule")
    dossierf_id              = fields.Many2one("is.dossierf", "Dossier F")
    product_id               = fields.Many2one("product.product", "Article")
    date_creation            = fields.Date(u"Date de création", copy=False, default=fields.Date.context_today)
    typologie_produit_id     = fields.Many2one("is.ctrl100.typologie.produit", "Typologie de produit")
    date_fin_validite        = fields.Date(u"Date de fin de validité")
    operation_standard_ids   = fields.One2many('is.ctrl100.gamme.standard', 'gamme_qualite_id', u"Opérations standard")
    operation_specifique_ids = fields.One2many('is.ctrl100.operation.specifique', 'gamme_qualite_id',  u"Opérations spécifiques")


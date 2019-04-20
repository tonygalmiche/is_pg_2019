# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models, fields, api
from openerp.tools.translate import _
from collections import defaultdict


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

    @api.multi
    def get_defautheque_data(self):
        res = False
        defautheque = []
        rec_dict = defaultdict(list)
        defautheque_obj = self.env['is.ctrl100.defautheque']
        for obj in self:
            defautheque_ids = defautheque_obj.search([('gamme_id','=',obj.id)])
            for rec in defautheque_ids:
                recdict = {
                    'name': rec.name,
                    'defaut': rec.defaut,
                    'photo': rec.photo,
                    'quantite': 'xxx',
                }
                defautheque.append(recdict)
        return defautheque

    @api.multi
    def get_default_data(self):
        res = False
        default = []
        rec_dict = defaultdict(list)
        defaut_obj = self.env['is.ctrl100.defaut']
        for obj in self:
            default_ids = defaut_obj.search([('gamme_id','=',obj.id)])
            for rec in default_ids:
                rec_dict = defaultdict(list)
                tracabilite_nm = ''
                if rec.tracabilite == 'article':
                    tracabilite_nm = rec.product_id.name
                if rec.tracabilite == 'of':
                    tracabilite_nm = rec.production_id.name
                if rec.tracabilite == 'reception':
                    tracabilite_nm = rec.picking_id.name
                if not rec.defautheque_ids:
                    recdict = {
                        'tracabilite_nm': tracabilite_nm,
                        'date_saisie': rec.date_saisie,
                        'tps_passe': rec.tps_passe,
                        'nb_pieces_controlees': rec.nb_pieces_controlees,
                        'employe_id': '',
                        'nb_rebuts': '',
                        'nb_repris': '',
                        'defaut_id': ''
                    }
                    default.append(recdict)
                for data in rec.defautheque_ids:
                    recdict = {
                        'tracabilite_nm': tracabilite_nm,
                        'date_saisie': rec.date_saisie,
                        'tps_passe': rec.tps_passe,
                        'nb_pieces_controlees': rec.nb_pieces_controlees,
                        'employe_id': data.employe_id and data.employe_id.id,
                        'nb_rebuts': data.nb_rebuts,
                        'nb_repris': data.nb_repris,
                        'defaut_id': data.defaut_id.name
                    }
                    default.append(recdict)
        return default

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


class is_ctrl100_defautheque(models.Model):
    _name        = 'is.ctrl100.defautheque'
    _description = u"Défauthèque”"
    _order       = 'name desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.defautheque') or ''
        return super(is_ctrl100_defautheque, self).create(vals)

    name      = fields.Char(u"N° du défaut")
    gamme_id  = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"N°gamme")
    defaut    = fields.Text(u"Défaut")
    photo     = fields.Binary("Photo")
    active    = fields.Boolean("Active", default=True)


class is_ctrl100_defaut(models.Model):
    _name        = 'is.ctrl100.defaut'
    _description = u"Défauts"
    _order       = 'name desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ctrl100.defaut') or ''
        return super(is_ctrl100_defaut, self).create(vals)

    name                 = fields.Char(u"N° du défaut")
    gamme_id             = fields.Many2one("is.ctrl100.gamme.mur.qualite", u"N°gamme")
    tracabilite                = fields.Selection([
                                    ("article", "Article"),
                                    ("of", "OF"),
                                    ("reception", "Réception"),
                                ], "Traçabilité")
    product_id           = fields.Many2one("product.product", "Article")
    production_id        = fields.Many2one("mrp.production", "OF")
    picking_id           = fields.Many2one("stock.picking", "Réception", domain=[('picking_type_id.code','=','incoming')])
    createur_id          = fields.Many2one("res.users", "Createur", default=lambda self: self.env.user)
    date_saisie          = fields.Date(u"Date saisie", copy=False, default=fields.Date.context_today)
    nb_pieces_controlees = fields.Integer("Nombre de pièces contrôlées")
    tps_passe            = fields.Float(u"Temps passé (H)", digits=(14, 2))
    defautheque_ids      = fields.One2many("is.ctrl100.defaut.line", "defautid", u"Défauthèque")


class is_ctrl100_defaut_line(models.Model):
    _name        = 'is.ctrl100.defaut.line'
    _description = u"Défauts Line"
    _order       = 'defaut_id desc'

    defaut_id   = fields.Many2one("is.ctrl100.defautheque", u"N° du défaut")
    defaut_text = fields.Text("Défaut", related="defaut_id.defaut")
    nb_rebuts   = fields.Integer("Nombre de rebuts")
    nb_repris   = fields.Integer("Nombre de repris")
    employe_id  = fields.Many2one("hr.employee", u"Employé")
    defautid    = fields.Many2one("is.ctrl100.defaut", u"N° du défaut")



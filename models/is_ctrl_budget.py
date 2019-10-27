# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models,fields,api
from openerp.tools.translate import _


_DESTINATION = [
    ("2", "PIC"),
    ("3", "Réa Std"),
    ("4", "Ctrl Mens"),
    ("7", "Saisie Trim"),
]


def _get_destination(dest):
    for line in _DESTINATION:
        if line[0] == dest:
            return line[1]
    return ''


class is_ctrl_budget_tdb_famille(models.Model):
    _name = 'is.ctrl.budget.tdb.famille'
    _description = u"Contrôle bugétaire - Budget Tableau de bord -Famille"
    _order='ordre,name'

    name     = fields.Char(u'Famille', select=True, required=True)
    ordre    = fields.Integer(u'Ordre', select=True, required=True)
    variable = fields.Boolean(u'Montant variable', default=True)
    fixe     = fields.Boolean(u'Montant fixe'    , default=True)


class is_ctrl_budget_tdb_famille_rel(models.Model):
    _name = 'is.ctrl.budget.tdb.famille.rel'
    _description = u"Contrôle bugétaire - Budget Tableau de bord - Famille - Relation"
    _order='id'

    saisie_id  = fields.Many2one("is.ctrl.budget.tdb.saisie", "Saisie")
    famille_id = fields.Many2one('is.ctrl.budget.tdb.famille', u"Famille")


    @api.multi
    def lignes_famille_action(self):
        for obj in self:
            name=str(obj.saisie_id.mois)+u'/'+str(obj.saisie_id.annee)+u':'+_get_destination(obj.saisie_id.destination)+u':'+obj.famille_id.name
            montant_fixe_filter=False
            if obj.famille_id.fixe:
                montant_fixe_filter=True
            return {
                'name': name,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'is.ctrl.budget.tdb',
                'domain': [
                    ('saisie_id' ,'=',obj.saisie_id.id),
                    ('famille_id','=',obj.famille_id.id)
                ],
                'context':{
                    'default_saisie_id' : obj.saisie_id.id,
                    'default_famille_id': obj.famille_id.id,
                    'search_default_montant_fixe_filter': montant_fixe_filter,
                },
                'type': 'ir.actions.act_window',
                'limit': 1000,
            }


class is_ctrl_budget_tdb_intitule(models.Model):
    _name = 'is.ctrl.budget.tdb.intitule'
    _description = u"Contrôle bugétaire - Budget Tableau de bord -Ligne"
    _order='famille_id, name'

    # La fonction name_get est une fonction standard d'Odoo permettant de définir le nom des fiches (dans les relations x2x)
    # La fonction name_search permet de définir les résultats des recherches dans les relations x2x. En général, elle appelle la fonction name_get
    @api.multi
    def name_get(self):
        res=[]
        for obj in self:
            name=obj.intitule+u' ('+str(obj.name)+')'
            res.append((obj.id, name))
        return res

    famille_id  = fields.Many2one('is.ctrl.budget.tdb.famille', u"Famille", required=True)
    name        = fields.Integer(u'Code', select=True, required=True)
    intitule    = fields.Char(u'Intitulé Ligne', required=True)


class is_ctrl_budget_tdb_saisie(models.Model):
    _name = 'is.ctrl.budget.tdb.saisie'
    _description = u"Contrôle bugétaire - Budget Tableau de bord - Saisie"
    _order='annee desc, mois desc, destination'

    annee        = fields.Char(u'Année'  , select=True, required=True)
    mois         = fields.Integer(u'Mois', select=True, required=True)
    destination  = fields.Selection(_DESTINATION  , "Destination", select=True, required=True)
    ligne_ids    = fields.One2many('is.ctrl.budget.tdb', 'saisie_id', u"Lignes", copy=True)
    famille_ids  = fields.One2many('is.ctrl.budget.tdb.famille.rel','saisie_id', string="Familles", copy=True)

    @api.multi
    def copy(self,vals):
        for obj in self:
            vals['annee']=obj.annee+u' (copie)'
            res=super(is_ctrl_budget_tdb_saisie, self).copy(vals)
            return res

    # La fonction name_get est une fonction standard d'Odoo permettant de définir le nom des fiches (dans les relations x2x)
    # La fonction name_search permet de définir les résultats des recherches dans les relations x2x. En général, elle appelle la fonction name_get
    @api.multi
    def name_get(self):
        res=[]
        for obj in self:
            name=str(obj.mois)+u'/'+str(obj.annee)+u':'+_get_destination(obj.destination)
            res.append((obj.id, name))
        return res


    @api.multi
    def lignes_action(self):
        for obj in self:
            name=str(obj.mois)+u'/'+str(obj.annee)+u':'+_get_destination(obj.destination)
            return {
                'name': name,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'is.ctrl.budget.tdb',
                'domain': [
                    ('saisie_id' ,'=',obj.id),
                ],
                'context':{
                    'default_saisie_id' : obj.id,
                    'search_default_montant_fixe_filter': True,
                },
                'type': 'ir.actions.act_window',
                'limit': 1000,
            }


    @api.multi
    def initialiser_lignes(self):
        for obj in self:
            obj.ligne_ids.unlink()
            intitules = self.env['is.ctrl.budget.tdb.intitule'].search([])
            for intitule in intitules:
                vals={
                    'saisie_id'  : obj.id,
                    'intitule_id': intitule.id,
                }
                self.env['is.ctrl.budget.tdb'].create(vals)
            obj.famille_ids.unlink()
            familles = self.env['is.ctrl.budget.tdb.famille'].search([])
            for famille in familles:
                vals={
                    'saisie_id' : obj.id,
                    'famille_id': famille.id,
                }
                self.env['is.ctrl.budget.tdb.famille.rel'].create(vals)


class is_ctrl_budget_tdb(models.Model):
    _name = 'is.ctrl.budget.tdb'
    _description = u"Contrôle bugétaire - Budget Tableau de bord"
    _order='intitule_id'


    @api.depends('intitule_id')
    def _compute(self):
        for obj in self:
            obj.famille_id  = obj.intitule_id.famille_id.id


    saisie_id        = fields.Many2one("is.ctrl.budget.tdb.saisie", "Saisie")
    intitule_id      = fields.Many2one('is.ctrl.budget.tdb.intitule', u"Intitulé", required=True)
    famille_id       = fields.Many2one("is.ctrl.budget.tdb.famille", "Famille", select=True, store=True, readonly=True, compute='_compute')
    #annee            = fields.Char(u'Année'                        , select=True, store=True, readonly=True, compute='_compute')
    #mois             = fields.Integer(u'Mois'                      , select=True, store=True, readonly=True, compute='_compute')
    #destination      = fields.Selection(_DESTINATION, "Destination", select=True, store=True, readonly=True, compute='_compute')

    #ligne            = fields.Integer('Ligne', select=True, required=True)
    montant_variable = fields.Integer('Montant Variable')
    montant_fixe     = fields.Integer('Montant Fixe')








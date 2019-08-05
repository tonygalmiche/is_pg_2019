# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models, fields, api
from openerp.tools.translate import _
from collections import defaultdict
from openerp.exceptions import except_orm, Warning, RedirectWarning
# from pytz import timezone
# import pytz
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt



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
    _order       = 'operation_standard_id'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        args += ['|', ('active', '=', True), ('active', '=', False)]
        return super(is_ctrl100_gamme_standard, self).search(args, offset, limit, order, count=count)


    gamme_qualite_id       = fields.Many2one('is.ctrl100.gamme.mur.qualite', u"Gamme mur qualité")
    operation_standard_id  = fields.Many2one('is.ctrl100.operation.standard', u"Opérations standard")
    active                 = fields.Boolean("Active", default=True)
    temps_etape            = fields.Float(u"Temps de l'étape  (Seconde / Pièce) ", digits=(14, 2))


class is_ctrl100_operation_specifique(models.Model):
    _name        = 'is.ctrl100.operation.specifique'
    _description = u"Opérations spécifiques"
    _order       = 'operation'

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
                        'employe_id': self.env.user.login,
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


    @api.returns('self')
    def _get_cout_ctrl_qualite(self):
        user = self.env['res.users'].browse(self.env.uid)
        cout = 0
        if user:
            cout = user.company_id.is_cout_ctrl_qualite or 0
        return cout


    @api.depends('cout_ctrl_qualite','operation_standard_ids','operation_specifique_ids')
    def _compute_cout(self):
        for obj in self:
            tps = 0
            for line in obj.operation_standard_ids:
                if line.temps_etape:
                    tps+=line.temps_etape
            for line in obj.operation_specifique_ids:
                if line.temps_etape:
                    tps+=line.temps_etape

            cadence_previsionnelle = 0
            if tps>0:
                cadence_previsionnelle = 3600/tps
            cout = obj.cout_ctrl_qualite*tps/3600
            obj.cout_previsionnel      = cout
            obj.cadence_previsionnelle = cadence_previsionnelle


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
    cout_ctrl_qualite        = fields.Float(u"Coût horaire vendu contrôle qualité", digits=(12, 2), default=_get_cout_ctrl_qualite)
    cout_previsionnel        = fields.Float(u"Coût prévisionnel par pièce", digits=(12, 2), compute="_compute_cout", store=True, readonly=True)
    cadence_previsionnelle   = fields.Float(u"Cadence de contrôle prévisionnelle (pcs/h)", digits=(12, 2), compute="_compute_cout", store=True, readonly=True)


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
        res = super(is_ctrl100_defaut, self).create(vals)
        for data in res:
            if data.nb_pieces_controlees <= 0:
                raise Warning(_("Nombre de pièces contrôlées value must be greater then 0 !"))
            for line in data.defautheque_ids:
                if line.nb_rebuts <= 0 and line.nb_repris <= 0:
                    raise Warning(_("Nombre de rebuts or Nombre de repris must be greater than 0"))
        return res

    @api.multi
    def write(self, vals):
        res = super(is_ctrl100_defaut, self).write(vals)
        for data in self:
            if data.nb_pieces_controlees <= 0:
                raise Warning(_("Nombre de pièces contrôlées value must be greater then 0 !"))
            for line in data.defautheque_ids:
                if line.nb_rebuts <= 0 and line.nb_repris <= 0:
                    raise Warning(_("Nombre de rebuts or Nombre de repris must be greater than 0"))
        return res

    @api.multi
    def get_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1) or False
        if emp_ids:
            return emp_ids and emp_ids[0].id
        else:
            return False

    @api.model
    def default_get(self, default_fields):
        res = super(is_ctrl100_defaut, self).default_get(default_fields)
        defautheque_obj = self.env['is.ctrl100.defautheque']
        lst = []
        defautheque_ids = defautheque_obj.search([('active', '=', True)])
        for num in defautheque_ids:
            lst.append((0,0, {
                'defaut_id': num.id,
                'employe_id': self.get_employee()
            }))
        res['defautheque_ids'] = lst
        return res

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

    @api.returns('self')
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1) or False

    defaut_id    = fields.Many2one("is.ctrl100.defautheque", u"N° du défaut")
    defaut_text  = fields.Text("Défaut", related="defaut_id.defaut")
    defaut_photo = fields.Binary("Photo", related="defaut_id.photo")
    nb_rebuts    = fields.Integer("Nombre de rebuts")
    nb_repris    = fields.Integer("Nombre de repris")
    employe_id   = fields.Many2one("hr.employee", u"Employé", default=_get_employee)
    defautid     = fields.Many2one("is.ctrl100.defaut", u"N° du défaut")


class is_ctrl100_rapport_controle(models.Model):
    _name        = 'is.ctrl100.rapport.controle'
    _description = u"Rapport de contrôle"
    _order       = 'gamme_id desc'

    @api.multi
    def get_default_data(self, gamme_id, date_debut, date_fin):
        defaut_line_obj = self.env['is.ctrl100.defaut.line']
        self._cr.execute("select is_ctrl100_defaut_line.defaut_id, sum(nb_rebuts) from is_ctrl100_defaut_line inner join is_ctrl100_defaut on is_ctrl100_defaut.id=is_ctrl100_defaut_line.defautid \
        where is_ctrl100_defaut.gamme_id=%s and is_ctrl100_defaut.date_saisie > %s and \
        is_ctrl100_defaut.date_saisie <= %s group by is_ctrl100_defaut_line.defaut_id", (gamme_id.id,date_debut,date_fin))
        listdisct = []
        performance = []
        res_ids = self._cr.fetchall()
        seq_no = 1
        for res in res_ids:
            print "Res..........",res, res[0], res[1]
            defautheque_data = defaut_line_obj.browse(res[0])
            performance.append(res[1])
            recdict = {
                'seq_no': seq_no,
                'desc': defautheque_data.defaut_id.defaut,
                'photo': defautheque_data.defaut_id.photo,
                'qty': res[1],
                'perc': res[1],
            }
            seq_no += 1
            listdisct.append(recdict)
        
        vrt = []
        for i in range(1, len(res_ids)+1):
            vrt.append(i)
        print "NM",vrt
        y_pos = np.arange(len(vrt))
        plt.bar(y_pos, performance, align='center', alpha=0.5)
        rect1 = plt.xticks(y_pos, vrt)
        plt.savefig('/tmp/books_read.png')
        return listdisct

    @api.multi
    def get_chart_img(self):
        import base64
        image = open('/tmp/books_read.png', 'rb')
        image_read = image.read()
        image_64_encode = base64.encodestring(image_read)
        return image_64_encode


    gamme_id    = fields.Many2one("is.ctrl100.gamme.mur.qualite", string=u"N°gamme", required=True)
    createur_id = fields.Many2one("res.users", "Createur", default=lambda self: self.env.user, required=True, writeable=True)
    date_debut  = fields.Date(u"Date de début", required=True)
    date_fin    = fields.Date("Date de fin", required=True)


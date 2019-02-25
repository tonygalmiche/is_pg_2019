# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import datetime
from collections import defaultdict
from collections import OrderedDict
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import SUPERUSER_ID
from lxml import etree


class is_ot_affectation(models.Model):
    _name = 'is.ot.affectation'

    name = fields.Char("Affectation", required=True)


class is_ot_temps_passe(models.Model):
    _name = 'is.ot.temps.passe'

    technicien_id = fields.Many2one("res.users", "Nom du technicien", default=lambda self: self.env.uid)
    descriptif    = fields.Text("Descriptif des travaux")
    temps_passe   = fields.Float(u"Temps passé", digits=(14, 2))
    ot_id         = fields.Many2one("is.ot", "OT")


class is_ot(models.Model):
    _name = 'is.ot'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.ot') or ''
        count = 0
        if vals and vals.get('equipement_id'):
            count += 1
        if vals and vals.get('moule_id'):
            count += 1
        if vals and vals.get('dossierf_id'):
            count += 1
        if count == 0 or count > 1:
            raise except_orm(_('Configuration!'),
                             _(" it is obligatory to enter one of these fields to create the form : Equipement or Moule or Dossier F "))
        if self._uid:
            user_data = self.env['res.users'].browse(self._uid)
            if user_data and not user_data.is_site_id:
                raise except_orm(_('Configuration!'),
                             _("Site must be filled in its user form"))
        return super(is_ot, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(is_ot, self).write(vals)
        for data in self:
            if data.state == 'analyse_ot' and data.validation_ot == 'oui':
                self.signal_workflow('travaux_a_realiser')
            if data.state == 'analyse_ot' and data.validation_ot == 'non':
                self.signal_workflow('annule')
            if data.state == 'travaux_a_valider' and data.validation_travaux == 'non_ok':
                data.signal_workflow('travaux_a_realiser')
            if data.state == 'travaux_a_valider' and data.validation_travaux == 'ok':
                data.signal_workflow('termine')
            count = 0
            if data.equipement_id:
                count += 1
            if data.moule_id:
                count += 1
            if data.dossierf_id:
                count += 1
            if count == 0 or count > 1:
                raise except_orm(_('Configuration!'),
                                 _(" it is obligatory to enter one of these fields to create the form : Equipement or Moule or Dossier F "))
        return res

    @api.multi
    def vers_travaux_a_valider(self):
        for data in self:
            data.signal_workflow('travaux_a_valider')
        return True

    @api.multi
    def vers_analyse_ot(self):
        for data in self:
            data.signal_workflow('creation_to_analyse')
        return True

    @api.multi
    def envoi_mail(self, email_from, email_to, subject, body_html):
        for obj in self:
            vals = {
                'email_from'    : email_from,
                'email_to'      : email_to,
                'email_cc'      : email_from,
                'subject'       : subject,
                'body_html'     : body_html,
            }
            email = self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)

    @api.multi
    def action_annule(self):
        for obj in self:
            subject = u'[' + obj.name + u'] Gestion des OT - Annule'
            email_to = obj.demandeur_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la getion des ot <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Annule'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, subject, body_html)
        return self.write({'state': 'annule'})

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        res = super(is_ot, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if view_type != 'form':
            return res
        if uid != 1:
            return res
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='state']"):
            node.set('clickable', "True")
        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def default_get(self, default_fields):
        res = super(is_ot, self).default_get(default_fields)
        if self._uid:
            user_data = self.env['res.users'].browse(self._uid)
            if user_data and user_data.is_site_id:
                res['site_id'] = user_data.is_site_id.id
        return res


    name                = fields.Char(u"N° de l'OT")
    state               = fields.Selection([
            ('creation', u'Création'),
            ('analyse_ot', u"Analyse de l'OT"),
            ('travaux_a_realiser', u'Travaux à réaliser'),
            ('travaux_a_valider', u'Travaux à valider'),
            ('annule', u'Annulé'),
            ('termine', u'Terminé'),
            ], "State", readonly=True, default="creation")
    site_id             = fields.Many2one("is.database", "Site", help="Site must be filled in its user form")
    date_creation       = fields.Date(u"Date de création", copy=False, default=fields.Date.context_today, readonly=True)
    demandeur_id        = fields.Many2one("res.users", "Demandeur", default=lambda self: self.env.uid, readonly=True)
    type_equipement_id  = fields.Many2one("is.equipement.type", u"Type d'équipement")
    equipement_id       = fields.Many2one("is.equipement", "Équipement")
    moule_id            = fields.Many2one("is.mold", "Moule")
    dossierf_id         = fields.Many2one("is.dossierf", "Dossier F")
    gravite             = fields.Selection([
            ('1', u"risque de rupture client suite panne moule/machine ; risque pour outillage ou équipement ; risque sécurité ; risque environnemental"),
            ('2', u"moule ou équipement en production mais en mode dégradé"),
            ('3', u"action d'amélioration ou de modification"),
            ], u"Gravité", required=True)
    numero_qrci         = fields.Char(u"Numéro de QRCI")
    descriptif          = fields.Text('Descriptif')
    complement          = fields.Text(u"Complément d'information")
    nature              = fields.Selection([
            ('preventif', u"Préventif"),
            ('curatif', "Curatif"),
            ('amelioratif', u"Amélioratif"),
            ('securite', u"Sécurité"),
            ('predictif', u"Prédictif"),
            ('changement_de_version', "Changement de version"),
            ], "Nature")
    affectation_id      = fields.Many2one("is.ot.affectation", "Affectation")
    delai_previsionnel  = fields.Float(u"Délai prévisionnel (H)", digits=(14, 2))
    validation_ot       = fields.Selection([
            ("non", "Non"),
            ("oui", "Oui"),
        ], "Validation OT")
    motif               = fields.Char("Motif")
    temps_passe_ids     = fields.One2many('is.ot.temps.passe', 'ot_id', u"Temps passé")
    
    valideur_id         = fields.Many2one("res.users", "Valideur", default=lambda self: self.env.uid)
    validation_travaux  = fields.Selection([
            ("ok", "Ok"),
            ("non_ok", "Non Ok"),
        ], "Validation travaux")
    nouveau_delai       = fields.Date(u"Nouveau délai")
    commentaires_non_ok = fields.Text("Commentaire")


# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import datetime
from collections import defaultdict
from collections import OrderedDict


class is_fiche_tampographie_constituant(models.Model):
    _name = 'is.fiche.tampographie.constituant'
    _order = 'name'

    name = fields.Char('Constituant', required=True)


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
    _order = 'name asc'

    name = fields.Char(u'Type de réglage de la machine', required=True)


class is_fiche_tampographie_reglage(models.Model):
    _name = 'is.fiche.tampographie.reglage'
    _order = 'type_reglage_id asc'

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
    def vers_approbation_action(self):
        for obj in self:
            subject = u'[' + obj.name + u'] tampographie'
            email_to = obj.approbateur_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.fiche.tampographie'
            body_html=u""" 
                <p>Bonjour,</p> 
                <p>"""+nom+""" vient de passer la fiche de réglage tampographie <a href='"""+url+"""'>"""+obj.name+"""</a> à l'état 'Approbation'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, subject, body_html)
            obj.date_redaction = datetime.datetime.today()
            obj.state = "approbation"

    @api.multi
    def vers_approbation_to_valide_action(self):
        for obj in self:
            subject = u'[' + obj.name + u'] tampographie'
            email_to = obj.approbateur_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.fiche.tampographie'
            body_html=u""" 
                <p>Bonjour,</p> 
                <p>"""+nom+""" vient de passer la fiche de réglage tampographie <a href='"""+url+"""'>"""+obj.name+"""</a> à l'état 'Validé'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, subject, body_html)
            obj.date_redaction = datetime.datetime.today()
            obj.state = "valide"

    @api.multi
    def vers_approbation_to_redaction_action(self):
        for obj in self:
            subject = u'[' + obj.name + u'] tampographie'
            email_to = obj.approbateur_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.fiche.tampographie'
            body_html=u""" 
                <p>Bonjour,</p> 
                <p>"""+nom+""" vient de passer la fiche de réglage tampographie <a href='"""+url+"""'>"""+obj.name+"""</a> à l'état 'Rédaction'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """
            self.envoi_mail(email_from, email_to, subject, body_html)
            obj.date_redaction = datetime.datetime.today()
            obj.state = "redaction"

    @api.multi
    def vers_valide_to_approbation_action(self):
        for obj in self:
            subject = u'[' + obj.name + u'] tampographie'
            email_to = obj.approbateur_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.fiche.tampographie'
            body_html=u""" 
                <p>Bonjour,</p> 
                <p>"""+nom+""" vient de passer la fiche de réglage tampographie <a href='"""+url+"""'>"""+obj.name+"""</a> à l'état 'Approbation'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, subject, body_html)
            obj.date_redaction = datetime.datetime.today()
            obj.state = "approbation"

    @api.depends('state','redacteur_id','approbateur_id')
    def _compute(self):
        uid = self._uid
        for obj in self:
            vsb = False
            if obj.state == 'redaction' and (uid == obj.redacteur_id.id or uid == 1):
                vsb = True
            obj.vers_approbation_vsb = vsb
            vsb = False
            if obj.state == 'approbation' and (uid == obj.redacteur_id.id or uid == obj.approbateur_id.id or uid == 1):
                vsb = True
            obj.vers_approbation_to_redaction_vsb = vsb
            vsb = False
            if obj.state == 'approbation' and (uid == obj.approbateur_id.id or uid == 1):
                vsb = True
            obj.vers_approbation_to_valide_vsb = vsb
            vsb = False
            if obj.state == 'valide' and (uid == obj.approbateur_id.id or uid == 1):
                vsb = True
            obj.vers_valide_to_approbation_vsb = vsb

    @api.multi
    def get_recette_encrier(self):
        res = False
        for obj in self:
            for recette in obj.recette_ids:
                if recette.name == "3":
                    return '3'
        return '2'

    @api.multi
    def get_reglage_encrier(self):
        res = False
        for obj in self:
            for recette in obj.reglage_ids:
                if recette.name == "3":
                    return '3'
        return '2'

    @api.multi
    def get_recette_data(self):
        res = False
        recet = []
        rec_dict = defaultdict(list)
        for obj in self:
            for rec in obj.recette_ids:
                if rec.constituant_id not in recet:
                    recdict = {
                        'name': rec.name,
                        'product_id': rec.product_id.is_code + ' ' + rec.product_id.name,
                        'poids': rec.poids
                    }
                    rec_dict[rec.constituant_id.name].append(recdict)
        return rec_dict

    @api.multi
    def get_reglage_data(self):
        res = False
        recet = []
        rec_dict = defaultdict(list)
        for obj in self:
            for rec in obj.reglage_ids:
                if rec.type_reglage_id not in recet:
                    recdict = {
                        'name': rec.name,
                        'type_reglage': rec.reglage
                    }
                    rec_dict[rec.type_reglage_id.name].append(recdict)
        sort_rec_dict = OrderedDict(sorted(rec_dict.items(), key=lambda x: x[0]))
        return sort_rec_dict


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
    vers_approbation_vsb              = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
    vers_approbation_to_redaction_vsb = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
    vers_approbation_to_valide_vsb    = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)
    vers_valide_to_approbation_vsb    = fields.Boolean('Champ technique', compute='_compute', readonly=True, store=False)


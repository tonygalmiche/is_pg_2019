# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    is_valideur_n1 = fields.Many2one('res.users', string=u'Valideur Niveau 1')
    is_valideur_n2 = fields.Many2one('res.users', string=u'Valideur Niveau 2')


class is_demande_conges(models.Model):
    _name        = 'is.demande.conges'
    _description = u'Demande de congés'

    @api.multi
    def envoi_mail(self, email_from, email_to, email_cc, subject, body_html):
        for obj in self:
            vals = {
                'email_from'    : email_from,
                'email_to'      : email_to,
                'email_cc'      : email_cc,
                'subject'       : subject,
                'body_html'     : body_html,
            }
            email = self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)

    @api.multi
    def niveau1_send_mail_action(self):
        for obj in self:
            obj.date_validation_n1 = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Sent Mail to - Valideur Niveau 1 '
            email_to = obj.valideur_n1.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_cc = obj.createur_id.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Niveau 1'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)
            obj.signal_workflow('validation_n1')
        return True

    @api.multi
    def niveau2_send_mail_action(self):
        for obj in self:
            obj.date_validation_n2 = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Sent Mail to - Vers Validation Niveau 2'
            email_to = obj.valideur_n2.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_cc = obj.createur_id.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Niveau 2'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)
            obj.signal_workflow('validation_n2')
        return True

    @api.multi
    def rh_send_mail_action(self):
        for obj in self:
            obj.date_validation_rh = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Sent Mail to - Validation RH'
            email_to = obj.responsable_rh_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_cc = obj.createur_id.email
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Validation RH'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)
            obj.signal_workflow('validation_rh')
        return True

    @api.multi
    def vers_solde_action(self):
        for obj in self:
            obj.signal_workflow('solde')
        return True

    @api.multi
    def vers_annule_action(self):
        for obj in self:
            obj.signal_workflow('annule')
        return True

    @api.model
    def default_get(self, default_fields):
        res = super(is_demande_conges, self).default_get(default_fields)
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1) or False
        if emp_id:
            res['valideur_n1'] = emp_id.is_valideur_n1.id
            res['valideur_n2'] = emp_id.is_valideur_n2.id
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.demande.conges') or ''
        return super(is_demande_conges, self).create(vals)

    @api.depends('date_debut', 'demandeur_id')
    def _get_visible(self):
        for obj in self:
            if obj.date_debut:
                current_date = datetime.date.today()
                current_date_plus_ten = current_date + relativedelta(days=10)
                if obj.state == 'validation_n1':
                    if str(current_date_plus_ten) < obj.date_debut:
                        if obj.createur_id and obj.createur_id.id == self._uid or obj.demandeur_id and obj.demandeur_id.id == self._uid:
                            obj.vers_creation_annuler_btn_vsb = True
                    if str(current_date) <= obj.date_debut:
                        if obj.responsable_rh_id and obj.responsable_rh_id.id == self._uid:
                            obj.vers_creation_annuler_btn_vsb = True
                if obj.state == 'validation_n2':
                    if str(current_date_plus_ten) < obj.date_debut:
                        if obj.valideur_n2 and obj.valideur_n2.id == self._uid or obj.responsable_rh_id and obj.responsable_rh_id.id == self._uid:
                            obj.vers_creation_annuler_btn_vsb = True
                    if str(current_date) <= obj.date_debut:
                        if obj.responsable_rh_id and obj.responsable_rh_id.id == self._uid:
                            obj.vers_creation_annuler_btn_vsb = True


    name                          = fields.Char(u"N° demande")
    createur_id                   = fields.Many2one('res.users', u'Créateur', default=lambda self: self.env.user)
    date_creation                 = fields.Datetime(string=u'Date de création', default=lambda *a: fields.datetime.now())
    demandeur_id                  = fields.Many2one('res.users', 'Demandeur', default=lambda self: self.env.user)
    valideur_n1                   = fields.Many2one('res.users', 'Valideur Niveau 1')
    date_validation_n1            = fields.Datetime(string='Date validation N1')
    valideur_n2                   = fields.Many2one('res.users', 'Valideur Niveau 2')
    date_validation_n2            = fields.Datetime(string='Date validation N2')
    responsable_rh_id             = fields.Many2one('res.users', 'Responsable RH', default=lambda self: self.env.user.company_id.is_responsable_rh_id)
    date_validation_rh            = fields.Datetime(string='Date Responsable RH')
    type_demande                  = fields.Selection([
                                        ('cp_rtt_journee', u'CP ou RTT par journée entière'),
                                        ('cp_rtt_demi_journee', u'CP ou RTT par ½ journée'),
                                        ('rc_heures', 'RC en heures'),
                                        ], string='Type de demande')
    cp                            = fields.Float(string='CP (jours)')
    rtt                           = fields.Float(string='RTT (jours)')
    rc                            = fields.Float(string='RC (jours)')
    date_debut                    = fields.Date(string=u'Date début')
    date_fin                      = fields.Date(string='Date fin')
    le                            = fields.Date(string='Le')
    matin_ou_apres_midi           = fields.Selection([
                                        ('matin', 'Matin'),
                                        ('apres_midi', u'Après-midi')
                                        ], string=u'Matin ou après-midi')
    heure_debut                   = fields.Integer(string=u'Heure début')
    heure_fin                     = fields.Integer(string=u'Heure fin')
    raison_du_retour              = fields.Text(string='Raison du retour')
    raison_annulation             = fields.Text(string='Raison annulation')
    state                         = fields.Selection([
                                        ('creation', u'Création'),
                                        ('validation_n1', 'Validation niveau 1'),
                                        ('validation_n2', 'Validation niveau 2'),
                                        ('validation_rh', 'Validation RH'),
                                        ('solde', 'Soldé'),
                                        ('annule', u'Annulé')], string='State', readonly=True, default='creation')
    vers_creation_annuler_btn_vsb = fields.Boolean(string='Creation Annuler Btn Vsb', compute='_get_visible', default=False, readonly=True)


class is_demande_absence_type(models.Model):
    _name        = 'is.demande.absence.type'

    name = fields.Char(string='Name')


class is_demande_absence(models.Model):
    _name        = 'is.demande.absence'
    _description = u'Demande d’absence'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.demande.absence') or ''
        return super(is_demande_absence, self).create(vals)

    name          = fields.Char(u"N° demande")
    createur_id   = fields.Many2one('res.users', u'Créateur', default=lambda self: self.env.user)
    date_creation = fields.Datetime(string=u'Date de création', default=lambda *a: fields.datetime.now())
    type_absence  = fields.Many2one('is.demande.absence.type', string=u'Type d’absence')
    date_debut    = fields.Date(string='Date de début')
    date_fin      = fields.Date(string='Date de fin')
    employe_ids   = fields.Many2many('hr.employee', string=u'Employés')



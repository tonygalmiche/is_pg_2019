# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
import os
import unicodedata


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    is_valideur_n1      = fields.Many2one('res.users', string=u'Valideur Niveau 1')
    is_valideur_n2      = fields.Many2one('res.users', string=u'Valideur Niveau 2')
    is_droit_conges_ids = fields.One2many('is.droit.conges', 'employe_id', u"Droit aux congés")

    is_mode_communication = fields.Selection([
                                        ('courriel'    , u'Courriel'),
                                        ('sms'         , u'SMS'),
                                        ('courriel+sms','Courriel + SMS'),
                                        ], string='Mode de communication')
    is_mobile   = fields.Char(u"Mobile"  , help="Téléphone utilisé pour l'envoi des SMS pour les demandes de congés")
    is_courriel = fields.Char(u"Courriel", help="Courriel utilisé pour l'envoi des informations pour les demandes de congés")


class is_demande_conges(models.Model):
    _name        = 'is.demande.conges'
    _inherit=['mail.thread']
    _description = u'Demande de congés'
    _order       = 'name desc'


    def _format_mobile(self,mobile):
        err=''
        if not mobile:
            err=u'Mobile non renseigné pour le contact'
        else:
            mobile = mobile.replace(' ','')
            if len(mobile)!=10:
                err=u'Le numéro doit contenir 10 chiffres'
            else:
                if mobile[0:2]!='06' and mobile[0:2]!='07':
                    err=u'Le numéro du mobile doit commencer par 06 ou 07'
                else:
                    mobile='0033'+mobile[-9:]
        return mobile,err



    @api.multi
    def envoi_sms(self, mobile, message):
        """Envoi de SMS avec OVH"""
        cr , uid, context = self.env.args
        mobile,err = self._format_mobile(mobile)
        print mobile,err
        res=''
        quota=0
        if err=='':
            err=''
            user = self.env['res.users'].browse(uid)
            company = user.company_id
            message = unicodedata.normalize('NFD', message).encode('ascii', 'ignore')
            if company.is_sms_mobile:
                to,err2 = self._format_mobile(company.is_sms_mobile)
            else:
                to = mobile
            param = \
                'account='+(company.is_sms_account or '')+\
                '&login='+(company.is_sms_login or '')+\
                '&password='+(company.is_sms_password or '')+\
                '&from='+(company.is_sms_from or '')+\
                '&to='+to+\
                '&message='+message
            cde = 'curl --data "'+param+'" https://www.ovh.com/cgi-bin/sms/http2sms.cgi'
            res=os.popen(cde).readlines()
            if res[0].strip()=='KO':
                err=res[1].strip()
            if res[0].strip()=='OK':
                res=str(int(float(res[1].strip())))
        return res,err


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
    def creer_notification(self, subject,body_html):
        for obj in self:
            vals={
                'subject'       : subject,
                'body'          : body_html, 
                'body_html'     : body_html, 
                'model'         : self._name,
                'res_id'        : obj.id,
                'notification'  : True,
                #'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].create(vals)


    @api.multi
    def vers_validation_n1_action(self):
        for obj in self:
            obj.date_validation_n1 = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Demande de congés - Validation Niveau 1 '
            email_to = obj.valideur_n1.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email

            email_cc = ''
            if obj.mode_communication in ['courriel','courriel+sms'] and obj.courriel:
                email_cc = obj.courriel

            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.demande.conges'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Validation Niveau 1'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)

            subject   = u"vers Validation niveau 1"
            body_html = u"<p>Mail envoyé de "+str(email_from)+u" à "+str(email_to)+u" (cc="+str(email_cc)+u")</p>"+body_html
            self.creer_notification(subject,body_html)

            if obj.mode_communication in ['sms','courriel+sms'] and obj.mobile:
                message = """Bonjour, """ + nom + """ vient de passer la Demande de congés """ + obj.name + """ à l'état 'Validation Niveau 1'."""
                res,err = self.envoi_sms(obj.mobile, message)
                if err=='':
                    subject = u'SMS envoyé sur le '+obj.mobile+u' (il reste '+res+u' SMS sur le compte)'
                    self.creer_notification(subject,message)
                else:
                    self.creer_notification(u'ATTENTION : SMS non envoyé', err)

            obj.signal_workflow('validation_n1')
        return True

    @api.multi
    def vers_validation_n2_action(self):
        for obj in self:
            obj.date_validation_n2 = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Demande de congés - Validation Niveau 2'
            email_to = obj.valideur_n2.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email

            email_cc = ''
            if obj.mode_communication in ['courriel','courriel+sms'] and obj.courriel:
                email_cc = obj.courriel

            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.demande.conges'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Validation Niveau 2'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)

            subject   = u"vers Validation niveau 2"
            body_html = u"<p>Mail envoyé de "+str(email_from)+u" à "+str(email_to)+u" (cc="+str(email_cc)+u")</p>"+body_html
            self.creer_notification(subject,body_html)

            if obj.mode_communication in ['sms','courriel+sms'] and obj.mobile:
                message = """Bonjour, """ + nom + """ vient de passer la Demande de congés """ + obj.name + """ à l'état 'Validation Niveau 2'."""
                res,err = self.envoi_sms(obj.mobile, message)
                if err=='':
                    subject = u'SMS envoyé sur le '+obj.mobile+u' (il reste '+res+u' SMS sur le compte)'
                    self.creer_notification(subject,message)
                else:
                    self.creer_notification(u'ATTENTION : SMS non envoyé', err)

            obj.signal_workflow('validation_n2')
        return True

    @api.multi
    def vers_validation_rh_action(self):
        for obj in self:
            obj.date_validation_rh = datetime.datetime.today()
            subject = u'[' + obj.name + u'] Demande de congés - Validation RH'
            email_to = obj.responsable_rh_id.email
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email

            email_cc = ''
            if obj.mode_communication in ['courriel','courriel+sms'] and obj.courriel:
                email_cc = obj.courriel

            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(obj.id) + u'&view_type=form&model=is.demande.conges'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + obj.name + """</a> à l'état 'Validation RH'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            self.envoi_mail(email_from, email_to, email_cc, subject, body_html)

            subject   = u"vers Validation RH"
            body_html = u"<p>Mail envoyé de "+str(email_from)+u" à "+str(email_to)+u" (cc="+str(email_cc)+u")</p>"+body_html
            self.creer_notification(subject,body_html)

            if obj.mode_communication in ['sms','courriel+sms'] and obj.mobile:
                message = """Bonjour, """ + nom + """ vient de passer la Demande de congés """ + obj.name + """ à l'état 'Validation RH'."""
                res,err = self.envoi_sms(obj.mobile, message)
                if err=='':
                    subject = u'SMS envoyé sur le '+obj.mobile+u' (il reste '+res+u' SMS sur le compte)'
                    self.creer_notification(subject,message)
                else:
                    self.creer_notification(u'ATTENTION : SMS non envoyé', err)

            obj.signal_workflow('validation_rh')
        return True

    @api.multi
    def vers_solde_action(self):
        for obj in self:

            subject   = u"vers Soldé"
            self.creer_notification(subject,"")

            obj.signal_workflow('solde')
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


    @api.depends('state','demandeur_id','createur_id','responsable_rh_id','valideur_n1','valideur_n1')
    def _get_btn_vsb(self):
        uid = self._uid
        for obj in self:
            vers_creation       = False
            vers_annuler        = False
            vers_refuse         = False
            vers_validation_n1  = False
            vers_validation_n2  = False
            vers_validation_rh  = False
            vers_solde          = False
            fld_vsb             = False
            test_date           = False
            if obj.date_debut:
                current_date = datetime.date.today()
                current_date_plus_ten = current_date + relativedelta(days=10)
                if str(current_date_plus_ten) < obj.date_debut:
                    test_date = True

            if test_date:
                if obj.state == 'validation_n1' or obj.state == 'validation_n2' or obj.state == 'validation_rh':
                    if obj.createur_id.id == uid or obj.demandeur_id.id == uid or obj.valideur_n1.id == uid or obj.valideur_n2.id == uid or obj.responsable_rh_id.id == uid:
                        vers_creation = True

            if obj.state == 'validation_rh' and  obj.responsable_rh_id.id == uid:
                fld_vsb = True

            if obj.state == 'creation':
                if obj.valideur_n1:
                    if obj.createur_id.id == uid or obj.demandeur_id.id == uid or obj.valideur_n1.id == uid or obj.valideur_n2.id == uid or obj.responsable_rh_id.id == uid:
                        vers_validation_n1 = True
                else:
                    if obj.valideur_n2:
                        if obj.valideur_n2.id == uid or obj.responsable_rh_id.id == uid:
                            vers_validation_rh = True
                            vers_annuler       = True
                            vers_refuse        = True
                    else:
                        if obj.responsable_rh_id.id == uid:
                            vers_validation_rh = True
                            vers_annuler       = True
                            vers_refuse        = True

            if obj.state == 'validation_n1':
                if obj.valideur_n2:
                    if obj.valideur_n1.id == uid or obj.valideur_n2.id == uid or obj.responsable_rh_id.id == uid:
                        vers_validation_n2 = True
                        vers_annuler       = True
                        vers_refuse        = True
                else:
                    if obj.valideur_n1.id == uid or obj.responsable_rh_id.id == uid:
                        vers_validation_rh = True
                        vers_annuler       = True
                        vers_refuse        = True


            if obj.state == 'validation_n2':
                if obj.valideur_n2.id == uid or obj.responsable_rh_id.id == uid:
                    vers_validation_rh = True
                    vers_annuler       = True
                    vers_refuse        = True
            if obj.state == 'validation_rh':
                if obj.responsable_rh_id.id == uid:
                    vers_solde   = True
                    vers_annuler = True
                    vers_annuler = True


            obj.vers_creation_btn_vsb      = vers_creation
            obj.vers_annuler_btn_vsb       = vers_annuler
            obj.vers_refuse_btn_vsb        = vers_refuse
            obj.vers_validation_n1_btn_vsb = vers_validation_n1
            obj.vers_validation_n2_btn_vsb = vers_validation_n2
            obj.vers_validation_rh_btn_vsb = vers_validation_rh
            obj.vers_solde_btn_vsb         = vers_solde
            obj.fld_vsb                    = fld_vsb


    @api.depends('demandeur_id')
    def _compute_mode_communication(self):
        for obj in self:
            employes = self.env['hr.employee'].search([('user_id', '=', obj.demandeur_id.id)], limit=1)
            mode_communication = False
            mobile             = False
            courriel           = False
            for employe in employes:
                mode_communication = employe.is_mode_communication
                mobile             = employe.is_mobile
                courriel           = employe.is_courriel
            obj.mode_communication = mode_communication
            obj.mobile             = mobile
            obj.courriel           = courriel


    name                          = fields.Char(u"N° demande")
    createur_id                   = fields.Many2one('res.users', u'Créateur', default=lambda self: self.env.user        , copy=False)
    date_creation                 = fields.Datetime(string=u'Date de création', default=lambda *a: fields.datetime.now(), copy=False)
    demandeur_id                  = fields.Many2one('res.users', 'Demandeur', default=lambda self: self.env.user)

    mode_communication = fields.Selection([
                                        ('courriel'    , u'Courriel'),
                                        ('sms'         , u'SMS'),
                                        ('courriel+sms','Courriel + SMS'),
                                        ], string='Mode de communication'                                                , compute='_compute_mode_communication', readonly=True, store=True)
    mobile   = fields.Char(u"Mobile"  , help="Téléphone utilisé pour l'envoi des SMS pour les demandes de congés"        , compute='_compute_mode_communication', readonly=True, store=True)
    courriel = fields.Char(u"Courriel", help="Courriel utilisé pour l'envoi des informations pour les demandes de congés", compute='_compute_mode_communication', readonly=True, store=True)

    valideur_n1                   = fields.Many2one('res.users', 'Valideur Niveau 1')
    date_validation_n1            = fields.Datetime(string='Date validation N1', copy=False)
    valideur_n2                   = fields.Many2one('res.users', 'Valideur Niveau 2')
    date_validation_n2            = fields.Datetime(string='Date validation N2', copy=False)
    responsable_rh_id             = fields.Many2one('res.users', 'Responsable RH', default=lambda self: self.env.user.company_id.is_responsable_rh_id)
    date_validation_rh            = fields.Datetime(string='Date Responsable RH', copy=False)
    type_demande                  = fields.Selection([
                                        ('cp_rtt_journee', u'CP ou RTT par journée entière'),
                                        ('cp_rtt_demi_journee', u'CP ou RTT par ½ journée'),
                                        ('rc_heures', 'RC en heures'),
                                        ], string='Type de demande')
    cp                            = fields.Float(string='CP (jours)' , copy=False)
    rtt                           = fields.Float(string='RTT (jours)', copy=False)
    rc                            = fields.Float(string='RC (heures)', copy=False)
    date_debut                    = fields.Date(string=u'Date début')
    date_fin                      = fields.Date(string='Date fin')
    le                            = fields.Date(string='Le')
    matin_ou_apres_midi           = fields.Selection([
                                        ('matin', 'Matin'),
                                        ('apres_midi', u'Après-midi')
                                        ], string=u'Matin ou après-midi')
    heure_debut                   = fields.Integer(string=u'Heure début')
    heure_fin                     = fields.Integer(string=u'Heure fin')
    raison_du_retour              = fields.Text(string='Motif du retour'       , copy=False)
    raison_annulation             = fields.Text(string='Motif refus/annulation', copy=False)
    state                         = fields.Selection([
                                        ('creation', u'Brouillon'),
                                        ('validation_n1', 'Validation niveau 1'),
                                        ('validation_n2', 'Validation niveau 2'),
                                        ('validation_rh', 'Validation RH'),
                                        ('solde' , u'Soldé'),
                                        ('refuse', u'Refusé'),
                                        ('annule', u'Annulé')], string='State', readonly=True, default='creation')

    vers_creation_btn_vsb      = fields.Boolean(string='vers_creation_btn_vsb'     , compute='_get_btn_vsb', default=False, readonly=True)
    vers_annuler_btn_vsb       = fields.Boolean(string='vers_annuler_btn_vsb'      , compute='_get_btn_vsb', default=False, readonly=True)
    vers_refuse_btn_vsb        = fields.Boolean(string='vers_refuse_btn_vsb'       , compute='_get_btn_vsb', default=False, readonly=True)
    vers_validation_n1_btn_vsb = fields.Boolean(string='vers_validation_n1_btn_vsb', compute='_get_btn_vsb', default=False, readonly=True)
    vers_validation_n2_btn_vsb = fields.Boolean(string='vers_validation_n2_btn_vsb', compute='_get_btn_vsb', default=False, readonly=True)
    vers_validation_rh_btn_vsb = fields.Boolean(string='vers_validation_rh_btn_vsb', compute='_get_btn_vsb', default=False, readonly=True)
    vers_solde_btn_vsb         = fields.Boolean(string='vers_solde_btn_vsb'        , compute='_get_btn_vsb', default=False, readonly=True)
    fld_vsb                    = fields.Boolean(string='Field Vsb'                 , compute='_get_btn_vsb', default=False, readonly=True)


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


class is_droit_conges(models.Model):
    _name        = 'is.droit.conges'
    _description = u'Droit aux congés'
    _order       = 'employe_id,name'

    name          = fields.Char(u"Type", required=True)
    description   = fields.Char(u"Description", required=True)
    nombre        = fields.Float(u"Nombre", digits=(14,1))
    employe_id    = fields.Many2one('hr.employee', 'Employé', required=True, ondelete='cascade', readonly=True)



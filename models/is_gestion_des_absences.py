# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
import os
import unicodedata
import codecs
import base64
import csv, cStringIO


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



#class is_demande_conges_droit(models.Model):
#    _name        = 'is.demande.conges.droit'
#    _description = u'Droit sur demannde de congés'
#    _order       = 'conge_id,name'

#    name       = fields.Char(u"Type", required=True)
#    nombre     = fields.Float(u"Nombre", digits=(14,2))
#    conge_id   = fields.Many2one('is.demande.conges', 'Demande de congés', required=True, ondelete='cascade', readonly=True)


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
            user = self.env['res.users'].browse(self._uid)
            vals={
                'subject'       : subject,
                'body'          : body_html, 
                'body_html'     : body_html, 
                'model'         : self._name,
                'res_id'        : obj.id,
                'notification'  : True,
                'author_id'     : user.partner_id.id
                #'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].sudo().create(vals)


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
#        droits = self.cherche_droits(vals['demandeur_id'])
#        #droit_conges_ids = res['value']['droit_conges_ids']
#        ids=[]
#        for line in droits:
#            ids.append((0,0,line))
#        vals['droit_conges_ids'] =  ids
        return super(is_demande_conges, self).create(vals)



#    @api.multi
#    def write(self,vals):
#        res = super(is_demande_conges, self).write(vals)
#        if 'demandeur_id' in vals:
#            employes = self.env['hr.employee'].search([('user_id', '=', vals['demandeur_id'])], limit=1)
#            for employe in employes:
#                droits = self.env['is.droit.conges'].search([('employe_id', '=', employe.id)])
#                for droit in droits:
#                    v={
#                        'name'    : droit.name,
#                        'nombre'  : droit.nombre,
#                        'conge_id': self.id,
#                    }
#                    print 'v=',v
#                    self.env['is.demande.conges.droit'].create(v)
#        print 'vals write=',vals
#        return res


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
            droit_cp  = 0
            droit_rtt = 0
            droit_rc  = 0


            for employe in employes:
                mode_communication = employe.is_mode_communication
                mobile             = employe.is_mobile
                courriel           = employe.is_courriel

                droits = self.env['is.droit.conges'].search([('employe_id', '=', employe.id)])
                for droit in droits:
                    if droit.name=='CP':
                        droit_cp = droit.nombre
                    if droit.name=='RTT':
                        droit_rtt = droit.nombre
                    if droit.name=='RC':
                        droit_rc = droit.nombre

            print courriel, droit_cp


            obj.mode_communication = mode_communication
            obj.mobile             = mobile
            obj.courriel           = courriel
            obj.droit_cp  = droit_cp
            obj.droit_rtt = droit_rtt
            obj.droit_rc  = droit_rc
        return True


#    @api.multi
#    def cherche_droits(self, demandeur_id):
#        print demandeur_id
#        employes = self.env['hr.employee'].search([('user_id', '=', demandeur_id)], limit=1)
#        #value = {}
#        lines = []
#        for employe in employes:
#            droits = self.env['is.droit.conges'].search([('employe_id', '=', employe.id)])
#            for droit in droits:
#                print droit, droit.name,droit.nombre,employe.id
#                
#                vals={
#                    'name'    : droit.name,
#                    'nombre'  : droit.nombre,
#                }
#                print vals
#                lines.append(vals)
#        return lines
#        #value.update({'droit_conges_ids': lines})
#        #return  {'value': value}






    name                          = fields.Char(u"N° demande")
    createur_id                   = fields.Many2one('res.users', u'Créateur', default=lambda self: self.env.user        , copy=False)
    date_creation                 = fields.Datetime(string=u'Date de création', default=lambda *a: fields.datetime.now(), copy=False)
    demandeur_id                  = fields.Many2one('res.users', 'Demandeur', default=lambda self: self.env.user, required=True)

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
                                        ('cp_rtt_journee'     , u'CP ou RTT par journée entière'),
                                        ('cp_rtt_demi_journee', u'CP ou RTT par ½ journée'),
                                        ('rc_heures'          , u'RC en heures'),
                                        ('sans_solde'         , u'Congés sans solde'),
                                        ('autre'              , u'Autre'),
                                        ], string='Type de demande', required=True)
    autre_id                      = fields.Many2one('is.demande.conges.autre', 'Type autre')
    justificatif_ids              = fields.Many2many('ir.attachment', 'is_demande_conges_attachment_rel', 'demande_conges_id', 'file_id', u"Justificatif")
    cp                            = fields.Float(string='CP (jours)' , digits=(14,2), copy=False)
    rtt                           = fields.Float(string='RTT (jours)', digits=(14,2), copy=False)
    rc                            = fields.Float(string='RC (heures)', digits=(14,2), copy=False)

    droit_cp                      = fields.Float(string='Droit CP (jours)' , digits=(14,2), compute='_compute_mode_communication', readonly=True, store=True)
    droit_rtt                     = fields.Float(string='Droit RTT (jours)', digits=(14,2), compute='_compute_mode_communication', readonly=True, store=True)
    droit_rc                      = fields.Float(string='Droit RC (heures)', digits=(14,2), compute='_compute_mode_communication', readonly=True, store=True)

    date_debut                    = fields.Date(string=u'Date début')
    date_fin                      = fields.Date(string='Date fin')
    le                            = fields.Date(string='Le')
    matin_ou_apres_midi           = fields.Selection([
                                        ('matin', 'Matin'),
                                        ('apres_midi', u'Après-midi')
                                        ], string=u'Matin ou après-midi')
    #heure_debut                  = fields.Integer(string=u'Heure début')
    #heure_fin                    = fields.Integer(string=u'Heure fin')
    heure_debut                   = fields.Float(u"Heure début", digits=(14, 2))
    heure_fin                     = fields.Float(u"Heure fin"  , digits=(14, 2))
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



class is_demande_conges_autre(models.Model):
    _name        = 'is.demande.conges.autre'

    name = fields.Char(string='Autre congé', required=True)



class is_demande_absence_type(models.Model):
    _name        = 'is.demande.absence.type'

    name = fields.Char(string='Type', required=True)
    code = fields.Char(string='Code', help=u"Code sur 1 ou 2 caractères utilisé dans le calendrier des absences")

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
    type_absence  = fields.Many2one('is.demande.absence.type', string=u'Type d’absence', required=True)
    date_debut    = fields.Date(string='Date de début', required=True)
    date_fin      = fields.Date(string='Date de fin', required=True)
    employe_ids   = fields.Many2many('hr.employee', string=u'Employés', required=True)


class is_droit_conges(models.Model):
    _name        = 'is.droit.conges'
    _description = u'Droit aux congés'
    _order       = 'employe_id,name'

    name       = fields.Char(u"Type", required=True)
    nombre     = fields.Float(u"Nombre", digits=(14,2))
    employe_id = fields.Many2one('hr.employee', 'Employé', required=True, ondelete='cascade', readonly=False)



class is_demande_conges_export_cegid(models.Model):
    _name        = 'is.demande.conges.export.cegid'

    name       = fields.Char(u"N°export")
    date_debut = fields.Date(string='Date de début', required=True, default=lambda self: self._date_debut())
    date_fin   = fields.Date(string='Date de fin'  , required=True, default=lambda self: self._date_fin())
    user_id    = fields.Many2one('res.users', 'Employé')


    def _date_debut(self):
        now  = datetime.date.today()              # Ce jour
        j    = now.day                            # Numéro du jour dans le mois
        d    = now - datetime.timedelta(days=j)   # Dernier jour du mois précédent
        j    = d.day                              # Numéro jour mois précédent
        d    = d - datetime.timedelta(days=(j-1)) # Premier jour du mois précédent
        return d.strftime('%Y-%m-%d')


    def _date_fin(self):
        now  = datetime.date.today()            # Ce jour
        j    = now.day                          # Numéro du jour dans le mois
        d    = now - datetime.timedelta(days=j) # Dernier jour du mois précédent
        return d.strftime('%Y-%m-%d')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('is.demande.conges.export.cegid') or ''
        return super(is_demande_conges_export_cegid, self).create(vals)




    @api.multi
    def get_employe(self,user):
        employes = self.env['hr.employee'].search([('user_id','=',user.id)])
        if employes:
            return employes[0]
        return False

    @api.multi
    def fdate(self,date):
        d=datetime.datetime.strptime(date, '%Y-%m-%d')
        return d.strftime('%d/%m/%Y')


    @api.multi
    def export_cegid_action(self):
        for obj in self:
            print obj
            name='export-cegid-'+obj.name+'.txt'
            model='is.demande.conges.export.cegid'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')
            annee = str(obj.date_debut)[:4]
            f.write('***DEBUT***\r\n')
            f.write('000	000000	01/01/'+annee+'	31/12/'+annee+'\r\n')

            conges1 = self.env['is.demande.conges'].search([
                ('date_debut', '>=', obj.date_debut),
                ('date_debut', '<=', obj.date_fin),
                ('state','=', 'solde'),
            ])
            conges2 = self.env['is.demande.conges'].search([
                ('le', '>=', obj.date_debut),
                ('le', '<=', obj.date_fin),
                ('state','=', 'solde'),
            ])
            for c in (conges1+conges2):
                employe = self.get_employe(c.demandeur_id)
                if employe:
                    matricule = employe.is_matricule or ''
                    matricule = ('0000000000'+matricule)[-10:]
                    f.write('MAB\t')
                    f.write(matricule+'\t')
                    f.write(self.fdate(c.date_debut)+'\t')
                    f.write(self.fdate(c.date_fin)+'\t')
                    f.write(str(c.rtt)+'\t')
                    f.write(str(c.rtt*7)+'\t')
                    f.write('RTT\t')
                    f.write('RTT\t')
                    f.write('\t\t')
                    f.write('MAT\tPAM')
                    f.write('\r\n')
            f.write('***FIN***\r\n')

            #***DEBUT***
            #000	000000	01/12/2004	30/11/2005
            #MHE	0000000789	31/10/2005	27/11/2005	000001	0015	H Spé 01                           	BAS	00000000037.00000			
            #MHE	0000000789	31/10/2005	27/11/2005	000001	3111	RTT(Heures)                        	BAS	00000000028.00000			
            #MAB	0000000789	31/10/2005	31/10/2005	0001.00	0007.00	RTT	RTT                                			MAT	PAM
            #MAB	0000000789	02/11/2005	02/11/2005	0001.00	0007.00	RTT	RTT                                			MAT	PAM
            #MAB	0000000789	04/11/2005	04/11/2005	0001.00	0007.00	RTT	RTT                                			MAT	PAM
            #MAB	0000000789	18/11/2005	18/11/2005	0001.00	0007.00	RTT	RTT                                			MAT	PAM
            #***FIN***

            f.close()
            r = open(dest,'rb').read().encode('base64')
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            id = self.env['ir.attachment'].create(vals)



# -*- coding: utf-8 -*-

from openerp import models, fields, api


class is_gestion_des_absences_wiz(models.TransientModel):
    _name = 'is.gestion.des.absences.wiz'

    conges_reason = fields.Text('Reason', required=True)

    @api.multi
    def valider_reponse(self):
        conges_obj = self.env['is.demande.conges']
        if self._context and self._context.get('active_id'):
            conges = conges_obj.browse(self._context.get(('active_id')))
            subject = u'[' + conges.name + u'] Sent Mail to createur_id - raison_du_retour'
            email_to = conges.createur_id.id
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_cc = email_from
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(conges.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + conges.name + """</a> à l'état 'createur_id - raison_du_retour'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            conges.sudo().raison_du_retour = self.conges_reason
            conges.sudo().envoi_mail(email_from, email_to, email_cc, subject, body_html)
            conges.sudo().state = 'creation'
            conges.sudo().delete_workflow()
            conges.sudo().create_workflow()
        return {'type': 'ir.actions.act_window_close'}


class is_gestion_vers_annuler_wiz(models.TransientModel):
    _name = 'is.gestion.vers.annuler.wiz'

    conges_reason = fields.Text('Reason', required=True)

    @api.multi
    def valider_reponse(self):
        conges_obj = self.env['is.demande.conges']
        if self._context and self._context.get('active_id'):
            conges = conges_obj.browse(self._context.get(('active_id')))
            subject = u'[' + conges.name + u'] Sent Mail to createur_id - raison_annulation'
            email_to = conges.createur_id.id
            user = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_cc = email_from
            nom = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + u'/web#id=' + str(conges.id) + u'&view_type=form&model=is.ot'
            body_html = u""" 
                <p>Bonjour,</p> 
                <p>""" + nom + """ vient de passer la Demande de congés <a href='""" + url + """'>""" + conges.name + """</a> à l'état 'createur_id - raison_annulation'.</p> 
                <p>Merci d'en prendre connaissance.</p> 
            """ 
            conges.sudo().raison_annulation = self.conges_reason
            conges.sudo().envoi_mail(email_from, email_to, email_cc, subject, body_html)
            conges.sudo().signal_workflow('annule')
        return {'type': 'ir.actions.act_window_close'}


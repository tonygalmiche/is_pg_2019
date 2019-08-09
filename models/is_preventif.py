# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import time
import datetime


class is_mold(models.Model):
    _inherit = 'is.mold'

    @api.multi
    def vers_nouveau_preventif_mold(self):
        for data in self:
            context = dict(self.env.context or {})
            print "CONTEeeeeeeeeee",context
            context['moule'] = data.id
            return {
                'name': u"Préventif Moule",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.preventif.moule',
                'type': 'ir.actions.act_window',
#                 'res_id': obj.id,
                'domain': '[]',
                'context': context,
            }
        return True

    @api.model
    def default_get(self, default_fields):
        res = super(is_mold, self).default_get(default_fields)
        res['is_base_check'] = False
        user_obj = self.env['res.users']
        user_data = user_obj.browse(self._uid)
        if user_data and user_data.company_id.is_base_principale:
            res['is_base_check'] = True
        return res

    @api.depends()
    def _check_base_db(self):
        for obj in self:
            user_obj = self.env['res.users']
            user_data = user_obj.browse(self._uid)
            if user_data and user_data.company_id.is_base_principale:
                obj.is_base_check = True


    nb_cycles_actuel              = fields.Integer(string="Nombre de cycles actuel")
    periodicite_maintenance_moule = fields.Integer(string=u"Périodicité maintenance moule (nb cycles)")
    gamme_preventif_ids           = fields.Many2many('ir.attachment', 'is_mold_attachment_rel', 'mold_id', 'file_id', u"Gamme préventif")
    is_base_check                 = fields.Boolean(string="Is Base", compute="_check_base_db")
    is_preventif_moule            = fields.One2many('is.preventif.moule', 'moule', u'Préventif Moule')


class is_preventif_moule(models.Model):
    _name = 'is.preventif.moule'
    _rec_name = 'moule'

    @api.model
    def default_get(self, default_fields):
        res = super(is_preventif_moule, self).default_get(default_fields)
        if self._context and self._context.get('moule'):
            res['moule'] = self._context.get('moule')
        return res

    moule               = fields.Many2one('is.mold', string='Moule')
    date_preventif      = fields.Date(string=u'Date du préventif', default=fields.Date.context_today)
    fiche_preventif_ids = fields.Many2many('ir.attachment', 'is_preventif_moule_attachment_rel', 'preventif_id', 'file_id', u"Fiche de réalisation du préventif")


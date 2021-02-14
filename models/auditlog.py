# -*- coding: utf-8 -*-
from openerp import models, fields

class AuditlogRule(models.Model):
    _inherit = 'auditlog.rule'

    is_duree_conservation = fields.Integer(string=u'Durée de conservation des journaux (en mois)')



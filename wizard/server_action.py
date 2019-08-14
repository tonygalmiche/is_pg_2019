# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import time
import datetime


class add_is_mold_preventif_data(models.TransientModel):
    _name = 'add.is.mold.preventif.data'
    _description = u"Initialisation Critères généraux"

    @api.multi
    def add_data(self):
        systematique_array_obj = self.env['is.mold.systematique.array']
        systematique_obj = self.env['is.mold.operation.systematique']
        systematique_ids = systematique_obj.search([('active', '=', True)])
        specifique_array_obj = self.env['is.mold.specifique.array']
        specifique_obj = self.env['is.mold.operation.specifique']
        specifique_ids = specifique_obj.search([('active', '=', True)])
        specification_array_obj = self.env['is.mold.specification.array']
        specification_obj = self.env['is.mold.specification.particuliere']
        specification_ids = specification_obj.search([('active', '=', True)])
        if self._context and self._context.get('active_ids'):
            for data in self._context.get('active_ids'):
                for num in systematique_ids:
                    systematique_array_obj.create({
                        'operation_systematique_id': num.id,
                        'mold_id': data,
                    })
                for num in specifique_ids:
                    specifique_array_obj.create({
                        'operation_specifique_id': num.id,
                        'mold_id': data,
                    })
                for num in specification_ids:
                    specification_array_obj.create({
                        'specification_particuliere_id': num.id,
                        'mold_id': data,
                    })
        return True



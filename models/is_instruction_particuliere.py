# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class is_instruction_particuliere(models.Model):
    _inherit = 'is.instruction.particuliere'

    afficher_imprimer = fields.Selection([
        ('afficher'         , u'Afficher'),
        ('imprimer'         , u'Imprimer'),
        ('afficher-imprimer', u'Afficher et Imprimer'),
    ], 'Afficher / Imprimer', required=True, help=u'Afficher dans THEIA ou imprimer en PDF avec les documents de fabrication', default='imprimer')
    groupe_ids = fields.Many2many('is.theia.validation.groupe','is_instruction_particuliere_groupe_rel','ip_id','groupe_id', string="Groupes autorisés")


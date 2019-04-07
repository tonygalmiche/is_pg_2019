# -*- coding: utf-8 -*-

from openerp import pooler
from openerp import models,fields,api
from openerp.tools.translate import _


class is_capteur(models.Model):
    _name = 'is.capteur'
    _description = u"Capteurs pour usine 4.0"
    _order='date_heure desc'

    name       = fields.Char('Nom du capteur', select=True, required=True)
    date_heure = fields.Datetime('Date Heure', select=True, required=True)
    mesure     = fields.Float('Mesure', digits=(12,4))
    unite      = fields.Char('Unité')


# -*- coding: utf-8 -*-

from openerp import tools
from openerp import pooler
from openerp import models,fields,api
from openerp.tools.translate import _


class is_donnee_machine(models.Model):
    _name = 'is.donnee.machine'
    _description = u"Données des machines pour l'usine 4.0"
    _order='date_heure desc'

    name       = fields.Char('Machine', select=True, required=True)
    fichier    = fields.Char('Fichier', select=True, required=True)
    date_heure = fields.Datetime('Date Heure', select=True, required=True)
    of         = fields.Char('OF', select=True, required=True)
    of_id      = fields.Many2one("mrp.production", "Ordre de fabrication", select=True)
    line_ids   = fields.One2many("is.donnee.machine.line", "donnee_id", u"Données")


class is_donnee_machine_line(models.Model):
    _name = 'is.donnee.machine.line'
    _description = u"Lignes des données des machines pour l'usine 4.0"
    _order='name'

    donnee_id  = fields.Many2one("is.donnee.machine", u"Donnée machine", required=True, ondelete='cascade', readonly=True)
    name       = fields.Char('Donnée', select=True, required=True)
    valeur     = fields.Char('Valeur', select=True, required=True)
    of_id      = fields.Many2one("mrp.production", "Ordre de fabrication", select=True)


class is_donnee_machine_line_report(models.Model):
    _name = 'is.donnee.machine.line.report'
    _order = 'date_heure desc'
    _auto = False

    machine      = fields.Char('Machine', select=True, required=True)
    fichier      = fields.Char('Fichier', select=True, required=True)
    date_heure   = fields.Datetime('Date Heure', select=True, required=True)
    of_id        = fields.Many2one("mrp.production", "OF", select=True)
    donnee       = fields.Char('Donnée', select=True, required=True)
    valeur       = fields.Char('Valeur', select=True, required=True)
    of_valeur_id = fields.Many2one("mrp.production", "OF Valeur", select=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_donnee_machine_line_report')
        cr.execute("""
            CREATE OR REPLACE view is_donnee_machine_line_report AS (
                select
                    l.id,
                    e.name as machine,
                    e.fichier,
                    e.date_heure,
                    e.of_id,
                    l.name as donnee,
                    l.valeur,
                    l.of_id as of_valeur_id
                from is_donnee_machine e inner join is_donnee_machine_line l on l.donnee_id=e.id 
            )
        """)





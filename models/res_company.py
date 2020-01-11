# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def update_group(self):
        for data in self:
            principale_grp_id = self.env.ref('is_pg_2019.is_base_principale_grp')
            secondaire_grp_id = self.env.ref('is_pg_2019.is_base_secondaire_grp')
            if data.company_id.is_base_principale:
                principale_grp_id.write({'users': [(4, data.id)]})
                secondaire_grp_id.write({'users': [(5, data.id)]})
            else:
                secondaire_grp_id.write({'users': [(4, data.id)]})
                principale_grp_id.write({'users': [(5, data.id)]})
        return True

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        res.update_group()
        return res


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def write(self, vals):
        base_group_id = self.env.ref('base.group_user')
        principale_grp_id = self.env.ref('is_pg_2019.is_base_principale_grp')
        secondaire_grp_id = self.env.ref('is_pg_2019.is_base_secondaire_grp')
        if vals and vals.get('is_base_principale'):
            principale_grp_id.write({'users': [(4, user) for user in base_group_id.users.ids]})
            secondaire_grp_id.write({'users': [(5, user) for user in base_group_id.users.ids]})
        if vals.get('is_base_principale') == False:
            secondaire_grp_id.write({'users': [(4, user) for user in base_group_id.users.ids]})
            principale_grp_id.write({'users': [(5, user) for user in base_group_id.users.ids]})
        return super(ResCompany, self).write(vals)

    is_responsable_rh_id = fields.Many2one('res.users', string='Responsable RH')



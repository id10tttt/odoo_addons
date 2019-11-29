# -*- coding: utf-8 -*-
# Copyright 2017 Jarvis (www.odoomod.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'


    # _sql_constrains = [('name_uniq','unique(name)','name already exist!')]

    @api.constrains('name')
    def _check_name(self):
        res = self.env['res.partner'].search([('name', '=', self.name),
                                              ('company_id', '=', self.company_id.id)])
        if len(res) > 1:
            raise ValidationError('已经存在该客户了 %s' % self.name)
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import traceback
import logging
from odoo.exceptions import Warning, ValidationError, UserError
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _name = 'hr.employee'

    @api.constrains('name', 'address_home_id')
    def _check_name(self):
        res = self.env['hr.employee'].search([('name', '=', self.name),
                                              ('company_id', '=', self.company_id.id)])
        if len(res) > 1:
            raise ValidationError('当前公司: [ %s ] 下,已经存在该员工:  [ %s ]' % (self.company_id.name, self.name))
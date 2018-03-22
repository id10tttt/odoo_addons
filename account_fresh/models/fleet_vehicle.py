#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError, UserError
from odoo.osv import *
import traceback

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _name = 'fleet.vehicle'

    # _sql_constraints = [('license_plate_uniq', 'unique (license_plate)', "license_plate already exists !")]
    # company_id = fields.Many2one('res.company', 'Company', required=True)



    @api.constrains('license_plate')
    def _validate_plate(self):
        res = self.env['fleet.vehicle'].sudo().search([('license_plate', '=', self.license_plate)])
        if len(res) > 1:
            raise ValidationError(u'已经存在该车牌，不能创建相同的车牌!!!')
        else:
            if not res.company_id:
                raise ValidationError(u'必须选中公司哦!')

    @api.constrains('company_id')
    def _check_company(self):
        print self.company_id
        if not self.company_id:
            raise ValidationError('You must choose company!')

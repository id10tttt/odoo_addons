#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError, UserError
from odoo.osv import *
import traceback

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _name = 'fleet.vehicle'

    # company_id = fields.Many2one('res.company', 'Company', required=True)



    @api.constrains('license_plate')
    def _validate_plate(self):
        res = self.env['fleet.vehicle'].sudo().search([('license_plate', '=', self.license_plate),
                                                       ('company_id', '=', self.company_id.id)])
        if len(res) > 1:
            raise ValidationError(u'已经存在该车牌 [%s]，不能创建相同的车牌!!!' % self.license_plate)
        else:
            if not res.company_id:
                raise ValidationError(u'必须选择公司!')

class FleetVehicleModelBrand(models.Model):
    _inherit = 'fleet.vehicle.model.brand'
    _name = 'fleet.vehicle.model.brand'


    @api.constrains('name')
    def _check_name(self):
        res = self.env['fleet.vehicle.model.brand'].sudo().search([('name', '=', self.name)])
        if len(res) > 1:
            raise ValidationError(u'已经存在该型号 [%s]，不能创建相同的型号!!!' % self.name)

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'
    _name = 'fleet.vehicle.model'

    @api.constrains('name')
    def _check_name(self):
        res = self.env['fleet.vehicle.model'].sudo().search([('name', '=', self.name),
                                                             ('brand_id', '=', self.brand_id.id)])
        if len(res) > 1:
            raise ValidationError(u'已经存在该车辆型号 [%s]，不能创建相同的车辆型号!!!' % self.name)
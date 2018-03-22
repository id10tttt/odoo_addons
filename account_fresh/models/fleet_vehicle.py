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
        res = self.env['fleet.vehicle'].sudo().search([('license_plate', '=', self.license_plate)])
        if len(res) > 1:
            raise ValidationError(u'已经存在该车牌 [%s]，不能创建相同的车牌!!!' % self.license_plate)
        else:
            if not res.company_id:
                raise ValidationError(u'必须选中公司哦!')


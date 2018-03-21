#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError
from odoo.osv import *

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _name = 'fleet.vehicle'

    company_id = fields.Many2one('res.company', 'Company', required=True)

    _sql_constraints = [
        ('_check_company_id', 'check(company_id)', 'The company_id field is invalid')
    ]
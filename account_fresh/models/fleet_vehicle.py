#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import *

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _name = 'fleet.vehicle'
# -*- coding: utf-8 -*-
import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning
import traceback
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class FleetProfit(models.Model):
    _name = 'fleet.profit'
    _description = '每辆车每天的利润'

    vehicle_fleet = fields.Many2one('fleet.vehicle',u'车辆')
    vehicle_income = fields.Float(u'收入')
    vehicle_date = fields.Date(u'日期')
    vehicle_cost = fields.Float(u'成本')
    vehicle_profit = fields.Float(u'利润')

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import traceback

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _name = 'hr.expense'

    contain_tax_price = fields.Float(string='tax_price', required=True)
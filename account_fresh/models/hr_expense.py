# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import traceback

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _name = 'hr.expense'

    # contain_tax_price = fields.Float(string='tax_price', required=True)
    tax_ids = fields.Many2many('account.tax', 'expense_tax', 'expense_id', 'tax_id', string='Taxes', states={'done': [('readonly', True)], 'post': [('readonly', True)]})

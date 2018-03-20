# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Quant(models.Model):
    _inherit = 'stock.quant'
    _name = 'stock.quant'

    owner = fields.Many2one('res.partner', string='Owner')
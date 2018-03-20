# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class RemovalStrategy(models.Model):
    _inherit = 'product.removal'
    _name = 'product.removal'

    owner = fields.Many2one('res.partner',string='Owner')


class PutAwayStrategy(models.Model):
    _inherit = 'product.putaway'
    _name = 'product.putaway'

    owner = fields.Many2one('res.partner', string='Owner')



# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import traceback
from odoo.exceptions import Warning

class StockPickingExternal(models.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'

    # @api.multi
    # def confirm_all_move(self):
    #     for x in self.pack_operation_product_ids:
    #         for y in x.pack_lot_ids:
    #             y.qty = y.qty_todo
    #         x.qty_done = x.product_qty

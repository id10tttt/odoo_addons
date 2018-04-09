# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductUom(models.Model):
    _inherit = 'product.uom'
    _name = 'product.uom'

    @api.multi
    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP'):
        '''
        更改销售里面的已送货、已开票数量的精度
        '''
        if not self:
            return qty
        self.ensure_one()
        if self.category_id.id != to_unit.category_id.id:
            if self._context.get('raise-exception', True):
                raise UserError(_('Conversion from Product UoM %s to Default UoM %s is not possible as they both belong to different Category!.') % (self.name, to_unit.name))
            else:
                return qty
        amount = qty / self.factor
        if to_unit:
            amount = amount * to_unit.factor
            if round:
                amount = tools.float_round(amount, precision_rounding=0.000001, rounding_method=rounding_method)
        return amount
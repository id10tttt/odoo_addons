# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import traceback
import logging
import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _name = 'hr.expense'

    contain_tax_price_unit = fields.Float(string='tax_price', store=True)

    unit_amount = fields.Float(string='Unit Price',
                               default=0.0,
                               compute='_compute_no_tax_price',
                               readonly=True,
                               required=True,
                               store=True,
                               states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                               digits=dp.get_precision('Product Price'))


    @api.multi
    @api.depends('contain_tax_price_unit', 'tax_ids')
    def _compute_no_tax_price(self):
        """
        计算不含税单价，当含税单价、不含税单价、税率变化时，自动计算不含税单价
        :return:
        """
        try:
            for x in self:
                tax_rate = x.tax_ids.amount / 100.0
                x.unit_amount = x.contain_tax_price_unit / (tax_rate + 1.0)
        except Exception, e:
            _logger.warning(traceback.format_exc())

    @api.multi
    def _prepare_move_line_value(self):
        res = super(HrExpense, self)._prepare_move_line_value()
        res['vehicle_id'] = self.vehicle_id.id
        return res
    @api.multi
    def _prepare_move_line(self, line):
        res = super(HrExpense, self)._prepare_move_line(line)
        res['vehicle_id'] = line.get('vehicle_id')
        return res

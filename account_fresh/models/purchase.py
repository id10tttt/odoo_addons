# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import traceback
import logging
_logger = logging.getLogger(__name__)

class PurchaseExternal(models.Model):
    '''
    添加负责人和订单号
    '''
    _inherit = 'purchase.order'
    _name = 'purchase.order'

    purchase_number = fields.Char(string='purchase_id')
    principal = fields.Many2one('res.partner')

class PurchaseOrderLineExternal(models.Model):
    '''
    添加含税价格，重写不含税价格，不含税价格改为计算字段
    price_unit = contain_tax_price / ((taxes_id.amount / 100.0) + 1.0)
    添加车牌号
    '''
    _inherit = 'purchase.order.line'
    _name = 'purchase.order.line'

    contain_tax_price = fields.Float(string='tax_price', required=True, default=0.0)
    price_unit = fields.Float(string='no_tax_price',
                              compute='_compute_no_tax_price',
                              default=0.0)

    vehicle_id = fields.Many2one('fleet.vehicle', u'车牌号',
                                 ondelete='restrict')

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'contain_tax_price')
    def _compute_amount(self):
        for line in self:
            # print 'line: ', line
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('contain_tax_price', 'price_unit', 'taxes_id')
    @api.multi
    def _compute_no_tax_price(self):
        try:
            for x in self:
                tax_rate = x.taxes_id.amount / 100.0
                x.price_unit = x.contain_tax_price / (tax_rate + 1.0)
        except Exception,e:
            _logger.warning(traceback.format_exc())

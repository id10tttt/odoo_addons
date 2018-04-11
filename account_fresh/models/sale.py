# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import traceback
import logging
_logger = logging.getLogger(__name__)

class SaleOrderExternal(models.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    sale_order_number = fields.Char(string='sale_id')

class SaleOrderLineExternal(models.Model):
    '''
    添加含税价格，车牌号，订单分类，共配专车字段
    不含税价格更改为计算字段
    复写 _prepare_invoice_line ，主要因为添加了车牌号等字段
    '''
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    contain_tax_price = fields.Float(string='tax_price', required=True, default=0.0)
    price_unit = fields.Float(string='no_tax_price', compute='_compute_no_tax_price')
    account_analytic_id = fields.Many2one('account.analytic.account','analytic_account')

    vehicle_id = fields.Many2one('fleet.vehicle', u'车牌号',
                            ondelete='restrict')
    otype_id = fields.Many2one('core.value', u'订单分类',
                            ondelete='restrict',
                            domain=[('type', '=', 'otype_id')],
                            context={'type': 'otype_id'})
    ctype_id = fields.Many2one('core.value', u'共配专车',
                            ondelete='restrict',
                            domain=[('type', '=', 'ctype_id')],
                            context={'type': 'ctype_id'})

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'contain_tax_price')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    @api.onchange('contain_tax_price', 'price_unit', 'tax_id')
    def _compute_no_tax_price(self):
        """
        计算不含税单价，当含税单价、不含税单价、税率变化时，自动计算不含税单价
        :return:
        """
        try:
            for x in self:
                tax_rate = x.tax_id.amount / 100.0
                x.price_unit = x.contain_tax_price / (tax_rate + 1.0)
        except Exception,e:
            _logger.warning(traceback.format_exc())

    @api.multi
    def _prepare_invoice_line(self, qty):
        try:
            res = super(SaleOrderLineExternal, self)._prepare_invoice_line(qty)

            res.update({
                'vehicle_id': self.vehicle_id.id,
                'otype_id': self.otype_id.id,
                'ctype_id': self.ctype_id.id,
                'account_analytic_id': self.account_analytic_id.id
            })
            return res
        except Exception,e:
            _logger.warning(traceback.format_exc())

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        try:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            for line in self:
                if not float_is_zero(qty, precision_digits=precision):
                    vals = line._prepare_invoice_line(qty=qty)
                    if vals:
                        vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                        self.env['account.invoice.line'].create(vals)
        except UserError,e:
            raise UserError(e.message)
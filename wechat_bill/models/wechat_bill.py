#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WechatBill(models.Model):
    _name = 'wechat.bill'
    _rec_name = 'transaction_datetime'

    transaction_datetime = fields.Datetime('Transaction datetime')
    transaction_type_id = fields.Many2one('wechat.bill.type', 'Transaction type')
    transaction_partner_id = fields.Many2one('res.partner', 'Transaction partner')
    transaction_product_id = fields.Many2one('product.product', 'Transaction product')

    income_expend_type = fields.Selection([
        ('income', 'Income'),
        ('expend', 'Expenses'),
        ('/', '/')
    ], string='Type')
    amount = fields.Float('Amount')
    payment_method = fields.Many2one('wechat.bill.payment.method', string='Payment method')

    transaction_number = fields.Char('Transaction number')
    merchant_number = fields.Char('Merchant number')
    note = fields.Char('Note')
    payment_state_id = fields.Many2one('wechat.bill.payment.state', 'Payment state')


class WechatBillType(models.Model):
    _name = 'wechat.bill.type'

    name = fields.Char('Name')


class WechatBillPaymentMethod(models.Model):
    _name = 'wechat.bill.payment.method'

    name = fields.Char('Name')


class WechatBillPaymentState(models.Model):
    _name = 'wechat.bill.payment.state'

    name = fields.Char('Name')
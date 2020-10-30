#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from pyecharts.charts import Line
from pyecharts.charts import Pie
from pyecharts import options as opts
import json


def echarts_wechat_bill_daily_bi(record_values) -> Line:
    if not record_values:
        return {}
    xaxis_data = [x.get('transaction_date') for x in record_values]
    yaxis_data = [x.get('daily_amount') for x in record_values]
    c = (
        Line()
            .add_xaxis(xaxis_data=xaxis_data)
            .add_yaxis(series_name="交易额", y_axis=yaxis_data)
            .set_global_opts(
            title_opts=opts.TitleOpts(title="交易额", subtitle="每天"),
            datazoom_opts=opts.DataZoomOpts(),
            tooltip_opts=opts.TooltipOpts(trigger='axis'),
            toolbox_opts=opts.ToolboxOpts(is_show=True,
                                          feature=opts.ToolBoxFeatureOpts(
                                              data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=False),
                                              brush=opts.ToolBoxFeatureBrushOpts(type_='clear')
                                          ))
        )
    )

    res = c.dump_options_with_quotes()
    return json.loads(res)


def echarts_wechat_bill_2_person_bi(record_values) -> Pie:
    if not record_values:
        return {}
    record_values = [(x.get('partner_name'), x.get('amount')) for x in record_values]
    c = (
        Pie()
        .add("", record_values)
        .set_global_opts(title_opts=opts.TitleOpts(title="交易对象"))
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{b}: {c}")
        )
    )
    res = c.dump_options_with_quotes()
    return json.loads(res)


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

    @api.model
    def get_extra_domain(self, **kwargs):
        search_domain = 'WHERE 1=1 '
        if kwargs.get('date_start'):
            search_domain += '''
             AND transaction_datetime >= '{}'
            '''.format(kwargs.get('date_start'))
        if kwargs.get('date_stop'):
            search_domain += '''
                         AND transaction_datetime <= '{}'
                        '''.format(kwargs.get('date_stop'))
        return search_domain

    def _get_wechat_bill_daily_bi_data(self, extra_domain):
        sql = '''
            select to_char(transaction_datetime, 'YYYY-MM-DD') as transaction_date, sum(amount) as daily_amount
            from wechat_bill {extra_domain}
            group by transaction_date order by transaction_date asc
        '''.format(
            extra_domain=extra_domain
        )
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def get_wechat_bill_daily_bi_data(self, user_id=None, **kwargs):
        try:
            extra_domain = self.get_extra_domain(**kwargs)
            record_values = self._get_wechat_bill_daily_bi_data(extra_domain)
            return echarts_wechat_bill_daily_bi(record_values)
        except Exception as e:
            raise e

    def _get_wechat_bill_2_person_bi_data(self, extra_domain):
        sql = '''
            with res as (
                select transaction_partner_id, sum(amount) as amount
                from wechat_bill {extra_domain}
                group by transaction_partner_id
            )select rp.name as partner_name, res.amount 
            from res 
                join res_partner as rp 
                on res.transaction_partner_id = rp.id
        '''.format(
            extra_domain=extra_domain
        )
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def get_wechat_bill_2_person_bi_data(self, user_id=None, **kwargs):
        extra_domain = self.get_extra_domain(**kwargs)

        record_values = self._get_wechat_bill_2_person_bi_data(extra_domain)
        return echarts_wechat_bill_2_person_bi(record_values)


class WechatBillType(models.Model):
    _name = 'wechat.bill.type'

    name = fields.Char('Name')


class WechatBillPaymentMethod(models.Model):
    _name = 'wechat.bill.payment.method'

    name = fields.Char('Name')


class WechatBillPaymentState(models.Model):
    _name = 'wechat.bill.payment.state'

    name = fields.Char('Name')

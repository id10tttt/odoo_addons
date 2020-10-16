# -*- coding: utf-8 -*-
from odoo import models, api
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.charts import Bar
from pyecharts.charts import Pie
import json
from odoo.tools import float_round
from itertools import groupby


def parse_dashboard_count_xaxis_data(daily_partner_data, daily_order_partner_data):
    daily_partner_keys = [x.get('create_date') for x in daily_partner_data]
    daily_order_partner_keys = [x.get('create_date') for x in daily_order_partner_data]

    all_keys = daily_partner_keys + daily_order_partner_keys
    all_keys = list(set(all_keys))
    all_keys = sorted(all_keys)
    return all_keys


def get_all_daily_order_partner_value(all_keys, values, fields='value'):
    value_keys = [x.get('create_date') for x in values]
    diff_keys = list(set(all_keys) - set(value_keys))

    diff_keys = sorted(diff_keys)

    for diff_key in diff_keys:
        values.append({
            'create_date': diff_key,
            fields: 0
        })
    values = sorted(values, key=lambda x: x.get('create_date'))
    return [x.get(fields) if x.get(fields) else 0 for x in values]


def parse_res_partner_crm_dashboard_count(daily_partner_data, daily_order_partner_data) -> Line:
    xaxis_data = parse_dashboard_count_xaxis_data(daily_partner_data, daily_order_partner_data)
    partner_value = get_all_daily_order_partner_value(xaxis_data, daily_partner_data)
    order_partner_value = get_all_daily_order_partner_value(xaxis_data, daily_order_partner_data,
                                                            fields='order_partner_count')
    order_count_value = get_all_daily_order_partner_value(xaxis_data, daily_order_partner_data, fields='order_count')

    c = (
        Line()
            .add_xaxis(xaxis_data=xaxis_data)
            .add_yaxis(series_name="注册数量", y_axis=partner_value)
            .add_yaxis(series_name="下单客户数", y_axis=order_partner_value)
            .add_yaxis(series_name="订单数量", y_axis=order_count_value)
            .set_global_opts(
            title_opts=opts.TitleOpts(title="数量统计", subtitle="单位(个)"),
            datazoom_opts=opts.DataZoomOpts(),
            toolbox_opts=opts.ToolboxOpts()
        )
    )

    res = c.dump_options_with_quotes()
    return json.loads(res)


def parse_res_partner_crm_dashboard_stage_pie(result) -> Pie:
    if not result:
        return {}
    c = (
        Pie()
            .add("", result)
            .set_global_opts(title_opts=opts.TitleOpts(title="客户等级"))
            .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{b}: {c}"),
            toolbox_opts=opts.ToolboxOpts()
        )
    )
    res = c.dump_options_with_quotes()
    return json.loads(res)


def parse_res_partner_crm_dashboard_order_total_bar(result) -> Bar:
    all_keys = [x.get('create_date') for x in result]
    yaxis_data = [x.get('value') for x in result]
    c = (
        Bar()
            .add_xaxis(all_keys)
            .add_yaxis("日销售额", yaxis_data)
            .set_global_opts(
            title_opts=opts.TitleOpts(title="销售额"),
            toolbox_opts=opts.ToolboxOpts(),
            datazoom_opts=opts.DataZoomOpts(),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    res = c.dump_options_with_quotes()
    return json.loads(res)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_allow_user_ids(self, user_id):
        if not user_id:
            return []
        member_ids = self.env['crm.team'].search([('user_id', '=', user_id)])
        if member_ids:
            allow_users_ids = member_ids.mapped('member_ids').ids
            allow_users_ids.append(user_id)
        else:
            allow_users_ids = [user_id]
        return allow_users_ids

    def get_extra_domain(self, search_domain, **kwargs):
        if kwargs.get('date_start'):
            search_domain.append(('create_date', '>=', kwargs.get('date_start')))
        if kwargs.get('date_stop'):
            search_domain.append(('create_date', '<=', kwargs.get('date_stop')))
        return search_domain

    def get_all_allow_partner_ids(self, allow_users_ids, **kwargs):
        if self.env.user._is_admin() or self.env.user.has_group('crm_metrics.group_seller_manager'):
            search_domain = []
        else:
            search_domain = [('user_id', 'in', allow_users_ids)]

        search_domain = self.get_extra_domain(search_domain, **kwargs)

        res = self.env['res.partner'].search(search_domain)
        return res

    @api.model
    def get_res_partner_bi_statistical(self, user_id=None, **kwargs):

        allow_users_ids = self.get_allow_user_ids(user_id)

        all_partner_ids = self.get_all_allow_partner_ids(allow_users_ids, **kwargs)

        search_domain = [
            ('partner_id', 'in', all_partner_ids.ids),
            ('state', '!=', 'cancel')
        ]
        search_domain = self.get_extra_domain(search_domain, **kwargs)
        all_order_count = self.env['sale.order'].search_count(search_domain)
        all_sale_order_ids = self.env['sale.order'].search_read(domain=search_domain,
                                                                fields=['amount_total', 'partner_id'],
                                                                order='create_date')

        all_order_price_total = sum(x.get('amount_total') for x in all_sale_order_ids)

        all_order_price_total = float_round(all_order_price_total, 2)
        all_order_partner_ids = [x.get('partner_id') for x in all_sale_order_ids]
        all_order_partner_ids = list(set(all_order_partner_ids))
        return {
            'partner_count': len(all_partner_ids),
            'order_partner_count': len(all_order_partner_ids),
            'order_count': all_order_count,
            'order_total': all_order_price_total
        }

    def get_all_allow_daily_partner_ids(self, allow_users_ids, **kwargs):
        if self.env.user._is_admin() or self.env.user.has_group('crm_metrics.group_seller_manager'):
            search_domain = []
        else:
            search_domain = [('user_id', 'in', allow_users_ids)]

        search_domain = self.get_extra_domain(search_domain, **kwargs)

        res = self.env['res.partner'].search_read(domain=search_domain, fields=['id', 'create_date'],
                                                  order='create_date')
        return res

    def get_all_allow_daily_order_partner_ids(self, all_partner_ids, **kwargs):
        search_domain = [('partner_id', 'in', all_partner_ids.ids)]
        search_domain = self.get_extra_domain(search_domain, **kwargs)

        res = self.env['sale.order'].search_read(domain=search_domain, fields=['id', 'partner_id', 'create_date'],
                                                 order='create_date')
        return res

    @api.model
    def parse_daily_partner_value(self, daily_partner_ids):
        for order_data in daily_partner_ids:
            order_data.update({
                'create_date': str(order_data.get('create_date').strftime('%Y-%m-%d'))
            })
        data = []
        group_data = groupby(daily_partner_ids, lambda x: x.get('create_date'))
        for group_key, group_value in group_data:
            all_id = [x.get('id') for x in group_value]
            tmp = {
                'create_date': str(group_key),
                'value': len(all_id)
            }
            data.append(tmp)
        return data

    @api.model
    def parse_daily_order_partner_value(self, daily_order_partner):
        for order_data in daily_order_partner:
            order_data.update({
                'create_date': str(order_data.get('create_date').strftime('%Y-%m-%d'))
            })
        data = []
        group_data = groupby(daily_order_partner, lambda x: x.get('create_date'))

        for group_key, group_value in group_data:
            all_order_partner = [x.get('partner_id') for x in group_value]
            order_partner = list(set(all_order_partner))
            tmp = {
                'create_date': str(group_key),
                'order_count': len(all_order_partner),
                'order_partner_count': len(order_partner)
            }
            data.append(tmp)
        return data

    @api.model
    def get_res_partner_crm_dashboard_count(self, user_id=None, **kwargs):
        allow_users_ids = self.get_allow_user_ids(user_id)

        all_partner_ids = self.get_all_allow_partner_ids(allow_users_ids, **kwargs)

        daily_partner_ids = self.get_all_allow_daily_partner_ids(allow_users_ids, **kwargs)

        daily_order_partner = self.get_all_allow_daily_order_partner_ids(all_partner_ids, **kwargs)

        daily_partner_data = self.parse_daily_partner_value(daily_partner_ids)
        daily_order_partner_data = self.parse_daily_order_partner_value(daily_order_partner)

        return parse_res_partner_crm_dashboard_count(daily_partner_data, daily_order_partner_data)

    @api.model
    def parse_sale_order_data(self, sale_order_data):
        for order_data in sale_order_data:
            order_data.update({
                'create_date': str(order_data.get('create_date').strftime('%Y-%m-%d'))
            })
        data = []
        group_data = groupby(sale_order_data, lambda x: x.get('create_date'))

        for group_key, group_value in group_data:
            amount_total = sum(float(x.get('amount_total')) for x in group_value)
            amount_total = float_round(amount_total, 2)
            tmp = {
                'create_date': str(group_key),
                'value': amount_total,
            }
            data.append(tmp)
        return data

    @api.model
    def get_res_partner_crm_dashboard_order_total(self, user_id=None, **kwargs):
        allow_users_ids = self.get_allow_user_ids(user_id)
        all_partner_ids = self.get_all_allow_partner_ids(allow_users_ids, **kwargs)

        search_domain = [
            ('partner_id', 'in', all_partner_ids.ids),
            ('state', '!=', 'cancel')
        ]
        search_domain = self.get_extra_domain(search_domain, **kwargs)

        sale_order_data = self.env['sale.order'].search_read(
            domain=search_domain,
            fields=['amount_total', 'create_date'],
            order='create_date')

        result = self.parse_sale_order_data(sale_order_data)
        return parse_res_partner_crm_dashboard_order_total_bar(result)

    @api.model
    def parse_res_partner_crm_dashboard_stage_pie(self, partner_data):
        all_stage = self.env['crm.stage'].search([])
        data = []
        group_data = groupby(partner_data, lambda x: x.get('stage_id'))

        for group_key, group_value in group_data:
            all_data = [x for x in group_value]
            try:
                group_key_value = all_stage.filtered(lambda x: x.id == group_key[0])
            except Exception as e:
                group_key_value = False
            tmp = [group_key_value.name if group_key_value else 'NULL', len(all_data)]
            data.append(tmp)
        return data

    @api.model
    def get_res_partner_crm_dashboard_stage_pie(self, user_id, **kwargs):
        allow_users_ids = self.get_allow_user_ids(user_id)

        if self.env.user._is_admin() or self.env.user.has_group('crm_metrics.group_seller_manager'):
            search_domain = []
        else:
            search_domain = [('user_id', 'in', allow_users_ids)]

        search_domain = self.get_extra_domain(search_domain, **kwargs)

        res = self.env['res.partner'].search_read(domain=search_domain, fields=['stage_id', 'id'],
                                                  order='stage_id')
        result = self.parse_res_partner_crm_dashboard_stage_pie(res)

        return parse_res_partner_crm_dashboard_stage_pie(result)

    def get_category_data(self, all_category_ids, category_id):
        if not category_id:
            return 'NULL'
        category_id = all_category_ids.filtered(lambda x: x.id == category_id[0])
        if category_id:
            return category_id.name
        return 'NULL'

    @api.model
    def get_res_partner_crm_dashboard_category(self, user_id=None, **kwargs):
        allow_users_ids = self.get_allow_user_ids(user_id)
        if self.env.user._is_admin() or self.env.user.has_group('crm_metrics.group_seller_manager'):
            search_domain = []
        else:
            search_domain = [('user_id', 'in', allow_users_ids)]
        search_domain = self.get_extra_domain(search_domain, **kwargs)

        res = self.env['res.partner'].read_group(domain=search_domain,
                                                 fields=['id'], groupby='xb_category_id')

        all_category_ids = self.env['xb.res.partner.category'].search([])

        result = [{
            'category_name': self.get_category_data(all_category_ids, x.get('xb_category_id')),
            'count': x.get('xb_category_id_count')
        } for x in res]
        return result

# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import http
import requests
from odoo.http import request
import json
from odoo.tools import config
import logging
from pyecharts import options as opts
from pyecharts.charts import Sankey
from pyecharts.faker import Faker
from pyecharts.globals import GeoType

_logger = logging.getLogger(__name__)


def get_all_wechat_bill(record_id):
    if record_id:
        bill_id = request.env['wechat.bill'].sudo().browse(record_id)
        bill_ids = request.env['wechat.bill'].sudo().search([
            ('transaction_partner_id', '=', bill_id.transaction_partner_id.id),
        ])
    else:
        # 数量多了，会出错
        bill_ids = request.env['wechat.bill'].sudo().search([])

    all_partner_ids = bill_ids.mapped('transaction_partner_id')
    all_product_ids = bill_ids.mapped('transaction_product_id')
    all_nodes = get_all_node(all_partner_ids, all_product_ids)

    # 所有的 link 是交易的总和
    all_links = get_all_link(bill_ids)
    return all_nodes, all_links


def get_all_node(all_partner_ids, all_product_ids):
    # 去除重复的
    all_nodes = list(set(all_partner_ids)) + list(set(all_product_ids))

    # 去除重复
    all_nodes_name = [x.name for x in all_nodes]
    all_nodes_name = list(set(all_nodes_name))
    res = []
    for node_name in all_nodes_name:
        res.append({
            'name': node_name
        })
    return res


def get_all_link(bill_ids):
    all_partner_product_ids = [(x.transaction_partner_id, x.transaction_product_id) for x in bill_ids]
    all_partner_product_ids = list(set(all_partner_product_ids))

    all_links = []
    for partner_product_id in all_partner_product_ids:
        record_ids = bill_ids.filtered(
            lambda x: x.transaction_partner_id == partner_product_id[0] and
                      x.transaction_product_id == partner_product_id[1]
        )
        # 名字重复会报错
        if partner_product_id[0].name != partner_product_id[1].name:
            all_links.append({
                'source': partner_product_id[0].name,
                'target': partner_product_id[1].name,
                'value': sum(x.amount for x in record_ids)
            })
    return all_links


def get_sankey_view(all_nodes, all_links) -> Sankey:
    colors = [
        "#67001f",
        "#b2182b",
        "#d6604d",
        "#f4a582",
        "#fddbc7",
        "#d1e5f0",
        "#92c5de",
        "#4393c3",
        "#2166ac",
        "#053061",
    ]
    # all_node_ids, all_link_ids = get_all_wechat_bill(False)
    c = (
        Sankey()
            .set_colors(colors)
            .add(
            "sankey",
            all_nodes,
            all_links,
            pos_bottom="10%",
            pos_left="20%",
            node_width=10,
            is_draggable=True,
            focus_node_adjacency="allEdges",
            linestyle_opt=opts.LineStyleOpts(opacity=0.2, curve=0.5, color="source"),
            label_opts=opts.LabelOpts(position="left"),
        )
        #     .add(
        #     "All",
        #     all_node_ids,
        #     all_link_ids,
        #     pos_bottom="10%",
        #     pos_left="20%",
        #     node_width=10,
        #     is_draggable=True,
        #     focus_node_adjacency="allEdges",
        #     linestyle_opt=opts.LineStyleOpts(opacity=0.2, curve=0.5, color="source"),
        #     label_opts=opts.LabelOpts(position="left"),
        # )
            .set_global_opts(title_opts=opts.TitleOpts(title="Sankey"),
                             tooltip_opts=opts.TooltipOpts(trigger="item", trigger_on="mousemove"),
                             )
    )
    return c.dump_options_with_quotes()


class GetSankeyView(http.Controller):
    @http.route('/api/get_sankey_view/<int:record_id>', type="http", auth="none", methods=["GET"], csrf=False)
    def get_sankey_view(self, record_id=False, **post):
        all_nodes, all_links = get_all_wechat_bill(record_id)
        sankey_data = get_sankey_view(all_nodes, all_links)
        return sankey_data

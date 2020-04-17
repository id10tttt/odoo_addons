# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import http
import requests
from odoo.http import request
import json
from odoo.tools import config
import logging
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Line, Pie, Tab
from pyecharts.commons.utils import JsCode
from pyecharts.faker import Faker

_logger = logging.getLogger(__name__)


def get_all_personal_weight(record_id):
    res = request.env['personal.weight'].sudo().browse(record_id)
    all_weight = request.env['personal.weight'].sudo().search([
        ('person', '=', res.person)
    ])
    xaxis = all_weight.filtered(lambda x: x.am_pm_type == 'am').mapped('date')

    am_yaxis = all_weight.filtered(lambda x: x.am_pm_type == 'am').mapped('weight')
    pm_yaxis = all_weight.filtered(lambda x: x.am_pm_type == 'pm').mapped('weight')
    return xaxis, am_yaxis, pm_yaxis


def bar_datazoom_slider(xaxis, am_yaxis, pm_yaxis) -> Bar:
    c = (
        Bar()
        .add_xaxis(xaxis)
        .add_yaxis("上午", am_yaxis)
        .add_yaxis("下午", pm_yaxis)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Bar图"),
            datazoom_opts=[opts.DataZoomOpts()],
        )
    )
    return c.dump_options_with_quotes()


def line_markpoint(xaxis, am_yaxis, pm_yaxis) -> Line:
    c = (
        Line()
        .add_xaxis(xaxis)
        .add_yaxis(
            "上午",
            am_yaxis,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="min")]),
        )
        .add_yaxis(
            "下午",
            pm_yaxis,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]),
        )
        .set_global_opts(title_opts=opts.TitleOpts(title="折线图"))
    )
    return c.dump_options_with_quotes()

def get_line_view(xaxis, am_yaxis, pm_yaxis):
    line_data = line_markpoint(xaxis, am_yaxis, pm_yaxis)
    return line_data

def get_bar_view(xaxis, am_yaxis, pm_yaxis):
    line_data = bar_datazoom_slider(xaxis, am_yaxis, pm_yaxis)
    return line_data


class GetWeightLineView(http.Controller):
    @http.route('/api/get_weight_line_view/<int:record_id>', type="http", auth="none", methods=["GET"], csrf=False)
    def get_weight_line_view(self, record_id=False, **post):
        xaxis, am_yaxis, pm_yaxis = get_all_personal_weight(record_id)
        weight_line_data = get_line_view(xaxis, am_yaxis, pm_yaxis)
        return weight_line_data

    @http.route('/api/get_weight_bar_view/<int:record_id>', type="http", auth="none", methods=["GET"], csrf=False)
    def get_weight_bar_view(self, record_id=False, **post):
        xaxis, am_yaxis, pm_yaxis = get_all_personal_weight(record_id)
        weight_line_data = get_bar_view(xaxis, am_yaxis, pm_yaxis)
        return weight_line_data
# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from pyecharts.charts import Bar
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.faker import Faker


def parse_crm_dashboard_bar_data() -> Bar:
    c = (
        Bar()
            .add_xaxis(
            [
                "名字很长的X轴标签1",
                "名字很长的X轴标签2",
                "名字很长的X轴标签3",
                "名字很长的X轴标签4",
                "名字很长的X轴标签5",
                "名字很长的X轴标签6",
            ]
        )
            .add_yaxis("商家A", [10, 20, 30, 40, 50, 40])
            .add_yaxis("商家B", [20, 10, 40, 30, 40, 50])
            .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
            title_opts=opts.TitleOpts(title="Bar-测试", subtitle="CRM-DASHBOARD 测试"),
        )
    )
    return c.dump_options_with_quotes()


def parse_crm_dashboard_line_data() -> Line:
    c = (
        Line()
            .add_xaxis(Faker.choose())
            .add_yaxis("商家A", Faker.values())
            .add_yaxis("商家B", Faker.values())
            .set_global_opts(title_opts=opts.TitleOpts(title="Line-基本示例"))
    )
    return c.dump_options_with_quotes()


class CrmDashboardControllers(http.Controller):

    @http.route('/crm_dashboard/statistical/bar', type="http", auth="none", methods=["GET"], csrf=False)
    def get_crm_dashboard_statistical_bar(self):
        print(request.env.user)
        return parse_crm_dashboard_bar_data()

    @http.route('/crm_dashboard/statistical/line', type="http", auth="none", methods=["GET"], csrf=False)
    def get_crm_dashboard_statistical_line(self):
        return parse_crm_dashboard_line_data()

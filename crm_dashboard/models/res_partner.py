# -*- coding: utf-8 -*-
from odoo import models, api
from pyecharts import options as opts
from pyecharts.charts import Bar
import json


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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_res_partner_statistical_bar(self, user_id=None):
        if not user_id:
            return {}
        result = parse_crm_dashboard_bar_data()
        return json.loads(result)

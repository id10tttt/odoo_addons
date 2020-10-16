odoo.define('crm_dashboard.dashboard_echarts', function (require) {
    "use strict";

    let AbstractAction = require('web.AbstractAction');
    let core = require('web.core');
    let ajax = require('web.ajax');
    let session = require('web.session');

    let CrmDashboardEcharts = AbstractAction.extend({
        template: 'crm_dashboard.EchartsCrmDashboard',
        // 需要额外引入的css文件
        cssLibs: [],
        // 需要额外引入的js文件
        jsLibs: [
            // 'https://cdn.staticfile.org/echarts/4.7.0/echarts.min.js',
            '/crm_dashboard/static/src/lib/echarts.min.js',
        ],
        // 事件绑定相关定义
        events: {
            'click #datetime_apply_search': 'search_apply'
        },

        // action的构造器，可以自行根据需求填入需要初始化的数据，比如获取context里的参数，根据条件判断初始化一些变量。
        init: function (parent, context) {
            this.echart_option = {};
            this._super(parent, context);
        },
        // willStart是执行介于init和start中间的一个异步方法，一般会执行向后台请求数据的请求，并储存返回来的数据。
        // 其中ajax.loadLibs(this)会帮加载定义在cssLibs，jsLibs的js组件。
        willStart: function () {
            let self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function () {
                console.log('willStart!');
            });
        },
        // start方法会在渲染完template后执行，此时可以做任何需要处理的事情。
        // 比如根据willStart返回来数据，初始化引入的第三方js库组件
        start: function () {
            let self = this;
            return this._super().then(function () {
                let date_range = self.get_default_start_stop_date();

                let date_start = date_range.date_start;
                let date_stop = date_range.date_stop;

                self.render_chart(date_start = date_start, date_stop = date_stop);
            });
        },

        set_default_start_stop_date_picker: function (date_start, date_stop) {
            this.$("#date_start").val(date_start);
            this.$("#date_stop").val(date_stop);
        },
        get_default_start_stop_date: function () {
            let time = new Date();
            let year = time.getFullYear();
            let month = time.getMonth() + 1;
            let day = time.getDate();
            let date_stop = year + '-' + month + '-' + day;
            let date_start = year + '-' + (month - 6) + '-' + day;

            this.set_default_start_stop_date_picker(date_start, date_stop);

            return {
                date_start: date_start,
                date_stop: date_stop
            }
        },
        render_chart: function (date_start = null, date_stop = null) {
            // 统计值
            this.set_bi_statistical(date_start = date_start, date_stop = date_stop);

            //每日统计
            this.set_bi_crm_dashboard_count(date_start = date_start, date_stop = date_stop);

            // 销售额
            this.set_crm_dashboard_order_total(date_start = date_start, date_stop = date_stop);

            //客户等级
            this.set_crm_dashboard_stage_pie(date_start = date_start, date_stop = date_stop);

            //客户类型
            this.set_crm_dashboard_category(date_start = date_start, date_stop = date_stop);

        },
        search_apply: function () {
            let start_date = $("#date_start").val();
            let date_stop = $("#date_stop").val();
            this.render_chart(start_date, date_stop);
            this.set_bi_statistical(start_date, date_stop);
        },
        set_bi_statistical: function (date_start = null, date_stop = null) {
            let that = this;
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_bi_statistical',
                args: [],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let reg_obj = that.$el.find('#reg_count');
                    let order_partner_obj = that.$el.find('#order_partner_count');
                    let order_count_obj = that.$el.find('#order_count');
                    let order_total_obj = that.$el.find('#order_total');

                    reg_obj[0].innerText = result.partner_count;
                    order_partner_obj[0].innerText = result.order_partner_count;
                    order_count_obj[0].innerText = result.order_count;
                    order_total_obj[0].innerText = result.order_total;
                }
            });
        },
        set_bi_crm_dashboard_count: function (date_start = null, date_stop = null) {
            let crm_dashboard_count = this.$el.find('#crm_dashboard_count')[0];
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_crm_dashboard_count',
                args: [],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let crm_line_echarts = echarts.init(crm_dashboard_count, {renderer: 'canvas'});
                    crm_line_echarts.setOption(result);
                }
            });
        },
        set_crm_dashboard_order_total: function (date_start = null, date_stop = null) {
            let crm_dashboard_order = this.$el.find('#crm_dashboard_order')[0];
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_crm_dashboard_order_total',
                args: [],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let crm_order_echarts = echarts.init(crm_dashboard_order, {renderer: 'canvas'});
                    crm_order_echarts.setOption(result);
                }
            });
        },
        set_crm_dashboard_stage_pie: function (date_start = null, date_stop = null) {
            let crm_dashboard_stage = this.$el.find('#crm_dashboard_stage')[0];
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_crm_dashboard_stage_pie',
                args: [],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let partner_stage_echarts = echarts.init(crm_dashboard_stage, {renderer: 'canvas'});
                    partner_stage_echarts.setOption(result);
                }
            });
        },
        set_crm_dashboard_category: function (date_start = null, date_stop = null) {
            let that = this;
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_crm_dashboard_category',
                args: [],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let str = '<div class="row p-3 mb-1 bg-primary text-white" style="padding: 10px 0 0 0;">' +
                        '<div class="col-sm-4">序号</div> ' +
                        '<div class="col-sm-4">名称</div>' +
                        '<div class="col-sm-4">数量</div>' +
                        '</div>';
                    for (let i in result) {
                        let current_index = parseInt(i) + 1
                        str += '<div class="row bg-primary p-3 mb-1 text-white" style="padding: 10px 0 0 0;">' +
                            '<div class="col-sm-4">' + current_index + '</div> ' +
                            '<div class="col-sm-4">' + result[i].category_name + '</div>' +
                            '<div class="col-sm-4">' + result[i].count + '</div>' +
                            '</div>'
                    }
                    let customer_category_obj = that.$el.find('#customer_category');
                    customer_category_obj[0].innerHTML = str;
                }
            });
        },

    });

    core.action_registry.add('crm_dashboard.dashboard_echarts', CrmDashboardEcharts);

    return CrmDashboardEcharts;

});

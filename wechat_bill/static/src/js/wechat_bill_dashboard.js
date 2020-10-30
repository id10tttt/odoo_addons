odoo.define('wechat_bill.wechat_bill_dashboard', function (require) {
    "use strict";

    let AbstractAction = require('web.AbstractAction');
    let core = require('web.core');
    let ajax = require('web.ajax');
    let session = require('web.session');
    let _t = core._t;

    let WeChatBillDashboard = AbstractAction.extend({
        template: 'wechat_bill.WeChatBillDashboardTemplate',
        // 需要额外引入的css文件
        cssLibs: [],
        // 需要额外引入的js文件
        jsLibs: [
            '/wechat_bill/static/src/lib/echarts.min.js',
        ],
        // 事件绑定相关定义
        events: {
            'click #datetime_apply_search': 'search_apply',
            'click #o_cp_fullscreen': 'toggle_fullscreen',
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
                console.log('Shall we! Let\'s dance!');
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
            //每日统计
            this.set_wechat_bill_daily_bi(date_start = date_start, date_stop = date_stop);

            // 针对不同主体的统计
            this.set_wechat_bill_2_person_bi(date_start = date_start, date_stop = date_stop);

        },
        search_apply: function () {
            let start_date = $("#date_start").val();
            let date_stop = $("#date_stop").val();
            this.render_chart(start_date, date_stop);
        },
        set_wechat_bill_daily_bi: function (date_start = null, date_stop = null) {
            let wechat_bill_daily_bi = this.$el.find('#wechat_bill_daily_bi')[0];
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'wechat.bill',
                method: 'get_wechat_bill_daily_bi_data',
                args: [session.uid],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let bill_daily_bi_echarts = echarts.init(wechat_bill_daily_bi, {renderer: 'canvas'});
                    bill_daily_bi_echarts.setOption(result);
                }
            });
        },
        set_wechat_bill_2_person_bi: function (date_start = null, date_stop = null) {
            let wechat_bill_2_person_bi = this.$el.find('#wechat_bill_2_person_bi')[0];
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'wechat.bill',
                method: 'get_wechat_bill_2_person_bi_data',
                args: [session.uid],
                kwargs: {
                    user_id: session.uid,
                    date_start: date_start,
                    date_stop: date_stop,
                }
            }).then(function (result) {
                if (result) {
                    let bill_2_person_echarts = echarts.init(wechat_bill_2_person_bi, {renderer: 'canvas'});
                    bill_2_person_echarts.setOption(result);
                }
            });
        },
        toggle_fullscreen: function () {
            $(".o_main_navbar").toggle();
        }
    });

    core.action_registry.add('wechat_bill.wechat_bill_dashboard', WeChatBillDashboard);

    return WeChatBillDashboard;

});

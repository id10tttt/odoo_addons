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
        jsLibs: ['https://cdn.staticfile.org/echarts/4.7.0/echarts.min.js'],
        // 事件绑定相关定义
        events: {},
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
        }

        ,
        // start方法会在渲染完template后执行，此时可以做任何需要处理的事情。
        // 比如根据willStart返回来数据，初始化引入的第三方js库组件
        start: function () {
            let self = this;
            return this._super().then(function () {
                console.log("in action start!");
                console.log('session: ', session)
                self.render_chart();
            });
        }
        ,
        render_chart: function () {
            let crm_bar = this.$el.find('#crm_dashboard_bar')[0];
            let crm_line = this.$el.find('#crm_dashboard_line')[0];
            let crm_line_echarts = echarts.init(crm_line, {renderer: 'canvas'});

            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'res.partner',
                method: 'get_res_partner_statistical_bar',
                args: [],
                kwargs: {
                    user_id: session.uid
                }
            }).then(function (result){
                if(result){
                    let crm_bar_echarts = echarts.init(crm_bar, {renderer: 'canvas'});
                    crm_bar_echarts.setOption(result);
                }
            })
            $.ajax({
                type: "GET",
                url: window.location.origin + "/crm_dashboard/statistical/line",
                dataType: "json",
                success: function (result) {
                    try {
                        crm_line_echarts.setOption(result);
                    } catch (error) {
                        console.log(error);
                    }
                }
            });
        },
    });

    core.action_registry.add('crm_dashboard.dashboard_echarts', CrmDashboardEcharts);

    return CrmDashboardEcharts;

})
;

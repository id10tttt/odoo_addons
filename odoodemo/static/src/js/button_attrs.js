odoo.define('odoodemo.add_new_button', function (require) {
    "use strict";
    let core = require('web.core');
    let ListView = require('web.ListView');
    let Model = require('web.Model');
    let session = require('web.session');
    let web_client = require('web.web_client');
    let ajax = require("web.ajax");
    let Dialog = require('web.Dialog');
    let form_widget = require("web.form_widgets");
    let QWeb = core.qweb;
    let _t = core._t;
    // let rpc_request = require('web.rpc');
    let test_func = form_widget.WidgetButton.include({

        on_click: function () {
            if (this.node.attrs.custom === "test_input_custom_js") {

                console.log("Hello world!");
                let test1 = $('.test_input_template_test_1');
                let test2 = $('.test_input_template_test_2');
                let test_code = test1.val();
                console.log('test1', test1);
                console.log('test2', test2);
                test1[0].value = 'Hello';
                test2[0].value = 'World';
                let txt1 = "<table class=\"o_group o_inner_group o_group_col_6\">\n" +
                    "                                            <tr>\n" +
                    "                                                <td>\n" +
                    "                                                    测试4\n" +
                    "                                                </td>\n" +
                    "                                                <td>\n" +
                    "                                                    <input type=\"text\" class=\"test_input_template_test_4\" name=\"测试4\"/>\n" +
                    "                                                </td>\n" +
                    "                                            </tr>\n" +
                    "                                        </table>";
                let txt2 = $("<p></p>").text("Text.");   // 以 jQuery 创建新元素
                let txt3 = document.createElement("p");  // 以 DOM 创建新元素
                txt3.innerHTML = "Text.";

                $('#test_add_auto_js').append(txt1, txt2, txt3);

                // new Model('add.new.button').call('test_rpc_js_method', ['', test_code]).then(function (res) {
                //     console.log(res);
                //     new Dialog.confirm(this, res.msg, {
                //         'title': 'Message'
                //     });
                // });

                return;
            }
            this._super();
        },
    });
});

odoo.define('odoodemo.switch_write_read', function (require) {
    "use strict";
    let core = require('web.core');
    let ListView = require('web.ListView');
    let ListEditor = require('web.ListEditor');
    let FormView = require('web.FormView');
    let Model = require('web.Model');
    let Widget = require('web.Widget');

    ListView.include({
        func_switch_write_read: function () {
            this.editable();
            this.reload_content();
        },
        editable: function () {
            let check_state = $('.switch_write_read_controller:checkbox:checked').val();
            if (typeof check_state != "undefined") {
                if (check_state == "on") {
                    return "bottom";
                }
            }
            return this._super.apply(this, arguments);
        },
        cancel_edition: function (force){
            return this._super.apply(this, arguments)
        },
        render_buttons: function () {
            let add_button = false;
            if (!this.$buttons) {
                add_button = true;
            }
            let result =  this._super.apply(this, arguments);
            if (add_button) {
                let self = this;
                this.$buttons
                    .on('click', '#switch_write_read_controller', this.func_switch_write_read.bind(this))
                    .off('click', '.o_list_button_save')
                    .on('click', '.o_list_button_save', this.proxy('save_edition'))
                    .off('click', '.o_list_button_discard')
                    .on('click', '.o_list_button_discard', function (e) {
                        e.preventDefault();
                        self.cancel_edition();
                    });
            }
            return result;
        }
    });
});

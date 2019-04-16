odoo.define('switch_read_write.controller', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;
    var QWeb = core.qweb;
    ListController.include({
        custom_events: _.extend({}, ListController.prototype.custom_events, {update_fields: '_updateFields',}),
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$mode_switch = $(QWeb.render('switch_read_write.switch', {
                    id: 'mk-list-switch-' + this.controllerID,
                    label: "编辑",
                }));
                this.$buttons.find('.read_write_list_button_switch').html(this.$mode_switch);
                this.$mode_switch.on('change', 'input[type="checkbox"]', this._onSwitchMode.bind(this));
                this.$mode_switch.find('input[type="checkbox"]').prop('checked', !!this.editable);
            }
        },
        _updateFields: function (event) {
            event.stopPropagation();
            var state = this.model.get(this.handle);
            state.fieldsInfo[this.viewType] = event.data.fields;
            this.renderer.arch.children = event.data.arch;
            this.update({fieldsInfo: state.fieldsInfo}, {reload: true});
        },
        _updateButtons: function (mode) {
            this._super.apply(this, arguments);
            this.$mode_switch.find('input[type="checkbox"]').prop('checked', !!this.editable);
        },
        _onSwitchMode: function (event) {
            var editable = $(event.currentTarget).is(':checked');
            if (editable) {
                this.editable = 'top';
                this.renderer.editable = this.editable;
            } else {
                this.editable = false;
                this.renderer.editable = false;
            }
            this.update({}, {reload: true}).then(this._updateButtons.bind(this, 'readonly'));
        }
    });
});

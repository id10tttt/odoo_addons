odoo.define('wechat_bill.dialog_draggable', function (require) {
    'use strict';

    let Dialog = require('web.Dialog');

    Dialog.include({
        opened: function (handler) {
            return this._super.apply(this, arguments).then(function () {
                if (this.$modal) {
                    this.$modal.draggable({
                        handle: '.modal-header',
                        helper: false
                    });
                }
            }.bind(this));
        },
        close: function () {
            if (this.$modal) {
                var draggable = this.$modal.draggable("instance");
                if (draggable) {
                    this.$modal.draggable("destroy");
                }
            }
            return this._super.apply(this, arguments);
        },
    });
});

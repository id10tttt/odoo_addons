odoo.define('disable_quick_create.disbale_many2one_quick_create_edit', function (require) {
    "use strict";

    let relational_fields = require('web.relational_fields');

    relational_fields.FieldMany2One.include({
        init: function () {
            this._super.apply(this, arguments);
            this.can_create = false;
            this.can_write = false;
            this.nodeOptions = {
                quick_create: true,
            }
        }
    })
})

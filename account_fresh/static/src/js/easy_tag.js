odoo.define('account.easy_tag', function (require) {
    "use strict";

    var core = require('web.core');
    var form_widget_registry = core.form_widget_registry;
    var Registry = require('web.Registry');
    var registry = new Registry();

    var EasyTag = form_widget_registry.get('one2many_list').extend({
        events: {
            "click .easy_tag_class": "easy_tag_func",
        },
        easy_tag_func: function () {
            var a = $('td[data-field=name]');
            if (a.length > 1) {
                $('input[data-fieldname=name]').val(a[a.length - 2].innerHTML);
            }
            else {
                $('input[data-fieldname=name]').val('');
            }
        },
    });

    core.form_widget_registry
        .add('easy_tag', EasyTag)

    registry
        .add('easy_tag', EasyTag)
    return registry;
});

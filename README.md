# odoo_addons
*  一些扩展

* 科目显示最末级

## customize_odoo 模块
* 移植odoo 12 的 create方法，新建create_multi方法，可以在odoo 10 上 bulk create
    * 使用： data = [{}, {}, ...{}], self.env[xxx.xxx].create_multi(data)
 
## odoodemo模块(适用于odoo 10)  
* 新增在列表上切换编辑和只读模式, dynamic switch read and write in list view
```javascript
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
```
* 在create 后面新增按钮的案例，用法的模板
```javascript
    ListView.include({
        render_buttons: function () {
            let add_button = false;
            if (!this.$buttons) {
                add_button = true;
            }
            let result = this._super.apply(this, arguments);
            if (add_button) {
                this.$buttons.on('click', '.o_list_add_new_button', execute_open_action.bind(this));
            }
            return result;
        }
    });
```   
	

* 新增按钮上面的attrs，使用自带的button，来实现原生的js功能
```javascript
    let test_func = form_widget.WidgetButton.include({
        on_click: function () {
            if (this.node.attrs.custom === "test_input_custom_js") {
                console.log("Hello world!");
                return;
            }
            this._super();
        },
    });
```

## switch_read_write 模块(适用于odoo 12)
* 新增在列表上切换编辑和只读模式, dynamic switch read and write in list view
```javascript
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
```
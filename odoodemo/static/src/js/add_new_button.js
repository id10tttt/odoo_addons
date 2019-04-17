odoo.define('add_new_button_tree_btn', function (require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	var Model = require('web.Model');
	var session = require('web.session');
	var web_client = require('web.web_client');
	var ajax = require("web.ajax");
	var Dialog = require('web.Dialog');

	var QWeb = core.qweb;
	var _t = core._t;


	/**
	 * ADD NEW BUTTON DEMO
	 */
	function execute_open_action() {
		let delete_data = function () {
				let add_new_button_add = $("#add").val();
				let add_new_button_new = $("#new").val();
				let add_new_button_button = $("#button").val();
				let active_id = $('tr');
				let check_active = new Array();
				for (let i = 0; i < active_id.length; i++) {
					if(active_id[i].getElementsByTagName('input')[0]){
						if(active_id[i].getElementsByTagName('input')[0].checked && active_id.eq(i).attr('data-id')){
							check_active.push(active_id.eq(i).attr('data-id'));
						}
					}
				}
				console.log(check_active);

				let period = $("#period").val();
				new Model('add.new.button').call('confirm_data', [add_new_button_add, add_new_button_new, add_new_button_button, period, check_active]).done(function (result) {
					console.log(result);
					web_client.action_manager.do_action({
						name: "调整工作底稿",
						type: "ir.actions.act_window",
						res_model: "adjust.working.papers.generate.wizard",
						target: 'new',
						xml_id: 'combined_statements.adjust_working_papers_generate_wizard_form',
						views: [[false, 'form']]
					});
					if (result.status) {
						new Dialog.confirm(this, result.message, {
							'title': 'Message'
						});
					}
				});
			};

		new Model("add.new.button").call('get_button_data').then(function (result) {
			if (result) {
				new Dialog(this, {
					title: "TEST NEW BUTTON FUNCTION",
					size: 'medium',
					buttons: [
						{
							text: _t("Save"),
							classes: 'btn-primary',
							close: true,
							click: delete_data
						}, {
							text: _t("Cancel"),
							close: true
						}
					],
					$content: $(QWeb.render('AddNewButtonTemplate', {widget: this, data: result}))
				}).open();
			}
		});
	}

	/**
	 * Extend the render_buttons function of ListView by adding an event listener
	 * on the import button.
	 * @return {jQuery} the rendered buttons
	 */
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
});
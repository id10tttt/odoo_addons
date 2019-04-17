# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)


class AddNewButton(models.Model):
    _name = 'add.new.button'
    _description = 'add new button after create and import button'

    name = fields.Char('Name')
    date = fields.Datetime('Date')

    link_record = fields.Text('Link records')
    button_line = fields.One2many('add.new.button.line', 'button_line')

    def test_rpc_js_method(self, test_code):
        pass

    @api.model
    def get_button_data(self):
        data = {
            'add': 'add',
            'new': 'new',
            'button': 'button'
        }
        _logger.info({'data': data})
        return data

    @api.model
    def confirm_data(self, add, new, button, period, check_active):

        if check_active:
            for x in check_active:
                record = self.env['add.new.button'].browse(int(x.encode('utf-8')))
                print(record)
                record.write({
                    'button_line': [(0, 0, {'name': x.encode('utf-8')})]
                })
            print('check_active {}'.format(check_active))

        return {'status': True, 'message': 'Success add new button after create'}

    @api.multi
    def test_button(self):
        _logger.info({'context': self._context})
        res = self.env['ac.tb'].search([], limit=1)

        return {
            'name': _(u'测试'),
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'ac.tb',
            'type': 'ir.actions.act_window',
            # 'view_id': False,
            'target': 'new',
        }


class AddNewButtonLine(models.Model):
    _name = 'add.new.button.line'

    name = fields.Char('name')
    button_line = fields.Many2one('add.new.button')

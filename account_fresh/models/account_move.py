# -*- coding: utf-8 -*-
import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning
import traceback
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    line_cash_id = fields.One2many('account.move.line.cash.id', 'move_lines_ids')

    @api.constrains('account_id', 'cash_id', 'partner_id', 'line_cash_id')
    def _check_cashid_account(self):
        if self.account_id.user_type_id.id == 3 or self.account_id.user_type_id.type == 'liquidity':
            if not self.line_cash_id:
                if not self.cash_id:
                    raise ValidationError('选择现金及银行 [科目代码：{0}] 时，必须选择现金流量表!'.format(self.account_id.code))
            else:
                for x in self.line_cash_id:
                    if not x.cash_id:
                        raise ValidationError('选择现金及银行 [科目代码：{0}] 时，必须选择现金流量表!'.format(self.account_id.code))
        elif self.account_id.user_type_id.id in self.env['account.account.type'].search([
            ('name', 'in', ['应收', '应付', 'Payable', 'Receivable'])]).ids:
            if not self.partner_id:
                raise ValidationError('选择，应收、应付类型时 [科目代码: {0}]，必须选择合作伙伴'.format(self.account_id.code))
        elif self.account_id.id in self.env['account.account'].search([
            ('code', '>=', 1122),
            ('code', '<', 1124),
            '|',
            ('code', '>=', 1221),
            ('code', '<', 1222),
            '|',
            ('code', '>=', 2202),
            ('code', '<', 2204),
            '|',
            ('code', '>=', 2241),
            ('code', '<', 2242),
        ]).ids:
            if not self.partner_id:
                raise ValidationError('当您选择 [科目: {0}]时，必须选择合作伙伴'.format(self.account_id.code))

        if self.line_cash_id:
            if self.debit != sum(x.cash_debit for x in self.line_cash_id):
                raise ValidationError('{0} 借方和不等于 {1}'.format(self.account_id.display_name, self.debit))

            if self.credit != sum(x.cash_credit for x in self.line_cash_id):
                raise ValidationError('{0} 贷方和不等于 {1}'.format(self.account_id.display_name, self.credit))

    # @api.multi
    # def _compute_name(self):
    #     return self.env['account.move.line'].search([], limit=1, order='write_date desc').name

    @api.multi
    def view_line_cash_id(self):
        if self.account_id.user_type_id.id != 3 or self.account_id.user_type_id.type != 'liquidity':
            raise ValidationError('非现金及银行类型的科目，不允许此操作。')

        view_id = self.env.ref('account.view_move_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    @api.onchange('line_cash_id', 'cash_id')
    def _check_cash_id_account(self):
        if self.line_cash_id:
            self.cash_id = False



class AccountMove(models.Model):
    _inherit = 'account.move'
    _name = 'account.move'

    red_dashed_from = fields.Many2one('account.move', u'原始凭证')
    red_dashed_to = fields.Many2one('account.move', u'红冲凭证')
    red_dashed_state = fields.Boolean('红冲状态', default=False, readonly=True)

    partner_id = fields.Many2many('res.partner', compute='_compute_partner_ids', string="Partner", store=True,
                                 readonly=True)

    @api.multi
    def _red_dashed(self):
        self.ensure_one()
        if self.state != 'posted':
            raise ValidationError('非已过账状态！不可冲销!\n请先过账。')

        for x in self.line_ids:
            if x.account_id.user_type_id.id == 3:
                raise ValidationError('现金银行科目[科目代码：{0} ]不可冲销!'.format(x.account_id.code))

        default = {}
        default.update({'ref': u'冲: ' + (self.ref if self.ref else '')})
        res = super(AccountMove, self).copy(default=default)
        for x in res.line_ids:
            x.debit = -x.debit
            x.credit = -x.credit
        res.red_dashed_from = self.id
        self.red_dashed_state = True
        self.red_dashed_to = res.id

    @api.multi
    @api.depends('line_ids.partner_id')
    def _compute_partner_ids(self):
        for move in self:
            partners = move.line_ids.mapped('partner_id')
            if partners:
                move.partner_id = [i.id for i in partners]

class AccountMoveLineCashID(models.Model):
    _name = 'account.move.line.cash.id'
    _description = u'拆分现金流量表行'

    cash_debit = fields.Float('借方')
    cash_credit = fields.Float('贷方')
    cash_id = fields.Many2one('core.value', '现金流量表行')

    move_lines_ids = fields.Many2one('account.move.line', string=u'日记账项目')

    move_id = fields.Many2one('account.move',
                              realated='move_lines_ids.move_id',
                              string=u'日记账分录',
                              store=True,
                              compute='compute_field'
                              )
    move_period_id = fields.Many2one('account.period', u'期间', store=True, compute='compute_field')

    company_id = fields.Many2one('res.company', u'公司',
                                 compute='compute_field',
                                 default=lambda self: self.env['res.company']._company_default_get())

    @api.depends('cash_debit', 'cash_credit', 'cash_id')
    def compute_field(self):
        for x in self:
            data = {
                'move_id': x.move_lines_ids.move_id.id,
                'move_period_id': x.move_lines_ids.move_id.period_id.id,
                'company_id': x.move_lines_ids.move_id.company_id.id
            }
            x.update(data)
        self.env.cr.commit()

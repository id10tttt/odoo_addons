# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from werkzeug import url_encode
import traceback
from odoo.osv import *
from odoo.exceptions import Warning, UserError
import logging
# _logger = logging.getLogger(__name__)
#
# class HrExpenseRegisterPaymentWizard(models.TransientModel):
#     '''
#     添加现金流量表行，expense_post_payment复写，添加cash_id传入
#     '''
#     _inherit = "hr.expense.register.payment.wizard"
#     _name = 'hr.expense.register.payment.wizard'
#
#     cash_id = fields.Many2one('core.value', string=u'现金流量表', required=True)
#     amount_total_price = fields.Monetary('total_amount')
#     diff_amount = fields.Monetary('diff_amount', compute='_compute_diff_amount', readonly=True, store=True)
#     diff_cash_id = fields.Many2one('core.value', string=u'差异现金流量表')
#
#     @api.multi
#     @api.onchange('amount_total_price', 'amount')
#     def _compute_diff_amount(self):
#         self.diff_amount = self.amount_total_price - self.amount
#
#     @api.multi
#     def expense_post_payment(self):
#         try:
#             self.ensure_one()
#             context = dict(self._context or {})
#             active_ids = context.get('active_ids', [])
#             expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)
#
#             res = self.get_payment_vals()
#             res['amount'] = self.amount_total_price
#             res['cash_id'] = self.cash_id.id
#             # Create payment and post it
#             if self.amount == self.amount_total_price:
#
#                 payment = self.env['account.payment'].create(res)
#                 payment.post()
#
#                 # Log the payment in the chatter
#                 body = (_(
#                     "A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (
#                         payment.amount, payment.currency_id.symbol,
#                         url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
#                 expense_sheet.message_post(body=body)
#
#                 # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
#                 account_move_lines_to_reconcile = self.env['account.move.line']
#
#
#                 for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
#                     if line.account_id.internal_type == 'payable':
#                         account_move_lines_to_reconcile |= line
#                 # DO NOT FORWARD-PORT! ONLY FOR v10
#                 if len(expense_sheet.expense_line_ids) > 1:
#                     return payment.open_payment_matching_screen()
#                 else:
#                     account_move_lines_to_reconcile.reconcile()
#                 return {'type': 'ir.actions.act_window_close'}
#             else:
#                 res_diff = self.get_payment_vals()
#                 res_diff['amount'] = abs(self.amount_total_price - self.amount)
#                 res_diff['cash_id'] = self.diff_cash_id.id
#
#                 payment_ids = []
#                 for data in [res, res_diff]:
#                     payment = self.env['account.payment'].create(data)
#                     payment.post()
#                     payment_ids.append(payment.id)
#                     # Log the payment in the chatter
#                     body = (_(
#                         "A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (
#                                 payment.amount, payment.currency_id.symbol,
#                                 url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name,
#                                 expense_sheet.name))
#                     expense_sheet.message_post(body=body)
#
#                     # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
#                 account_move_lines_to_reconcile = self.env['account.move.line']
#
#                 payment = self.env['account.payment'].search([('id', 'in', payment_ids)])
#                 payment_move_line_ids = []
#                 for x in payment:
#                     for y in x.move_line_ids:
#                         payment_move_line_ids.append(y.id)
#                 pay_m_l = self.env['account.move.line'].search([('id', 'in', payment_move_line_ids)])
#                 for line in pay_m_l + expense_sheet.account_move_id.line_ids:
#                     if line.account_id.internal_type == 'payable':
#                         account_move_lines_to_reconcile |= line
#
#                 # DO NOT FORWARD-PORT! ONLY FOR v10
#                 if len(expense_sheet.expense_line_ids) > 1:
#                     return (x.open_payment_matching_screen() for x in payment)
#                 else:
#                     account_move_lines_to_reconcile.reconcile()
#
#                 return {'type': 'ir.actions.act_window_close'}
#
#         except UserError:
#             raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
#             _logger.warning(traceback.format_exc())
#         except Exception,e:
#             raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
#             _logger.warning(traceback.format_exc())

class HrExpenseRegisterPaymentWizard(models.TransientModel):
    '''
    添加现金流量表行，expense_post_payment复写，添加cash_id传入
    '''
    _inherit = "hr.expense.register.payment.wizard"
    _name = 'hr.expense.register.payment.wizard'

    cash_id = fields.Many2one('core.value', string=u'现金流量表', required=True)
    amount_total_price = fields.Float('total_amount')


    @api.multi
    def expense_post_payment(self):
        try:
            self.ensure_one()
            context = dict(self._context or {})
            active_ids = context.get('active_ids', [])
            expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

            # Create payment and post it
            payment = self.env['account.payment'].create(self.get_payment_vals())

            payment.cash_id = self.cash_id
            payment.post()

            # Log the payment in the chatter
            body = (_(
                "A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (
                    payment.amount, payment.currency_id.symbol,
                    url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
            expense_sheet.message_post(body=body)

            # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
            account_move_lines_to_reconcile = self.env['account.move.line']


            for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
                if line.account_id.internal_type == 'payable':
                    account_move_lines_to_reconcile |= line
            # DO NOT FORWARD-PORT! ONLY FOR v10
            if len(expense_sheet.expense_line_ids) > 1:
                return payment.open_payment_matching_screen()
            else:
                account_move_lines_to_reconcile.reconcile()
            return {'type': 'ir.actions.act_window_close'}
        except UserError:
            raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
            _logger.warning(traceback.format_exc())
        except Exception,e:
            raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
            _logger.warning(traceback.format_exc())

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from werkzeug import url_encode
import traceback
from odoo.osv import *
from odoo.exceptions import Warning, UserError
import logging
_logger = logging.getLogger(__name__)

class HrExpenseRegisterPaymentWizard(models.TransientModel):
    '''
    添加现金流量表行，expense_post_payment复写，添加cash_id传入
    '''
    _inherit = "hr.expense.register.payment.wizard"
    _name = 'hr.expense.register.payment.wizard'

    cash_id = fields.Many2one('core.value', string=u'现金流量表')

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
            # raise osv.except_osv(_("警告!"), _('不能创建其他公司的！'))
            raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
            _logger.warning(traceback.format_exc())
        except Exception,e:
            raise osv.except_osv(_("警告!"), _(traceback.format_exc()))
            _logger.warning(traceback.format_exc())
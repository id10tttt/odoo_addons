# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import traceback
import logging

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.constrains('name', 'account_id')
    def _check_account(self):
        if self.account_id:
            res = self.env['account.account'].search([('parent_id', '=', self.account_id.id)])
            if res:
                raise ValidationError('必须选择末级科目！ [%s %s] 不是末级科目' % (self.account_id.code, self.account_id.name))

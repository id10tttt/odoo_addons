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

    @api.constrains('account_id', 'cash_id')
    def _check_cashid_account(self):
        if self.account_id.user_type_id.id == 3:
            if not self.cash_id:
                raise ValidationError('选择现金及银行 [科目代码：%s] 时，必须选择现金流量表!' % self.account_id.code)
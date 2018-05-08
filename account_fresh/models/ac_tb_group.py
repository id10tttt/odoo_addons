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


class AcTbGroup(models.Model):
    """
    科目余额表
    period,code,account_id,year_init,initial,debit,credit,balance
    """
    _name = 'ac.tb.group'
    _description = u'科目余额表'
    _order = 'period, code'

    period = fields.Char(u'期间')
    code = fields.Char(u'科目编号')
    account_id = fields.Many2one('account.account', u'科目')
    partner_id = fields.Many2one('res.partner', u'往来单位')
    product_id = fields.Many2one('product.product', u'产品')
    year_init = fields.Float(u'年初余额')
    initial = fields.Float(u'期初余额')
    debit = fields.Float(u'本期借方')
    credit = fields.Float(u'本期贷方')
    balance = fields.Float(u'期末余额')
    company_id = fields.Many2one(
        string=u'公司',
        comodel_name='res.company',
    )

    analytic_account_id = fields.Many2one('account.analytic.account')
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

class AccountTax(models.Model):
    '''
    复写compute_all函数，在原有的基础上，计算税的保留位数，是当前公司所设置的货币的小数点位数，但这样存在
    精度问题，如果直接对当前公司的货币保留位数进行修改，会造成金额在保留2位的基础上，在后面添加很多0.所以重写该方法
    主要就是将所有涉及到精度的地方，更改为保留8位，保留8位数，可以解决一分钱的差异问题
    '''
    _inherit = 'account.tax'

    @api.multi
    @api.depends('invoice_id.invoice_line_ids.quantity',
                 'invoice_id.invoice_line_ids.price_unit',
                 'invoice_id.invoice_line_ids')
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """ Returns all information required to apply taxes (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """

        # 1) Flatten the taxes.

        def collect_taxes(self, all_taxes=None):
            # Collect all the taxes recursively ordered by the sequence.
            # Example:
            # group | seq | sub-group |
            # ------------|-----------|
            #       |  1  |           |
            # ------------|-----------|
            #   t   |  2  |  | seq |  |
            #       |     |  |  4  |  |
            #       |     |  |  5  |  |
            #       |     |  |  6  |  |
            #       |     |           |
            # ------------|-----------|
            #       |  3  |           |
            # ------------|-----------|
            # Result: 1-4-5-6-3
            if not all_taxes:
                all_taxes = self.env['account.tax']
            for tax in self.sorted(key=lambda r: r.sequence):
                if tax.amount_type == 'group':
                    all_taxes = collect_taxes(tax.children_tax_ids, all_taxes)
                else:
                    all_taxes += tax
            return all_taxes

        taxes = collect_taxes(self)

        # 2) Avoid dealing with taxes mixing price_include=False && include_base_amount=True
        # with price_include=True

        base_excluded_flag = False  # price_include=False && include_base_amount=True
        included_flag = False  # price_include=True
        for tax in taxes:
            if tax.price_include:
                included_flag = True
            elif tax.include_base_amount:
                base_excluded_flag = True
            if base_excluded_flag and included_flag:
                raise UserError(_(
                    'Unable to mix any taxes being price included with taxes affecting the base amount but not included in price.'))

        # 3) Deal with the rounding methods

        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        prec = currency.decimal_places

        # In some cases, it is necessary to force/prevent the rounding of the tax and the total
        # amounts. For example, in SO/PO line, we don't want to round the price unit at the
        # precision of the currency.
        # The context key 'round' allows to force the standard behavior.
        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5

        # 4) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
        #     tax  |  base  |  amount  |
        # /\ ----------------------------
        # || tax_1 |  XXXX  |          | <- we are looking for that, it's the total_excluded
        # || tax_2 |        |          |
        # || tax_3 |        |          |
        # ||  ...  |   ..   |    ..    |
        #    ----------------------------

        def recompute_base(base_amount, fixed_amount, percent_amount):
            # Recompute the new base amount based on included fixed/percent amount and the current base amount.
            # Example:
            #  tax  |  amount  |
            # ------------------
            # tax_1 |   10%    |
            # tax_2 |   15     |
            # tax_3 |   20%    |
            # ------------------
            # if base_amount = 145, the new base is computed as:
            # (145 - 15) / (1.0 + ((10 + 20) / 100.0)) = 130 / 1.3 = 100
            if fixed_amount == 0.0 and percent_amount == 0.0:
                return base_amount
            # return round((base_amount - fixed_amount) / (1.0 + percent_amount / 100.0), prec)
            return round((base_amount - fixed_amount) / (1.0 + percent_amount / 100.0), 8)

        # base = round(price_unit * quantity, prec)
        base = round(price_unit * quantity, 8)

        # For the computation of move lines, we could have a negative base value.
        # In this case, compute all with positive values and negative them at the end.
        if base < 0:
            base = -base
            sign = -1
        else:
            sign = 1

        # Keep track of the accumulated included fixed/percent amount.
        incl_fixed_amount = incl_percent_amount = 0
        for tax in reversed(taxes):
            if tax.include_base_amount:
                base = recompute_base(base, incl_fixed_amount, incl_percent_amount)
                incl_fixed_amount = incl_percent_amount = 0
            if tax.price_include:
                if tax.amount_type == 'fixed':
                    incl_fixed_amount += tax.amount
                elif tax.amount_type == 'percent':
                    incl_percent_amount += tax.amount
        # Start the computation of accumulated amounts at the total_excluded value.
        total_excluded = total_included = base = recompute_base(base, incl_fixed_amount, incl_percent_amount)

        # 5) Iterate the taxes in the sequence order to fill missing base/amount values.
        #      tax  |  base  |  amount  |
        # ||  ----------------------------
        # ||  tax_1 |   OK   |   XXXX   |
        # ||  tax_2 |  XXXX  |   XXXX   |
        # ||  tax_3 |  XXXX  |   XXXX   |
        # \/  ...  |   ..   |    ..    |
        #     ----------------------------
        taxes_vals = []
        for tax in taxes:
            # Compute the amount of the tax but don't deal with the price_include because it's already
            # took into account on the base amount except for 'division' tax:
            # (tax.amount_type == 'percent' && not tax.price_include)
            # == (tax.amount_type == 'division' && tax.price_include)
            tax_amount = tax.with_context(force_price_include=False)._compute_amount(base, price_unit, quantity,
                                                                                     product, partner)
            if not round_tax:
                # tax_amount = round(tax_amount, prec)
                tax_amount = round(tax_amount, 8)
            else:
                # tax_amount = currency.round(tax_amount)
                tax_amount = round(tax_amount, 8)

            # Suppose:
            # seq | amount | incl | incl_base | base | amount
            # -----------------------------------------------
            #  1  |   10 % |   t  |     t     | 100.0 | 10.0
            # -----------------------------------------------
            # ... the next computation must be done using 100.0 + 10.0 = 110.0 as base but
            # the tax base of this tax will be 100.0.
            tax_base = base
            if tax.include_base_amount:
                base += tax_amount

            # The total_included amount is computed as the sum of total_excluded with all tax_amount
            total_included += tax_amount

            taxes_vals.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': sign * tax_amount,
                'base': sign * tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
            })

        # return {
        #     'taxes': taxes_vals,
        #     'total_excluded': sign * (currency.round(total_excluded) if round_total else total_excluded),
        #     'total_included': sign * (currency.round(total_included) if round_total else total_included),
        #     'base': sign * base,
        # }
        return {
            'taxes': taxes_vals,
            'total_excluded': sign * (total_excluded if round_total else total_excluded),
            'total_included': sign * (total_included if round_total else total_included),
            'base': sign * base,
        }
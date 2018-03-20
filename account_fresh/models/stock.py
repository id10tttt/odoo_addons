# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMoveExternal(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()
        # if self._context.get('purchase') == '85dbdb21fe502c4d7a1e81bca0aa396d':
        #     valuation_amount = self.price_unit
        #
        if self._context.get('force_valuation_amount'):
            # valuation_amount = self._context.get('force_valuation_amount')
            valuation_amount = self.price_unit
        else:
            if self.product_id.cost_method == 'average':
                valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
            else:
                valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount * qty)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            if self.product_id.cost_method == 'standard':
                raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
            return []
        credit_value = debit_value

        if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
            # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
            # account books the real purchase price, while the stock account books the average price. The difference is
            # booked in the dedicated price difference account.
            if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
            # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
            # is made using the original average price to negate the delivery effect.
            if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
                credit_value = debit_value
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': self.picking_id.name,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
            res.append((0, 0, price_diff_line))
        return res


class StockAccountExternal(models.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'




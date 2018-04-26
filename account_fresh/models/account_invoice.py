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

class AccountInvoice(models.Model):
    '''
    添加发票的状态，主要应用在，查看该发票是正常生成的发票，还是由于核销生成的发票
    '''
    _inherit = "account.invoice"
    _name = 'account.invoice'

    # driver_name = fields.Many2one('res.partner', string='司机')
    # pack_man = fields.Many2one('res.partner', string='装卸工')

    state_invoice = fields.Selection([
        ('normal', u'正常发票'),
        ('difference', u'差异发票'),
        ('split', u'拆分发票'),
    ], string=u'状态', index=True, readonly=True, default='normal')

    source_invoice = fields.Many2one('account.invoice',u'源发票单据')

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
                'analytic_tag_ids': analytic_tag_ids,
                'vehicle_id': line.vehicle_id.id
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['vehicle_id'] = line.get('vehicle_id', False)
        return res

    @api.multi
    def action_invoice_open_invoice(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create_invoice()
        return to_open_invoices.invoice_validate()

    @api.multi
    def action_move_create_invoice(self):
        """ Creates invoice related analytics and financial move lines """

        account_move = self.env['account.move']
        # vehicle = self.invoice_line_ids.purchase_id.order_line.vehicle_id.id
        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)
            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = \
                inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total,
                                                                                                            inv.date_invoice)[
                    0]
                res_amount_currency = total_currency
                ctx['date'] = inv.date or inv.date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id,
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]

            line = inv.group_lines(iml, line)


            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)


            for x in line:
                if x[2]['quantity'] < 0:
                    tmp = x[2]['credit']
                    x[2]['credit'] = x[2]['debit']
                    x[2]['debit'] = tmp
                    x[2]['amount_currency'] = -x[2]['amount_currency']

            if self.type == 'out_refund' or self.type == 'in_refund':
                for x in line:
                    tmp = -x[2]['credit']
                    x[2]['credit'] = -x[2]['debit']
                    x[2]['debit'] = tmp
                    x[2]['amount_currency'] = -x[2]['amount_currency']


            date = inv.date or inv.date_invoice

            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }


            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv


            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.multi
    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False),
            'quantity': qty,
            'vehicle_id': line.vehicle_id.id,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

# class AccountInvoiceLine(models.Model):
#     _inherit = "account.invoice.line"
#     _name = 'account.invoice.line'
#
#     price_subtotal = fields.Monetary(string='Amount',
#                      store=True, compute='_compute_price')
#
#     price_difference = fields.Monetary(string=u'差异金额',
#                      store=True, compute='_compute_difference')
#
#     @api.one
#     @api.onchange('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
#                  'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
#                  'invoice_id.date_invoice')
#     def _compute_price(self):
#         """
#         允许发票里面的金额可以修改
#         :return:
#         """
#         if self.price_subtotal > 10000:
#             return
#         currency = self.invoice_id and self.invoice_id.currency_id or None
#         price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
#         taxes = False
#         if self.invoice_line_tax_ids:
#             taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
#                                                           partner=self.invoice_id.partner_id)
#         self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
#         if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
#             price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id.date_invoice).compute(
#                 price_subtotal_signed, self.invoice_id.company_id.currency_id)
#         sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
#         self.price_subtotal_signed = price_subtotal_signed * sign
#
#     @api.onchange('price_difference')
#     def _compute_difference(self):
#         try:
#             print self.price_unit
#             # data = {
#             #     'product_id': r.product_id.id,
#             #     'quantity': r.quantity,
#             #     'price_unit': r.price_difference - r.price_unit,
#             #     'discount': r.discount,
#             #     'account_id': r.product_id.categ_id.property_stock_valuation_account_id.id,
#             #     'company_id': r.company_id.id,
#             #     'name': r.name,
#             #     'invoice_id': r.invoice_id.id
#             # }
#
#             data = {
#                 'product_id': self.product_id.id,
#                 'quantity': self.quantity,
#                 'price_unit': self.price_difference - self.price_unit,
#                 'discount': self.discount,
#                 'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
#                 'company_id': self.company_id.id,
#                 'name': self._name,
#                 'invoice_id': self.invoice_id.id
#             }
#             self.write(data)
#             self.env.cr.commit()
#         except Exception,e:
#             raise Warning(_(traceback.format_exc()))

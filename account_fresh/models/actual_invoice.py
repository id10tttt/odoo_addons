#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import *
import logging
import traceback
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class ActualInvoice(models.Model):
    '''
    真实发票管理：
    新增一个发票的录入界面，和系统的发票界面类似，只是字段有些许差异
    '''
    _name = 'actual.invoice'
    _inherit = 'mail.thread'
    _description = 'Allow user input actual invoice'

    # name = fields.Char('actual invoice', required=True)
    partner_id = fields.Many2one('res.partner', string=u'供应商', change_default=True,
                                 required=True, ondelete='restrict',
                                 track_visibility='always')
    taxpayer_id = fields.Char(string=u'纳税人识别号')
    taxpayer_address_phone = fields.Char(string=u'地址、电话')
    taxpayer_bank_no = fields.Char(string=u'开户行及帐号')

    date_invoice = fields.Date(string=u'账单日期',
                               index=True,
                               help="Keep empty to use the current date", copy=False)
    date_due = fields.Date(string=u'截止日期',
                           index=True, copy=False,
                           help="If you use payment terms, the due date will be computed automatically at the generation "
                                "of accounting entries. The payment term may compute several due dates, for example 50% "
                                "now and 50% in one month, but if you want to force a due date, make sure that the payment "
                                "term is not set on the invoice. If you keep the payment term and the due date empty, it "
                                "means direct payment.")

    company_id = fields.Many2one('res.company', string=u'公司',
                                 ondelete='restrict', change_default=True,
                                 required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.invoice'))


    actual_invoice_line_id = fields.One2many('actual.invoice.line',
                                             'actual_invice_line_ids',
                                             string=u'发票行')

    amount_untaxed = fields.Float(string='Untaxed Amount',
                                     store=True, readonly=True, compute='_compute_amount_money')

    amount_tax = fields.Float(string='Tax',
                                 store=True, readonly=True, compute='_compute_amount_money')
    amount_total = fields.Float(string='Total',
                                   store=True, readonly=True, compute='_compute_amount_money')

    @api.one
    @api.depends('actual_invoice_line_id','actual_invoice_line_id.quantity',
                  'actual_invoice_line_id.discount',
                  'actual_invoice_line_id.price_total',
                  'actual_invoice_line_id.price_unit',
                  'actual_invoice_line_id.contain_tax_price')
    def _compute_amount_money(self):
        try:
            amount_u = amount_ta = amount_t = 0
            for x in self.actual_invoice_line_id:
                amount_u += x.price_unit * x.quantity * (1 - (x.discount or 0.0) / 100.0)
                amount_ta += x.contain_tax_price * (x.tax_id.amount / 100.0) * x.quantity

            self.amount_untaxed = amount_u
            self.amount_tax = amount_ta
            self.amount_total = (amount_u + amount_ta)
        except Exception,e:
            raise Warning(_(traceback.format_exc()))

class ActualInvoiceLine(models.Model):
    '''
    在发票行上面，添加两个按钮，一个核销，一个查看
    核销 cancel_after_verify
    查看 view_after_verify
    验证 verify_valid
    核销 verify_final
    '''
    _name = 'actual.invoice.line'

    product_id = fields.Many2one('product.product', string=u'产品',
                                 ondelete='restrict', required=True)
    name = fields.Text(string=u'说明')

    quantity = fields.Float(string=u'数量', store=True,
                            digits=dp.get_precision('Product Unit of Measure'),
                            required=True, default=1)

    uom_id = fields.Many2one('product.uom', string=u'单位',
                             ondelete='restrict')
    discount = fields.Float(string=u'折扣(%)', digits=dp.get_precision('Discount'),
                            default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    price_total = fields.Float(string=u'不含税小计',
                                  store=True,
                                  readonly=True, compute='_compute_price_total')

    contain_tax_price = fields.Float(string='tax_price', required=True)
    price_unit = fields.Float(string='no_tax_price', compute='_compute_no_tax_price')

    state = fields.Selection([
            ('draft',u'草稿'),
            ('verify', u'已验证'),
            ('finish', u'核销'),
        ], string=u'状态', index=True, readonly=True, default='draft')


    actual_invice_line_ids = fields.Many2one('actual.invoice',
                                             string=u'发票',
                                             ondelete='restrict', index=True)

    actual_verify_line_ids = fields.One2many('actual.invoice.verify', 'actual_verify_ids')



    @api.multi
    @api.onchange('product_id')
    def _apply_uom(self):
        self.uom_id = self.product_id.uom_po_id

    @api.multi
    @api.onchange('contain_tax_price', 'price_unit', 'tax_id')
    def _compute_no_tax_price(self):
        """
        计算不含税单价，当含税单价、不含税单价、税率变化时，自动计算不含税单价
        :return:
        """
        try:
            for x in self:
                tax_rate = x.tax_id.amount / 100.0
                x.price_unit = x.contain_tax_price / (tax_rate + 1.0)
        except Exception, e:
            _logger.warning(traceback.format_exc())

    @api.one
    # @api.onchange('price_unit', 'quantity', 'price_subtotal', 'discount')
    @api.depends('price_unit', 'quantity', 'discount')
    def _compute_price_total(self):
        try:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            # self.price_total = self.price_unit * self.quantity
            self.price_total = price * self.quantity
        except:
            raise Warning(_(traceback.format_exc()))



    def cancel_after_verify(self):
        '''
        使用
            return {
                        'name': _('核销管理'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'actual.invoice.line',
                        'views': [(view_id, 'form')],
                        'view_id': view_id,
                        'target': 'new',
                        'res_id': self.ids[0],
                        'context': action_ctx
                    }
        返回小窗口
        '''
        try:
            action_ctx = dict(self.env.context)
            state_id = []
            product_id = self.product_id.id
            res1 = self.env['account.invoice'].search([('state', '=', 'draft'),('partner_id', '=', self.actual_invice_line_ids.partner_id.id)])
            for r in res1:
                state_id.append(r.id)
            res = self.env['account.invoice.line'].sudo().search([('product_id', '=', product_id),
                                                                  ('invoice_id', 'in', state_id),
                                                                  ('account_id', '!=', self.product_id.categ_id.property_stock_valuation_account_id.id),
                                                                  ('quantity', '>', 0)],
                                                                 order="create_date desc")

            if res:
                for del_data in self.actual_verify_line_ids:
                    del_data.unlink()
                for x in res:
                    data = {
                        'purchase_bill': x.id,
                        'product_note': x.name,
                        'quantity': x.quantity,
                        'actual_verify_ids': self.id
                    }
                    action_ctx.update(data)
                    res = self.actual_verify_line_ids.create(data)
                self.env.cr.commit()
                self.state = 'draft'
                view_id = self.env.ref('account_fresh.view_actual_invoice_verify_form').id
                return {
                    'name': _('核销管理'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'actual.invoice.line',
                    'views': [(view_id, 'form')],
                    'view_id': view_id,
                    'target': 'new',
                    'res_id': self.ids[0],
                    'context': action_ctx
                }
            else:
                raise Warning(_('没有该产品的发票需要核销,请确认!'))
                return {
                    "type": "ir.actions.do_nothing",
                }
        except Exception,e:
            raise Warning(_(traceback.format_exc()))

    def view_after_verify(self):
        view_id = self.env.ref('account_fresh.view_actual_invoice_verify_form').id
        return {
            'name': _('核销管理'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'actual.invoice.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    def verify_valid(self):
        try:
            sum_qty = sum(x.verify_quantity for x in self.actual_verify_line_ids)
            if sum_qty == self.quantity:
                self.state = 'verify'
            else:
                raise Warning(_(u'核销数量不一致'))
            return {
                "type": "ir.actions.do_nothing",
            }
        except Exception,e:
            raise Warning(_(traceback.format_exc()))

    def verify_final(self):
        '''
        核销，生成一张新的发票记录，进行关联
        '''
        try:
            for x in self.actual_verify_line_ids:
                if x.verify_quantity != 0:
                    # 新纪录的数据，数量等于原本的数量减去核销的数量
                    if not x.purchase_bill.asset_category_id:
                        asset_category_id = False
                    else:
                        asset_category_id = x.purchase_bill.asset_category_id.id

                    # 数量相同的时候，不需要拆分发票，只需要创建一条差异金额的发票行
                    if x.purchase_bill.quantity == x.verify_quantity:
                        ids = []
                        for id_tax in x.purchase_bill.invoice_line_tax_ids:
                            ids.append(id_tax.id)

                        data_diff_invoice_line = {
                            'product_id': x.purchase_bill.product_id.id,
                            'name': x.purchase_bill.name,
                            'asset_category_id': asset_category_id,
                            'account_id': x.purchase_bill.product_id.categ_id.property_stock_valuation_account_id.id,
                            'analytic_tag_ids': [x.purchase_bill.analytic_tag_ids.id],
                            # 'quantity': x.quantity - x.verify_quantity,
                            'quantity': x.quantity,
                            'uom_id': x.purchase_bill.uom_id.id,
                            'price_unit': (x.actual_verify_ids.price_unit - x.purchase_bill.price_unit),
                            'discount': x.purchase_bill.discount,
                            'vehicle_id': x.purchase_bill.vehicle_id.id,
                            'invoice_id': x.purchase_bill.invoice_id.id,
                        }
                        if ids:
                            data_diff_invoice_line['invoice_line_tax_ids'] = [(4, ids)]
                        else:
                            data_diff_invoice_line['invoice_line_tax_ids'] = ''
                        self.env['account.invoice.line'].sudo().create(data_diff_invoice_line)

                        x.purchase_bill.invoice_id._onchange_invoice_line_ids()

                        # link exist record
                        x.cav_sys_invoice = x.purchase_bill.invoice_id.id

                    if x.purchase_bill.quantity != x.verify_quantity:
                        # 创建发票
                        data_invoice = {
                            'partner_id': x.purchase_bill.invoice_id.partner_id.id,
                            'origin': x.purchase_bill.invoice_id.origin,
                            'journal_id': x.purchase_bill.invoice_id.journal_id.id,
                            'user_id': x.purchase_bill.invoice_id.user_id.id,
                            'account_id': x.purchase_bill.invoice_id.account_id.id,
                            'company_id': x.purchase_bill.invoice_id.company_id.id,
                            'type': 'in_invoice',
                            'date': False,
                            'date_due': False,
                            'state_invoice': 'split',
                            'source_invoice': x.purchase_bill.invoice_id.id
                        }
                        res = self.env['account.invoice'].sudo().create(data_invoice)
                        _logger.info('create account invoice success!\n创建发票成功!')

                        # link new record
                        x.cav_sys_invoice = res.id
                        # 税金
                        ids = []
                        for id_tax in x.purchase_bill.invoice_line_tax_ids:
                            ids.append(id_tax.id)

                        # 发票行

                        data_invoice_line = {
                            'product_id': x.purchase_bill.product_id.id,
                            'name': x.purchase_bill.name,
                            'asset_category_id': asset_category_id,
                            'account_id': x.purchase_bill.account_id.id,
                            'analytic_tag_ids': [x.purchase_bill.analytic_tag_ids.id],
                            # 'quantity': x.quantity - x.verify_quantity,
                            'quantity': x.verify_quantity,
                            'uom_id': x.purchase_bill.uom_id.id,
                            'price_unit': x.purchase_bill.price_unit,
                            'discount': x.purchase_bill.discount,
                            'vehicle_id': x.purchase_bill.vehicle_id.id,
                            'invoice_id': res.id,
                        }

                        data_diff_invoice_line = {
                            'product_id': x.purchase_bill.product_id.id,
                            'name': x.purchase_bill.name,
                            'asset_category_id': asset_category_id,
                            'account_id': x.purchase_bill.product_id.categ_id.property_stock_valuation_account_id.id,
                            'analytic_tag_ids': [x.purchase_bill.analytic_tag_ids.id],
                            # 'quantity': x.quantity - x.verify_quantity,
                            'quantity': x.verify_quantity,
                            'uom_id': x.purchase_bill.uom_id.id,
                            'price_unit': (x.actual_verify_ids.price_unit - x.purchase_bill.price_unit),
                            'invoice_line_tax_ids': [(4, ids)],
                            'discount': x.purchase_bill.discount,
                            'vehicle_id': x.purchase_bill.vehicle_id.id,
                            # 'invoice_id': x.purchase_bill.invoice_id.id,
                            'invoice_id': res.id,
                        }
                        if ids:
                            data_invoice_line['invoice_line_tax_ids'] = [(4,ids)]
                            data_diff_invoice_line['invoice_line_tax_ids'] = [(4,ids)]
                        else:
                            data_invoice_line['invoice_line_tax_ids'] = False
                            data_diff_invoice_line['invoice_line_tax_ids'] = False

                        # 更新当前发票的数量
                        # x.purchase_bill.update({'quantity': x.verify_quantity})
                        x.purchase_bill.update({'quantity': (x.quantity - x.verify_quantity)})

                        self.env['account.invoice.line'].sudo().create(data_diff_invoice_line)

                        # x.purchase_bill.invoice_id.tax_line_ids.update({'amount': sum_price})
                        x.purchase_bill.invoice_id._onchange_invoice_line_ids()




                        # if len(x.purchase_bill.invoice_id.invoice_line_ids) == 1:
                        #     x.purchase_bill.invoice_id.action_invoice_open_invoice()

                        _logger.info('update account invoice quantity success!\n更新发票行数量成功')
                        # res = x.purchase_bill.create(data)

                        # 创建一条新的发票行记录
                        res = self.env['account.invoice.line'].sudo().create(data_invoice_line)
                        res.invoice_id._onchange_invoice_line_ids()
                        for tax_id in x.purchase_bill.invoice_line_tax_ids:
                            tax_id.compute_all(x.purchase_bill.price_unit)

                        _logger.info('create account invoice line success!\n创建发票行成功')

            self.env.cr.commit()
            self.state = 'finish'
            return {
                "type": "ir.actions.do_nothing",
            }
        except Exception,e:
            raise Warning(_(traceback.format_exc()))

    def cancel_verify(self):
        '''
        取消发票核销
        使用
            return {
                    "type": "ir.actions.do_nothing",
                }
        可以解决当点击按钮的时候，窗口自动关闭的问题
        '''
        try:
            for x in self.actual_verify_line_ids:
                if x.cav_sys_invoice:
                    if x.cav_sys_invoice.state == 'open' or x.cav_sys_invoice.state == 'paid':
                        x.cav_sys_invoice.action_invoice_cancel()
                    if x.cav_sys_invoice.state == 'cancel':
                        x.cav_sys_invoice.action_invoice_draft()
                    for inv_id in x.cav_sys_invoice.invoice_line_ids:
                        if inv_id.account_id.id == inv_id.product_id.categ_id.property_stock_valuation_account_id.id:
                            inv_id.unlink()
                            _logger.info(('delete account invoice line (%s) success! 删除发票行成功') % (inv_id))
                # 删除核销行
                x.unlink()
                # self.verify_quantity = 0
                # x.cav_sys_invoice = None

            self.state = 'draft'

            return {
                "type": "ir.actions.do_nothing",
            }
        except Exception,e:
            raise Warning(_(traceback.format_exc()))

class Vertify(models.Model):
    '''
    需要核销的产品，原有的数量和需要核销的数量
    '''
    _name = 'actual.invoice.verify'

    purchase_bill = fields.Many2one('account.invoice.line', ondelete='restrict', readonly=True)
    product_note = fields.Char(string=u'产品说明', readonly=True)
    quantity = fields.Float(u'数量', readonly=True)
    verify_quantity = fields.Float(u'核销数量')

    actual_verify_ids = fields.Many2one('actual.invoice.line',string=u'核销ID',ondelete='restrict', index=True)

    cav_sys_invoice = fields.Many2one('account.invoice', 'cav_sys_invoice')

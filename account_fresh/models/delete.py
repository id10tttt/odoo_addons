#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import *
import logging
import traceback
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class DeleteData(models.Model):
    _name = 'delete.data'

    delete_name = fields.Char('delete_name', help='要删除的订单')
    delete_type = fields.Selection([('sale', u'销售'),
                                    ('purchase', u'采购')])

    state = fields.Selection([
            ('draft',u'未删除'),
            ('finish', u'已删除'),
        ], string=u'状态', index=True, readonly=True, default='draft')

    def delete_data(self):
        try:
            res = self.env['account.invoice'].search([('origin', '=', self.delete_name)])
            origins = []
            account_invoice = ()
            account_invoice_line = ()
            for x in res:
                origins.append(x.origin)
                for y in x.invoice_line_ids:
                    account_invoice_line = account_invoice_line + (y.id,)
                    # account_invoice_line.append(y.id)
                # account_invoice.append(x.id)
                account_invoice = account_invoice + (x.id,)

            res_mode = ''
            table_order = ''
            if self.delete_type == 'sale':
                res_mode = 'sale.order'
                table_order = 'sale_order'
            elif self.delete_type == 'purchase':
                res_mode = 'purchase.order'
                table_order = 'purchase_order'

            res1 = self.env[res_mode].search([('name', '=', self.delete_name)])
            order_line = ()
            ps_order = ()
            for x in res1:
                for y in x.order_line:
                    order_line = order_line + (y.id,)
                    ps_order = ps_order + (x.id,)
                    # order_line.append(y.id)
                    # ps_order.append(x.id)

            res = self.env['stock.picking'].search([('origin', '=', self.delete_name)])
            quant_ids = ()
            stock_pack_ids = ()
            stock_move_ids = ()
            stock_picking_ids = ()
            for x in res:
                for y in x.move_lines:
                    for z in y.quant_ids:
                        quant_ids = quant_ids + (z.id,)
                        # quant_ids.append(z.id)
                    # stock_move_ids.append(y.id)
                    stock_move_ids = stock_move_ids + (y.id,)
                for a in x.pack_operation_ids:
                    # stock_pack_ids.append(a.id)
                    stock_pack_ids = stock_pack_ids + (a.id,)
                # stock_picking_ids.append(x.id)
                stock_picking_ids = stock_picking_ids + (x.id,)

            # print 'quant_ids:', quant_ids
            # print 'stock_pack_ids:', stock_pack_ids
            # print 'stock_move_ids:', stock_move_ids
            # print 'stock_picking_ids:', stock_picking_ids
            # print 'purchase_order_line:', order_line
            # print 'purchase_order:', ps_order
            # print 'account_invoice_line:', account_invoice_line
            # print 'account_invoice:', account_invoice, '\n\n\n'
            ctx = {
                'delete_name': self.delete_name,
                'delete_type': self.delete_type
            }


            if quant_ids:
                sql_quant = """delete from stock_quant where id in %s ;""" % \
                            (quant_ids if len(quant_ids) > 1 else '(' + str(quant_ids[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_quant)
                _logger.info('删除库存数量移动成功! %s' % self.env.user.name)


            if stock_pack_ids:
                sql_stock_pack = """delete from stock_pack_operation where id in %s ;""" % \
                                 (stock_pack_ids if len(stock_picking_ids) > 1 else '(' + str(stock_picking_ids[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_stock_pack)
                _logger.info('删除库存操作成功! %s' % self.env.user.name)

            if stock_move_ids:
                sql_stock_move = """delete from stock_move where id in %s ;""" % \
                                 (stock_move_ids if len(stock_move_ids) > 1 else '(' + str(stock_move_ids[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_stock_move)
                _logger.info('删除库存移动成功! %s' % self.env.user.name)

            if stock_picking_ids:
                sql_stock_picking = """delete from stock_picking where id in %s ;""" % \
                                    (stock_picking_ids if len(stock_picking_ids) > 1 else '(' + str(stock_picking_ids[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_stock_picking)
                _logger.info('删除库存成功! %s' % self.env.user.name)

            if order_line:
                sql_order_line = """delete from %s_line where id in %s ;""" %\
                                 (table_order, (order_line if len(order_line) > 1 else  '(' + str(order_line[0]) + ')'))
                self.env.invalidate_all()
                self.env.cr.execute(sql_order_line)
                _logger.info('删除订单行成功! %s' % self.env.user.name)

            if ps_order:
                sql_order = """delete from %s where id in %s ;""" % \
                            (table_order, (ps_order if len(ps_order) > 1 else '(' + str(ps_order[0]) + ')'))
                self.env.invalidate_all()
                self.env.cr.execute(sql_order)
                _logger.info('删除订单成功! %s' % self.env.user.name)


            if account_invoice_line:
                sql_invoice_line = """delete from account_invoice_line where id in %s ;""" % \
                            (account_invoice_line if len(account_invoice_line) > 1 else '(' + str(account_invoice_line[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_invoice_line)
                _logger.info('删除发票行成功! %s' % self.env.user.name)
 
            if account_invoice:
                sql_invoice = """delete from account_invoice where id in %s ;""" % \
                              (account_invoice if len(account_invoice) > 1 else '(' + str(account_invoice[0]) + ')')
                self.env.invalidate_all()
                self.env.cr.execute(sql_invoice)
                _logger.info('删除发票成功! %s' % self.env.user.name)

            self.create(ctx)
            self.state = 'finish'
            return {
                "type": "ir.actions.do_nothing",
            }
        except Exception,e:
            raise Warning(traceback.format_exc())

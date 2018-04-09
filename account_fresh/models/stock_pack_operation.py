# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import traceback
from odoo.exceptions import Warning

class StockPackOperationLotExternal(models.Model):
    '''
    在使用条码枪扫描的时候，当公司里面设置的允许确认所有数量，即可在点击的时候出现全部按钮

    '''
    _inherit = 'stock.pack.operation.lot'
    _name = 'stock.pack.operation.lot'

    # qty = fields.Float('Done',
    #                    default=1.0,
    #                    digits=dp.get_precision('Product Unit of Measure'),
    #                    # compute='_compute_finish_qty',
    #                    readonly=False,
    #                    store=True)

    state_allow = fields.Boolean('state', compute='_compute_state_visible', default=False)

    @api.one
    def _compute_state_visible(self):
        # if self.operation_id.product_id.tracking == 'serial':
        for x in self:
            x.state_allow = self.env.user.company_id.allow_confirm_qty
        return self.state_allow

    @api.multi
    def do_allcount(self):
        if self.env.user.company_id.allow_confirm_qty:
            for lot in self:
                if lot.qty_todo > 0:
                    lot.qty = lot.qty_todo
                    lot.operation_id.qty_done = sum(operation_lot.qty for operation_lot in lot.operation_id.pack_lot_ids)
                else:
                    lot.qty = lot.operation_id.product_qty
                    lot.operation_id.qty_done = sum(
                        operation_lot.qty for operation_lot in lot.operation_id.pack_lot_ids)
            return self.mapped('operation_id').action_split_lots()
        else:
            raise Warning(_('您不被允许全选，请联系您的管理员！'))
            return self.mapped('operation_id').action_split_lots()

    # def _compute_finish_qty(self):
    #     try:
    #         print self.sudo().qty, '**********'
    #         if self.env.user.company_id.allow_confirm_qty:
    #             for x in self:
    #                 if x.qty_todo > 0:
    #                     x.qty = x.qty_todo
    #                     #
    #                     # if x.qty == 0:
    #                     #     x.qty = x.qty_todo
    #                 else:
    #                     print '.....\n\n\n...'
    #                     pass
    #     except Exception, e:
    #         raise Warning(_(traceback.format_exc()))
    if __name__ == '__main__':
        _compute_state_visible()

class StockPackOperationLotExternal(models.Model):
    '''
    在使用条码枪扫描的时候，当公司里面设置的允许确认所有数量，即可在点击的时候出现全部按钮

    '''
    _inherit = 'stock.pack.operation'
    _name = 'stock.pack.operation'

    # qty = fields.Float('Done',
    #                    default=1.0,
    #                    digits=dp.get_precision('Product Unit of Measure'),
    #                    # compute='_compute_finish_qty',
    #                    readonly=False,
    #                    store=True)

    state_allow = fields.Boolean('state', compute='_compute_state_visible', default=False)

    @api.one
    def _compute_state_visible(self):
        # if self.operation_id.product_id.tracking == 'serial':
        for x in self:
            x.state_allow = self.env.user.company_id.allow_confirm_qty
        return self.state_allow

    @api.multi
    def do_allcount(self):
        if self.env.user.company_id.allow_confirm_qty:
            for lot in self:
                if lot.qty_done > 0:
                    lot.qty_done = lot.product_qty
                else:
                    lot.qty_done = lot.product_qty
        else:
            raise Warning(_('您不被允许全选，请联系您的管理员！'))

    if __name__ == '__main__':
        _compute_state_visible()

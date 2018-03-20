# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    '''
    添加时候允许在仓库里面扫描操作时，可以将数量，在点击的时候补全!
    '''
    _inherit = 'res.company'

    allow_confirm_qty = fields.Boolean(string='allow confirm all',
                                       help='allow this company\'s user to comfirm the qty.')
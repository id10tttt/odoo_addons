# -*- coding: utf-8 -*-

import time
import xlwt
from odoo import http
from odoo.http import request
from xlwt import Workbook
import json

try:
    import StringIO
except ImportError:
    from io import StringIO


book = Workbook(encoding='utf-8')


class CustomerExport(http.Controller):
    @http.route(['/report/odoo_demo.customer_export'], type='http', auth='user', multilang=True)
    def customer_export(self, **data):
        # 用传过来的期间取得报表数据
        # data = json.loads(data)
        # print 'data', data
        res = request.env['account.move.line'].search([])
        data = res.read()
        worksheet = book.add_sheet('Account Balances')
        # 将发送的数据流
        xls = StringIO.StringIO()

        index = True
        for i, j in enumerate(data):
            for x, y in enumerate(j.keys()):
                if i == 0:
                    worksheet.write(i, x, y)
                else:
                    worksheet.write(i, x, str(j.get(y)))
        book.save(xls)

        # 返回给用户
        xls.seek(0)
        content = xls.read()
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', 'attachment; filename=%s%s_account_balance.xlsx;' % ('2019', '01'))
        ])

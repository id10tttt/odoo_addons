# -*- encoding: utf-8 -*-
{
    'name': "Wechat bill",
    'version': '12.0.0',
    'summary': 'Wechat bill',
    'description': """Wechat bill""",
    'author': '1di0t',
    "depends": ['base', 'product'],
    'data': [
        # 'views/assets.xml',
        'security/ir.model.access.csv',
        'views/wechat_bill.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
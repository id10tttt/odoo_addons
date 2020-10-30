# -*- encoding: utf-8 -*-
{
    'name': "Wechat bill",
    'version': '14.0.0',
    'summary': 'Wechat bill',
    'description': """Wechat bill""",
    'author': '1di0t',
    "depends": ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/wechat_bill.xml',
        'views/menu.xml',
        'views/assets.xml',
    ],
    'qweb': [
        "static/src/xml/wechat_bill_dashboard.xml"
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

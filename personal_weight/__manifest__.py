# -*- encoding: utf-8 -*-
{
    'name': "Weight manage",
    'version': '12.0.0',
    'summary': 'Weight manage',
    'description': """Weight manage""",
    'author': '1di0t',
    "depends": ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/personal_weight_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
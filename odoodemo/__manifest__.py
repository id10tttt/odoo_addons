# -*- coding: utf-8 -*-
{
    'name': 'odoo_demo',
    'summary': 'odoo_demo',
    'version': '1.0',

    'description': 'odoo_demo',

    'author': '1di0t',
    'maintainer': 'dgqcjx@gmail.com',

    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/base.xml',
        'views/menu.xml',
        'views/add_new_button.xml'
    ],
    'qweb': ['static/xml/*.xml'],
}

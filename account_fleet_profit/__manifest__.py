{
    'name': 'fleet vehicle profit',
    'description': 'fleet vehicle profit',
    'author': '1di0t',
    'depends': ['base',
                'fleet',
                'account_period'],
    'application': True,
    'data': [
        'views/fleet_profit.xml',
        'wizard/fleet_profit_cal.xml',
        'security/ir.model.access.csv',
    ],
}

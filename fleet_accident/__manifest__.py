{
    'name': 'fleet accident',
    'description': 'fleet accident',
    'author': '1di0t',
    'depends': ['base',
                'fleet',
                'account'],
    'application': True,
    'data': [
        'security/fleet_security.xml',
        'views/fleet_accident.xml',
        'security/ir.model.access.csv',
    ],
}

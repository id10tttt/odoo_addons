{
    'name': "CRM Dashboard Echarts",

    'summary': """
        CRM Dashboard Echarts""",

    'description': """
        CRM Dashboard Echarts
    """,

    'author': "1di0t",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'web', 'crm_metrics'],

    'data': [
        'views/menu.xml',
        'views/assets.xml',
    ],
    'qweb': [
        "static/src/xml/dashboard_echarts.xml"
    ],
}

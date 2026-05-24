# -*- coding: utf-8 -*-

{
    'name': 'Union Energy Calculator',
    'summary': 'Union Energy Calculator',
    'category': 'Union Energy',
    'author': 'BatamTech',
    'sequence': 10,
    'version': '1.2',
    'description': "This module allows to publish the Union Energy calculator.",
    'depends': ['website', 'crm'],
    'data': [
        'security/calculator_security.xml',
        'security/ir.model.access.csv',
        'data/calculator_data.xml',
        'data/crm_tag_data.xml',
        'views/calculator_setting_view.xml',
        'views/calculator_enquiry_view.xml',
        'views/crm_lead_views.xml',
        'menus/calculator_menu.xml',
        'websites/calculator_web.xml',
        'websites/calculator_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_frontend': [
            'union_energy_calculator/static/src/css/calculator.css',
            'union_energy_calculator/static/src/js/calculator.js',
        ],
    },
    'license': 'LGPL-3',
}

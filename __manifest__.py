# -*- coding: utf-8 -*-

{
    'name': 'Union Energy Calculator',
    'summary': 'Union Energy Calculator',
    'category': 'Union Energy',
    'author': 'BatamTech',
    'sequence': 10,
    'version': '1.3.17',
    'description': "This module allows to publish the Union Energy calculator.",
    'depends': ['web', 'website', 'crm', 'website_crm', 'union_energy_web'],
    'data': [
        'security/calculator_security.xml',
        'security/ir.model.access.csv',
        'data/calculator_data.xml',
        'data/crm_tag_data.xml',
        'data/crm_tag_contactus_data.xml',
        'data/calculator_menu.xml',
        'data/calculator_menu_sync.xml',
        'data/calculator_website.xml',
        'views/calculator_setting_view.xml',
        'views/calculator_enquiry_view.xml',
        'views/crm_lead_views.xml',
        'menus/calculator_menu.xml',
        'websites/calculator_web.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_frontend': [
            'union_energy_calculator/static/src/scss/calculator.scss',
            'union_energy_calculator/static/src/js/calculator.js',
        ],
    },
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}

# -*- coding: utf-8 -*-
{
    'name': "Microfinancing - Accounts",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Cuburt R. Balanon",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['credit_base', 'account', 'sale', 'sale_crm', 'om_account_accountant', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/template.xml',
        'data/accounts.xml',
        'data/banks.xml',
        'data/payment_terms.xml',
        'data/journals.xml',
        'data/products.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
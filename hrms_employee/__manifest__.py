# -*- coding: utf-8 -*-
{
    'name': "HRMS EMPLOYEE",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MSG-MIS",
    'website': "http://www.mutigroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hrms_base','hr_contract','hr_public_holidays','ph_localization', 'report_xlsx'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        # 'data/hr_recruitment_data.xml',
        'views/hr_contract_view.xml',
        'views/hr_recruitment_view.xml',
        'views/hr_view.xml',
        'views/res_views.xml',
        'views/hr_holiday_policy.xml',
        'views/res_bank_views.xml',
        'data/hr_contract_sequence.xml',
        'data/ir_cron_data.xml',
        'data/res_users_data.xml',
        'report/employee_list_report_view.xml',
        'report/report_recruitment_views.xml',
        'report/report_resource_plan_views.xml',
        'report/report_recruitment_agreement_views.xml',
        'report/report_contract_views.xml',
        'report/gift_check_view.xml',
        'report/employee_headcount_views.xml',
        'report/personnel_action_form_views.xml',
        'report/non_disclosure_agreement_views.xml',
        'report/probationary_employment_contract_views.xml',
        'report/memorandum_agreement_views.xml',
        'report/man_power_plan_views.xml',
        'report/template/report_contract.xml',
        'report/template/report_hr_employee_template.xml',
        'report/template/report_hr_employee_headcount_template.xml',
        'report/template/report_regularization_template.xml',
        'report/template/report_contract_template.xml',
        'report/template/report_my_paf_template.xml',
        'report/template/report_non_disclosure_template.xml',
        'report/template/report_probationary_employment_template.xml',
        'report/template/report_memorandum_agreement_template.xml',
        'report/template/insurance_waiver_template.xml',
        'report/template/report_employee_profile_template.xml',
        'report/template/report_check_template.xml',
        'report/template/hrms_employee_report_layout.xml',
        'report/template/report_monthly_contract_template.xml',
        'report/template/hr_recruitment_layout.xml',
        'report/template/report_recruitment_template.xml',
        'report/template/report_resource_template.xml',
        'report/template/report_recruitment_agreement_template.xml',
        'report/template/personnel_requisition_form_template.xml',
        'report/template/report_man_power_template.xml',
        'report/template/all_hrms_employee_report.xml',
        'security/hr_employee_multicompany.xml',
        'wizard/hr_contract_employee_views.xml',
        'wizard/employee_transfer_views.xml',
        # 'data/ir_cron_data.xml',

    ],
    # only loaded in demonstration mode-
    'installable': True,
    'application': True,
}
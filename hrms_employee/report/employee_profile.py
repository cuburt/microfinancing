from odoo import api, models


class EmployeeProfileReport(models.AbstractModel):
    _name = 'report.hrms_employee.dev_emp_profile_report_template'

    def get_cat_id(self, tag_id):
        tages = ''
        if tag_id:
            for tage in tag_id:
                tages += tage.name + ','
        return tages

    @api.model
    def render_html(self, docids, data=None):
        hr_employee = self.env['hr.employee'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': hr_employee,
            'data': data,
            'get_cat_id': self.get_cat_id,
        }
        return self.env['report'].render('hrms_employee.dev_emp_profile_report_template', docargs)
from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
import calendar
from dateutil.relativedelta import relativedelta


class PersonnelActionFormHandler(models.TransientModel):
    _name = 'hr.contract.handler'

    from_date = fields.Date(string="Start Date", required=False,
                            default=date(date.today().year, date.today().month, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, date.today().month,
                                                                          calendar.monthrange(date.today().year,
                                                                                              date.today().month)[1]))
    job_ids = fields.Many2many(comodel_name="hr.job", string="Employee", required=False)
    branch_ids = fields.Many2many(comodel_name="hr.department", string="Branch")
    department_ids = fields.Many2many(comodel_name="hr.department", string="Department")
    company_ids = fields.Many2many(comodel_name="res.company", string="Company", )
    filters = fields.Selection(selection=[('company', 'By Company'),
                                          ('department', 'By Department'),
                                          ('branch', 'By Branch'),
                                          ('job', 'By Job Title')], string='Filter By', default='company')
    contract_comparison = fields.Boolean(string="Contract Comparison")
    employment_type = fields.Selection(string="Employment Type",
                                       selection=[('initial', 'Initial Hire'),
                                                  ('confirm', 'Confirmation of Regular Employment'),
                                                  ('rehire', 'Re-Hire'),
                                                  ('promote', 'Promotion'),
                                                  ('position', 'Change in Position'),
                                                  ('separate', 'Separation'),
                                                  ('others', 'Others')], required=True, default='confirm')
    user_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False,
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))

    @api.multi
    def get_approvers_name(self, values):
        if values:
            employee = self.env['hr.employee'].browse(values)
            if employee:
                last_name = employee.last_name
                first_name = employee.first_name
                if employee.middle_name:
                    middle_name = employee.middle_name[:1]
                else:
                    middle_name = ''
                name = '%s %s. %s' % (first_name, middle_name, last_name)
                return name

    @api.multi
    def get_sorted(self, list):
        if list:
            result = sorted(list, key=lambda x: x.name)
            print result
            return result

    @api.onchange('from_date', 'to_date')
    def get_validation_date(self):
        if self.from_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))
        if self.to_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))

    @api.multi
    def print_contract_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['employment_type', 'company_ids', 'department_ids', 'job_ids', 'branch_ids',
                                  'from_date', 'to_date', 'filters', 'user_id', 'contract_comparison'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_monthly_contract_template', data=data)


# PDF FILE REPORT
class PersonnelActionFormReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_monthly_contract_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        company = data['form']['company_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        filters = data['form']['filters']
        employment_type = data['form']['employment_type']
        department = data['form']['department_ids']
        branch = data['form']['branch_ids']
        job = data['form']['job_ids']

        if from_date and to_date and employment_type and filters == 'company' and not company:
            c1 = []
            for companies in self.env['res.company'].search([]):
                c1.append(companies.id)
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('company_id', 'in', c1)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'department' and not department:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('department_id.is_branch', '=', False)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'branch' and not branch:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('department_id.is_branch', '=', True)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'job' and not job:
            j1 = []
            for jobs in self.env['hr.job'].search([]):
                j1.append(jobs.id)
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('job_id', 'in', j1)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'company' and company:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('company_id', 'in', company)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'department' and department:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('department_id', 'in', department)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'branch' and branch:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('department_id', 'in', branch)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        if from_date and to_date and employment_type and filters == 'job' and job:
            records = self.env['hr.contract.partial'].search([('date_start', '>=', from_date), ('date_start', '<=', to_date),
                                                      ('employment_type', '=', employment_type),
                                                      ('job_id', 'in', job)])
            if records:
                records
            else:
                raise ValidationError(_('No Records Found!'))

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'records': records

        }

        return self.env['report'].render('hrms_employee.report_monthly_contract_template', docargs)

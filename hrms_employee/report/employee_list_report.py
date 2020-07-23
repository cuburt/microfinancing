from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import calendar


class HrEmployeeMonthlyReport(models.TransientModel):
    _name = 'hr.employee.list.handler'

    from_date = fields.Date(string="Start Date", required=False,
                            default=date(date.today().year, date.today().month, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, date.today().month,
                                                                          calendar.monthrange(date.today().year,
                                                                                              date.today().month)[1]))
    company_ids = fields.Many2many('res.company', string="Company")
    branch_ids = fields.Many2many('hr.department', string="Branch")
    department_ids = fields.Many2many('hr.department', string="Department")
    state = fields.Selection(string="Employment Status", selection=[('joined', 'New Employee'),
                                                                    ('probationary', 'Probationary'),
                                                                    ('employment', 'Regular'),
                                                                    ('relieved', 'Resigned'),
                                                                    ('terminate', 'Terminated')], default='employment')
    hiring_filter = fields.Selection(string="Hiring Date", selection=[('actual', 'Date of Joining'),
                                                                      ('payroll', 'Payroll Hiring Date'),
                                                                      ('regular', 'Date of Regularization'),
                                                                      ('separate', 'Date of Separation')],
                                     required=True, default='actual')
    filters = fields.Selection([('by_company', 'By Company'),
                                   ('by_dept', 'By Department'),
                                   ('by_branch', 'By Branch')], string='Filter By')
    user_id = fields.Many2one(comodel_name="hr.employee", string="User(s)", required=False,
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
            return result

    @api.onchange('state')
    def _onchange_state(self):
        if self.state:
            if self.state in ('joined', 'probationary'):
                self.hiring_filter = 'actual'
            if self.state == 'employment':
                self.hiring_filter = 'regular'
            if self.state in ('relieved', 'terminate'):
                self.hiring_filter = 'separate'

    @api.onchange('from_date', 'to_date')
    def get_validation_date(self):
        if self.from_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))
        if self.to_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))

    @api.multi
    def print_emp_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_ids', 'from_date', 'state', 'branch_ids', 'department_ids',
                                  'to_date', 'filters', 'hiring_filter', 'user_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_hr_employee_template', data=data)


# PDF FILE REPORT
class HRMSEmployeeListReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_hr_employee_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        company = data['form']['company_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        filters = data['form']['filters']
        hiring_filter = data['form']['hiring_filter']
        state = data['form']['state']
        department = data['form']['department_ids']
        branch = data['form']['branch_ids']

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/ DATE
        if from_date and to_date and hiring_filter == 'actual':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and company and filters == 'by_company' and hiring_filter == 'actual':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and hiring_filter == 'actual':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and hiring_filter == 'actual':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/O DATE
        if hiring_filter == 'actual' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if company and filters == 'by_company' and hiring_filter == 'actual' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and hiring_filter == 'actual' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and hiring_filter == 'actual' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND PAYROLL HIRING DATE W/ DATE
        if from_date and to_date and hiring_filter == 'payroll':
            records = self.env['hr.employee'].search([('pyrl_date_hired', '>=', from_date),
                                                      ('pyrl_date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and company and filters == 'by_company' and hiring_filter == 'payroll':
            records = self.env['hr.employee'].search([('pyrl_date_hired', '>=', from_date),
                                                      ('pyrl_date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and branch and filters == 'by_branch' and hiring_filter == 'payroll':
            records = self.env['hr.employee'].search([('pyrl_date_hired', '>=', from_date),
                                                      ('pyrl_date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and hiring_filter == 'payroll':
            records = self.env['hr.employee'].search([('pyrl_date_hired', '>=', from_date),
                                                      ('pyrl_date_hired', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND PAYROLL HIRING DATE W/O DATE
        if hiring_filter == 'payroll' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('pyrl_date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if company and filters == 'by_company' and hiring_filter == 'payroll' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('pyrl_date_hired', '<=', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and hiring_filter == 'payroll' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('pyrl_date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                print records
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and hiring_filter == 'payroll' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('pyrl_date_hired', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND REGULAR DATE W/ DATE
        if from_date and to_date and hiring_filter == 'regular':
            records = self.env['hr.employee'].search([('date_regularized', '>=', from_date),
                                                      ('date_regularized', '<=', to_date),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and company and filters == 'by_company' and hiring_filter == 'regular':
            records = self.env['hr.employee'].search([('date_regularized', '>=', from_date),
                                                      ('date_regularized', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and branch and filters == 'by_branch' and hiring_filter == 'regular':
            records = self.env['hr.employee'].search([('date_regularized', '>=', from_date),
                                                      ('date_regularized', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and hiring_filter == 'regular':
            records = self.env['hr.employee'].search([('date_regularized', '>=', from_date),
                                                      ('date_regularized', '<=', to_date),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND REGULARIZATION DATE W/O DATE
        if hiring_filter == 'regular' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_regularized', '<=', date.today()),
                                                      ('date_separated', '>', date.today()),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if company and filters == 'by_company' and hiring_filter == 'regular' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_regularized', '<=', date.today()),
                                                      ('date_separated', '>', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and hiring_filter == 'regular' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_regularized', '<=', date.today()),
                                                      ('date_separated', '>', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                print records
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and hiring_filter == 'regular' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_regularized', '<=', date.today()),
                                                      ('date_separated', '>', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND SEPARATED W/O DATE
        if hiring_filter == 'separate' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_separated', '<=', date.today()),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if company and filters == 'by_company' and hiring_filter == 'separate' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_separated', '<=', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and hiring_filter == 'separate' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_separated', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                print records
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and hiring_filter == 'separate' and not from_date and not to_date:
            records = self.env['hr.employee'].search([('date_separated', '<=', date.today()),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND SEPARATED DATE W/ DATE
        if from_date and to_date and hiring_filter == 'separate':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('active', '=', False),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and company and filters == 'by_company' and hiring_filter == 'separate':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('active', '=', False),
                                                      ('state', 'ilike', str(state))])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and branch and filters == 'by_branch' and hiring_filter == 'separate':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('active', '=', False),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', branch)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and hiring_filter == 'separate':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('active', '=', False),
                                                      ('state', 'ilike', str(state)),
                                                      ('department_id', 'in', department)])
            print records
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'records': records,

        }

        return self.env['report'].render('hrms_employee.report_hr_employee_template', docargs)

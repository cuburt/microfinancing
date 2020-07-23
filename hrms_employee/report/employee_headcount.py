from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class HrEmployeeHeadcountHandler(models.TransientModel):
    _name = 'hr.employee.headcount.handler'

    from_date = fields.Date(string="Start Date", required=False,
                            default=date(date.today().year, date.today().month, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, date.today().month,
                                                                          calendar.monthrange(date.today().year,
                                                                                              date.today().month)[1]))
    company_ids = fields.Many2many('res.company', string="Company")
    branch_ids = fields.Many2many('hr.department', string="Branch(es)")
    department_ids = fields.Many2many('hr.department', string="Department(s)")
    state = fields.Selection(string="Employment Status", selection=[('all', 'All Active Employee(s)'),
                                                                    ('newly', 'Newly Hired Employee(s)'),
                                                                    ('separated', 'Separated Employee(s)')], default='all')
    filters = fields.Selection([('by_dept', 'MSG Employees'),('by_branch', 'Non-MSG / Operation Employees'), ('by_all', 'All Departments')], string='Filter By', default='by_dept')
    user_id = fields.Many2one(comodel_name="hr.employee", string="User(s)", required=False,
                              default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))
    
    @api.onchange('company_ids', 'filters')
    def _onchange_company_ids(self):
        result = {}
        if self.company_ids:
            if self.filters == 'by_dept':
                result['domain'] = {'department_ids': [('company_id', 'in', self.company_ids.ids)]}
            if self.filters == 'by_branch':
                result['domain'] = {'branch_ids': [('company_id', 'in', self.company_ids.ids)]}
            return result

    @api.multi
    def company_env(self, cid):
        if cid:
            result = self.env['res.company'].browse(cid)
            return result

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

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'all':
            self.from_date = None
            self.to_date = None
        else:
            self.from_date = date(date.today().year, date.today().month, 01)
            self.to_date = date(date.today().year, date.today().month,calendar.monthrange(date.today().year, date.today().month)[1])

    @api.multi
    def print_emp_headcount_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_ids', 'from_date', 'state', 'branch_ids', 'department_ids',
                                  'to_date', 'filters', 'user_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_hr_employee_headcount_template', data=data)

    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'hr.employee'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            if self.state == 'separated':
                name = 'List of Separated Employees\' HeadCount'
            elif self.state == 'newly':
                name = 'List of Newly Hired Employees\' HeadCount'
            else:
                name = 'List of All Employees\' HeadCount'
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'hrms_employee.hr_employee_headcount_report_xls.xlsx',
                    'datas': datas,
                    'name': name + ' ' + str(
                        datetime.strftime(datetime.now() + relativedelta(hours=8), "%Y-%m-%d %I:%M:%S %p"))
                    }


# PDF FILE REPORT
class HRMSEmployeeHeadCountReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_hr_employee_headcount_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        records = {}
        company = data['form']['company_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        filters = data['form']['filters']
        state = data['form']['state']
        department = data['form']['department_ids']
        branch = data['form']['branch_ids']

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/O DATE
        # All Active Employees
        if filters == 'by_all' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id.is_operation', '=', False)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', True),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', False),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/ DATE
        if from_date and to_date and filters == 'by_all' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")
        
        # Newly Hired Employees
        if from_date and to_date and filters == 'by_all' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")
        
        # Separated Employees
        if from_date and to_date and filters == 'by_all' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

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

        return self.env['report'].render('hrms_employee.report_hr_employee_headcount_template', docargs)


# EXPORT EXCEL
class HrEmployeeHeadCountReportXls(ReportXlsx):

    def get_lines(self, data):
        records = {}
        company = data['form']['company_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        filters = data['form']['filters']
        state = data['form']['state']
        department = data['form']['department_ids']
        branch = data['form']['branch_ids']

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/O DATE
        # All Active Employees
        if filters == 'by_all' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id.is_operation', '=', False)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', True),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if branch and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('department_id.is_operation', '=', False),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '<=', date.today()),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # EMPLOYEE SELECTION WITH STATUS AND ACTUAL HIRING DATE W/ DATE
        if from_date and to_date and filters == 'by_all' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'not in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'all':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', 'not in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # Newly Hired Employees
        if from_date and to_date and filters == 'by_all' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', '=', 'probationary')])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'newly':
            records = self.env['hr.employee'].sudo().search([('date_hired', '>=', from_date),
                                                      ('date_hired', '<=', to_date),
                                                      ('state', '=', 'probationary'),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        # Separated Employees
        if from_date and to_date and filters == 'by_all' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and not company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', True),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_branch' and branch and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', branch)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'by_dept' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('company_id', 'in', company),
                                                      ('department_id.is_operation', '=', False),
                                                      ('state', 'in', ['relieved', 'terminate'])])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'by_dept' and company and state == 'separated':
            records = self.env['hr.employee'].search([('date_separated', '>=', from_date),
                                                      ('date_separated', '<=', to_date),
                                                      ('state', 'in', ['relieved', 'terminate']),
                                                      ('company_id', 'in', company),
                                                      ('department_id', 'in', department)])

            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        return records

    def get_data(self, data):
        lines = []
        employee = self.get_lines(data)
        if employee:
            for obj in sorted(employee, key=lambda r: r.name):
                values = {
                    'company_id': obj.company_id.id,
                    'company_name': obj.company_id.name,
                    'department_id': obj.department_id.parent_id.id if obj.department_id.parent_id else obj.department_id.id,
                    'department_name': obj.department_id.parent_id.name if obj.department_id.parent_id else obj.department_id.name,
                    'parent_department_id': obj.department_id.parent_id.id if obj.department_id.parent_id else False,
                    'is_parent': True if obj.department_id.parent_id else False,
                    'operation': obj.department_id.is_operation,
                    'employee_id': obj.id,
                    'employee_name': obj.name,
                }
                lines.append(values)
        else:
            raise ValidationError(_('No records found.'))
        return lines

    def get_companies(self, data):
        cats = []
        get_lines = self.get_data(data)
        for category in get_lines:
            val1 = {
                'company_id': category['company_id'],
                'company_name': category['company_name'],
            }
            cats.append(val1)
        return cats

    def get_company(self, data):
        company = self.get_companies(data)
        companies = list({v['company_id']: v for v in company}.values())
        result = sorted(companies, key=lambda r: r['company_name'])
        print companies
        return result

    def get_parent_department(self, data):
        depts = self.get_depts(data)
        d = list({v['company_id'] and v['parent_department_id']: v for v in depts}.values())
        result = sorted(d, key=lambda x: x['department_name'])
        print result
        return result

    def get_depts(self, data):
        dept = []
        get_lines = self.get_data(data)
        for category in get_lines:
            val1 = {
                'company_id': category['company_id'],
                'department_id': category['department_id'],
                'department_name': category['department_name'],
                'parent_department_id': category['parent_department_id'],
                'operation': category['operation']
            }
            dept.append(val1)
        return dept

    def get_department(self, data):
        depts = self.get_depts(data)
        d = list({v['company_id'] and v['department_id']: v for v in depts}.values())
        result = sorted(d, key=lambda x: x['department_name'])
        print result
        return result

    def get_emps(self, data):
        dept = []
        get_lines = self.get_data(data)
        for category in get_lines:
            val1 = {
                'company_id': category['company_id'],
                'department_id': category['department_id'],
                'employee_id': category['employee_id'],
                'employee_name': category['employee_name'],
            }
            dept.append(val1)
        return dept

    def get_employee(self, data):
        emps = self.get_emps(data)
        l1 = list({v['department_id'] and v['employee_id']: v for v in emps}.values())
        result = sorted(l1, key=lambda x: x['employee_name'])
        return result

    def generate_xlsx_report(self, workbook, data, lines):
        get_company = self.get_company(data)
        get_department = self.get_department(data)
        get_parent_department = self.get_parent_department(data)
        get_data = self.get_data(data)
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        company_ids = data['form']['company_ids']
        filters = data['form']['filters']
        state = data['form']['state']
        if filters == 'by_dept':
            add_sheets = [1]
        elif filters == 'by_branch':
            add_sheets = [2]
        else:
            add_sheets = [1, 2]
        prod_row = 8
        prod_col = 0
        header_row = 7
        header_col = 0
        for cid in add_sheets:
            # company = self.env['res.company'].browse(cid['company_id'])
            # abbr = company.partner_id.abbreviation
            if cid == 1:
                abbr = 'MSG'
                operation = False
                header_name = 'MANAGEMENT SERVICES GROUP'
            else:
                operation = True
                names = []
                abbrs = []
                for cidss in company_ids:
                    comps = self.env['res.company'].browse(cidss)
                    if comps.partner_id.abbreviation not in ('MUTI', 'HSI', 'EPFC', 'MSG'):
                        names.append(str(comps.name))
                        abbrs.append(str(comps.partner_id.abbreviation))
                if names:
                    header_name = ', '.join(names)
                    abbr = ', '.join(abbrs)
                else:
                    header_name = 'OPERATIONS'
                    abbr = 'OPERATIONS'
            sheet = workbook.add_worksheet(str(abbr))
            format_header = workbook.add_format({'font_size': 14, 'bold': True})
            format_header1 = workbook.add_format({'font_size': 13, 'bold': True})
            format_header2 = workbook.add_format({'font_size': 12, 'bold': True})
            format_no_border = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'right': False, 'left': False, 'bottom': False, 'top': False, 'bold': True})
            format_gray = workbook.add_format( {'text_wrap': True, 'bg_color': 'd6d8db', 'font_size': 11, 'valign': 'vcenter','align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format_name = workbook.add_format({'text_wrap': True, 'color': 'white', 'bg_color': '0d3982', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format_names = workbook.add_format({'text_wrap': True, 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format_record_left = workbook.add_format({'valign': 'vcenter','bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 11})
            format_record_center = workbook.add_format({'valign': 'vcenter','bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 11})
            format_record_right = workbook.add_format({'valign': 'vcenter','bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 11, 'num_format': '#,##0.00'})
            format_date = workbook.add_format({'font_size': 12})
            format_total = workbook.add_format({'valign': 'vcenter','bg_color': 'd6d8db', 'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12, 'bold':True})
            format_record_left.set_align('left')
            format_record_center.set_align('center')
            format_record_right.set_align('right')
            format_total.set_align('center')
            format_header.set_align('center')
            format_header1.set_align('center')
            format_header2.set_align('left')
            format_date.set_align('left')
            sheet.merge_range('B2:K2', header_name, format_header)
            if state == 'newly':
                heading = 'NEWLY HIRED '
            elif state == 'separated':
                heading = 'SEPARATED '
            else:
                heading = ''

            if from_date and to_date:
                sheet.merge_range('B4:K4', heading + 'OFFICIAL HEADCOUNT AS OF ' + str(from_date) + ' - ' + str(to_date),
                                  format_header1)
            else:
                sheet.merge_range('B4:K4', heading + 'OFFICIAL HEADCOUNT AS OF ' + str(date.today().strftime("%B %d, %Y")),
                                  format_header1)
            sheet.merge_range('A5:K5', 'Date: ' + str(datetime.strftime(datetime.now() + relativedelta(hours=8), "%Y-%m-%d %I:%M:%S %p")), format_date)

            for did in get_department:
                if did['operation'] == operation:
                    department = self.env['hr.department'].browse(did['department_id'])
                    sheet.merge_range(header_row - 2, 0, header_row - 2, header_col + 3, department.name, format_header2)
                    sheet.write(header_row - 1, header_col, 'NO.', format_name)
                    sheet.merge_range(header_row - 1, header_col + 1, header_row - 1, header_col + 3, 'EMPLOYEE NAME', format_name)
                    sheet.write(header_row - 1, header_col + 4, 'COMPANY NAME', format_name)
                    sheet.write(header_row - 1, header_col + 5, 'DATE HIRED', format_name)
                    if state == 'separated':
                        sheet.write(header_row - 1, header_col + 6, 'DATE SEPARATED', format_name)
                        sheet.merge_range(header_row - 1, header_col + 7, header_row - 1, header_col + 9, 'POSITION', format_name)
                        sheet.merge_range(header_row - 1, header_col + 10, header_row - 1, header_col + 11, 'COMPANY', format_name)
                        num = 12
                    else:
                        sheet.merge_range(header_row - 1, header_col + 6, header_row - 1, header_col + 8, 'POSITION', format_name)
                        sheet.merge_range(header_row - 1, header_col + 9, header_row - 1, header_col + 10, 'COMPANY', format_name)
                        num = 11
                    number = 1
                    for cids in company_ids:
                        companies = self.env['res.company'].browse(cids)
                        sheet.write(header_row - 1, header_col + num, str(companies.partner_id.abbreviation).upper(), format_name)
                        num += 1
                    sheet.write(header_row - 1, header_col + num, 'TOTAL', format_name)

                    over_all = 0.0
                    for each in get_data:
                        if each['department_id'] == department.id:
                            emp_id = self.env['hr.employee'].browse(each['employee_id'])
                            # date_hired = (datetime.strptime(emp_id.date_hired, '%Y-%m-%d')).strftime('%B %d, %Y')
                            sheet.write(prod_row, prod_col, number, format_record_center)
                            sheet.write(prod_row, prod_col + 1, str(emp_id.identification_id).upper(), format_record_center)
                            sheet.merge_range(prod_row, prod_col + 2, prod_row, prod_col + 3, emp_id.name, format_record_left)
                            sheet.write(prod_row, prod_col + 4, emp_id.company_name, format_record_left)
                            sheet.write(prod_row, prod_col + 5, str(emp_id.date_hired), format_record_center)
                            if state == 'separated':
                                sheet.write(prod_row, prod_col + 6, str(emp_id.date_separated), format_record_center)
                                sheet.merge_range(prod_row, prod_col + 7, prod_row, prod_col + 9, str(emp_id.job_id.name).upper(), format_record_left)
                                sheet.merge_range(prod_row, prod_col + 10, prod_row, prod_col + 11, str(emp_id.company_id.name).upper(), format_record_left)
                                x = 12
                            else:
                                sheet.merge_range(prod_row, prod_col + 6, prod_row, prod_col + 8, str(emp_id.job_id.name).upper(), format_record_left)
                                sheet.merge_range(prod_row, prod_col + 9, prod_row, prod_col + 10, str(emp_id.company_id.name).upper(), format_record_left)
                                x = 11
                            total = 0.00
                            for cids in company_ids:
                                companies = self.env['res.company'].browse(cids)
                                if emp_id.compensation_ids:
                                    for compensation in emp_id.compensation_ids:
                                        if compensation.company_id.id == companies.id:
                                            total += compensation.shared / 100.0
                                            sheet.write(prod_row, prod_col + x, float(compensation.shared / 100.0), format_no_border)
                                x = x + 1
                            over_all += total
                            sheet.write(prod_row, prod_col + x, total, format_no_border)
                            number = number + 1
                            prod_row = prod_row + 1
                    if state == 'separated':
                        under = 11
                    else:
                        under = 10
                    sheet.merge_range(prod_row, prod_col, prod_row, prod_col + under, 'TOTAL >>>', format_gray)
                    if state == 'separated':
                        y = 12
                    else:
                        y = 11
                    for cids in company_ids:
                        companies = self.env['res.company'].browse(cids)
                        total_comp = 0.0
                        for each in get_data:
                            if each['department_id'] == department.id:
                                employee_id = self.env['hr.employee'].browse(each['employee_id'])
                                for compensation in employee_id.compensation_ids:
                                    if compensation.company_id.id == companies.id:
                                        total_comp += compensation.shared / 100.0
                        sheet.write(prod_row, prod_col + y, total_comp, format_gray)
                        y = y + 1
                    sheet.write(prod_row, prod_col + y, over_all, format_gray)
                    prod_row = prod_row + 3
                    header_row = prod_row

            sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, 'GRAND TOTAL ' + str(abbr), format_gray)
            zz = 4
            for cidss in company_ids:
                companies = self.env['res.company'].browse(cidss)
                sheet.write(prod_row, prod_col + zz, str(companies.partner_id.abbreviation).upper(),
                            format_name)
                zz = zz + 1
            sheet.write(prod_row, prod_col + zz, 'TOTAL', format_name)
            prod_row = prod_row + 1
            z = 4
            over_alls = 0.0
            for cids in company_ids:
                companies = self.env['res.company'].browse(cids)
                total_comp = 0.0
                get_datas = self.get_data(data)

                for each in get_datas:
                    if each['operation'] == operation:
                        employee_id = self.env['hr.employee'].browse(each['employee_id'])
                        for compensation in employee_id.compensation_ids:
                            if compensation.company_id.id == companies.id:
                                total_comp += compensation.shared / 100.0
                over_alls += total_comp
                sheet.write(prod_row, prod_col + z, total_comp, format_names)
                z = z + 1
            sheet.write(prod_row, prod_col + z, over_alls, format_names)
            prod_row = prod_row + 2
            sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, 'GRAND TOTAL OTHERS', format_gray)
            xx = 4
            for cidss in company_ids:
                companies = self.env['res.company'].browse(cidss)
                sheet.write(prod_row, prod_col + xx, str(companies.partner_id.abbreviation).upper(),
                            format_name)
                xx = xx + 1
            sheet.write(prod_row, prod_col + xx, 'TOTAL', format_name)
            prod_row = prod_row + 1
            zx = 4
            over_allss = 0.0
            for cids in company_ids:
                companies = self.env['res.company'].browse(cids)
                total_comp = 0.0
                get_datas = self.get_data(data)

                for each in get_datas:
                    if each['operation'] != operation:
                        employee_id = self.env['hr.employee'].browse(each['employee_id'])
                        for compensation in employee_id.compensation_ids:
                            if compensation.company_id.id == companies.id:
                                total_comp += compensation.shared / 100.0
                over_allss += total_comp
                sheet.write(prod_row, prod_col + zx, total_comp, format_names)
                zx = zx + 1
            sheet.write(prod_row, prod_col + zx, over_allss, format_names)
            prod_row = prod_row + 2
            sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, 'TOTAL HEADCOUNT', format_gray)
            xxx = 4
            for cidss in company_ids:
                companies = self.env['res.company'].browse(cidss)
                sheet.write(prod_row, prod_col + xxx, str(companies.partner_id.abbreviation).upper(),
                            format_name)
                xxx = xxx + 1
            sheet.write(prod_row, prod_col + xxx, 'TOTAL', format_name)
            prod_row = prod_row + 1
            zxx = 4
            grand_over_allss = 0.0
            for cids in company_ids:
                companies = self.env['res.company'].browse(cids)
                total_comp = 0.0
                get_datas = self.get_data(data)
                for each in get_datas:
                    employee_id = self.env['hr.employee'].browse(each['employee_id'])
                    for compensation in employee_id.compensation_ids:
                        if compensation.company_id.id == companies.id:
                            total_comp += compensation.shared / 100.0
                grand_over_allss += total_comp
                sheet.write(prod_row, prod_col + zxx, total_comp, format_names)
                zxx = zxx + 1
            sheet.write(prod_row, prod_col + zxx, grand_over_allss, format_names)
            header_row = 7
            prod_row = 8


HrEmployeeHeadCountReportXls('report.hrms_employee.hr_employee_headcount_report_xls.xlsx', 'hr.employee')

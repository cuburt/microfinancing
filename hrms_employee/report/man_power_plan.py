from odoo import models, api, fields, _
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError
import calendar

MonthDate = [(1, 'JAN'),
             (2, 'FEB'),
             (3, 'MAR'),
             (4, 'APR'),
             (5, 'MAY'),
             (6, 'JUN'),
             (7, 'JUL'),
             (8, 'AUG'),
             (9, 'SEP'),
             (10, 'OCT'),
             (11, 'NOV'),
             (12, 'DEC'),
             ]


class HrManpowerPlanHandler(models.TransientModel):
    _name = 'hr.manpower.plan.handler'

    department_ids = fields.Many2many(comodel_name="hr.department", string="Department", required=False)
    from_date = fields.Date(string="Start Date", required=False, default=date(date.today().year, 01, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, 12, 31))
    responsible_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False,
                                     default=lambda self: self.env['hr.employee'].search(
                                         [('user_id', '=', self.env.user.id)], limit=1))
    prepared_by = fields.Many2one(comodel_name="hr.employee", string="Prepared By:", required=False)

    approved_by1 = fields.Many2one(comodel_name="hr.employee", string="1st Approval:", required=False)
    approved_by2 = fields.Many2one(comodel_name="hr.employee", string="2nd Approval:", required=False)
    prepared_by_job = fields.Char(string="Prepared By:", required=False, )
    approved_by1_job = fields.Char(string="1st Approval:", required=False, )
    approved_by2_job = fields.Char(string="2nd Approval:", required=False, )
    notes = fields.Text(string="Notes", required=False, )

    @api.onchange('from_date', 'to_date')
    def check_department_ids(self):
        result = {}
        if self.from_date and self.to_date:
            records = []
            departments = self.env['hr.department'].search([('active', '=', True)])
            if departments:
                for department in departments:
                    if not department.parent_id and department.id not in records:
                        records.append(department.id)
            result['domain'] = {'department_ids': [('id', 'in', records)]}
            return result

    @api.onchange('department_ids')
    def _onchange_department_ids(self):
        if self.department_ids:
            for dept in self.department_ids.ids:
                department = self.env['hr.department'].browse(dept)
                if department:
                    self.prepared_by = department.manager_id.id
                    self.approved_by1 = department.manager_id.parent_id.id
                    self.prepared_by_job = department.manager_id.job_id.name
                    self.approved_by1_job = department.manager_id.parent_id.job_id.name

    @api.onchange('approved_by2')
    def _onchange_approved_by2(self):
        if self.approved_by2:
            self.approved_by2_job = self.approved_by2.job_id.name

    @api.onchange('approved_by1')
    def _onchange_approved_by1(self):
        if self.approved_by1:
            self.approved_by1_job = self.approved_by1.job_id.name

    @api.onchange('prepared_by')
    def _onchange_prepared_by(self):
        if self.prepared_by:
            self.prepared_by_job = self.prepared_by.job_id.name

    @api.multi
    def get_sorted(self, list):
        if list:
            result = sorted(list, key=lambda x: x.name)
            print result
            return result

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

    def get_department(self, values):
        if values:
            result = self.env['hr.department'].sudo().browse(values)
            if result:
                return result

    def get_job(self, values):
        if values:
            result = self.env['hr.job'].sudo().browse(values)
            if result:
                return result

    def get_employees(self, department, from_date, to_date):
        if department and from_date and to_date:
            start = datetime.strptime(from_date, '%Y-%m-%d').date()
            end = datetime.strptime(to_date, '%Y-%m-%d').date()
            manpower = self.env['hr.manpower.plan'].search([('date_applied', '>=', start),
                                                            ('date_applied', '<=', end),
                                                            ('state', '=', 'posted'), '|',
                                                            ('department_id', '=', department.id),
                                                            ('department_id.parent_id', '=', department.id)], limit=1,
                                                           order='date_applied')
            # employees = self.env['hr.employee'].search([('state', 'not in', ['relieved', 'terminate']), ('date_hired', '<=', date_hired), '|',
            #                                             ('department_id', '=', department.id),
            #                                             ('department_id.parent_id', '=', department.id)])

            return manpower

    def get_count_employees(self, job, department, from_date, to_date):
        if department and job and from_date and to_date:
            start = datetime.strptime(from_date, '%Y-%m-%d').date()
            end = datetime.strptime(to_date, '%Y-%m-%d').date()
            manpower = self.env['hr.manpower.plan'].search([('date_applied', '>=', start),
                                                           ('date_applied', '<=', end),
                                                           ('state', '=', 'posted'), '|',
                                                           ('department_id', '=', department.id),
                                                           ('department_id.parent_id', '=', department.id)], limit=1, order='date_applied')


            # employees = self.env['hr.employee'].search([('job_id', '=', job.id), ('state', 'not in', ['relieved', 'terminate']),
            #                                             ('date_hired', '<=', date_hired), '|',
            #                                             ('department_id', '=', department.id),
            #                                             ('department_id.parent_id', '=', department.id)])
            count = 0
            if manpower:
                for rec in manpower.line_ids:
                    if rec.job_id.id == job.id:
                        count += rec.no_of_employee
            return count

    @api.onchange('from_date', 'to_date')
    def get_validation_date(self):
        if self.from_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))
        if self.to_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))

    @api.multi
    def print_manpower_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.sudo().read(['from_date', 'department_ids',
                                         'to_date', 'responsible_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_man_power_template', data=data)


class HrManpowerPlanReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_man_power_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        department = data['form']['department_ids']
        records = {}
        if from_date and to_date and department:
            records = self.env['hr.manpower.plan'].search([('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date),
                                                           ('state', '=', 'posted'), '|',
                                                           ('department_id', 'in', department),
                                                           ('department_id.parent_id', 'in', department)])

            # print records
            # if records:
            #     for record in records:
            #         values = {
            #             'department_id': record.department_id.parent_id.id if record.department_id.parent_id else record.department_id.id,
            #             'month_date': record.month_date,
            #             'job_id': record.job_id.id,
            #             'no_of_recruitment': record.no_of_recruitment
            #         }
            #         result.append(values)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'records': records,
            'months': MonthDate

        }

        return self.env['report'].sudo().render('hrms_employee.report_man_power_template', docargs)

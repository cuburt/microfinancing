from odoo import models, api, _, fields
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
import calendar

MonthDate = [(1, 'January'),
             (2, 'February'),
             (3, 'March'),
             (4, 'April'),
             (5, 'May'),
             (6, 'June'),
             (7, 'July'),
             (8, 'August'),
             (9, 'September'),
             (10, 'October'),
             (11, 'November'),
             (12, 'December'),
             ]

class HrResourcingPlan(models.TransientModel):
    _name = 'hr.resource.handler'

    from_date = fields.Date(string="Start Date", required=False,
                            default=date(date.today().year, 01, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, 12, 31))
    year_date = fields.Selection([(num, str(num)) for num in range(date.today().year - 5, date.today().year + 1)],
                                 string="Year", default=date.today().year)
    month_date = fields.Selection(selection=MonthDate, required=False, string="Month", default=date.today().month)
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Company", required=False)
    company_ids = fields.Many2many(comodel_name="res.company", string="Company", required=False, )
    department_ids = fields.Many2many(comodel_name="hr.department", string="Department(s)", required=False)
    branch_ids = fields.Many2many(comodel_name="hr.department", string="Branch(es)", required=False)
    job_ids = fields.Many2many(comodel_name="hr.job", string="Job Position(s)", )
    filters = fields.Selection(string="Filter By", selection=[('company', 'By Company'),
                                                              ('department', 'By Department'),
                                                              ('branch', 'By Branch'),
                                                              ('job', 'By Job Position')],
                               required=False, default='department')
    plan_type = fields.Selection(string="Type", selection=[('monthly', 'Resourcing Plan'), ('yearly', 'Recruitment Plan'), ], required=False, default='monthly')
    responsible_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False,
                                     default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))

    @api.multi
    def get_approvers_name(self, values):
        if values:
            employee = self.env['hr.employee'].browse(values)
            if employee:
                last_name = employee.last_name
                first_name = employee.first_name
                if employee.middle_name:
                    middle_name = str(employee.middle_name)[:1]
                else:
                    middle_name = ''
                name = '%s %s. %s' % (first_name, middle_name, last_name)
                return name

    @api.onchange('plan_type')
    def _get_duration(self):
        if self.plan_type:
            if self.plan_type == 'yearly':
                if self.year_date:
                    self.from_date = date(int(self.year_date), 01, 01)
                    self.to_date = date(int(self.year_date), 12, 31)
            else:
                if self.month_date:
                    last = calendar.monthrange(date.today().year, self.month_date)[1]
                    start_months = date(date.today().year, self.month_date, 01)
                    finish_months = date(date.today().year, self.month_date, last)
                    self.from_date = start_months
                    self.to_date = finish_months

    @api.onchange('year_date')
    def _onchange_year_date(self):
        if self.year_date:
            self.from_date = date(int(self.year_date), 01, 01)
            self.to_date = date(int(self.year_date), 12, 31)

    @api.onchange('month_date')
    def _onchange_month_date(self):
        if self.month_date:
            last = calendar.monthrange(date.today().year, self.month_date)[1]
            start_months = date(date.today().year, self.month_date, 01)
            finish_months = date(date.today().year, self.month_date, last)
            self.from_date = start_months
            self.to_date = finish_months

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
    def print_resource_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.sudo().read(['partner_ids', 'department_ids', 'job_ids', 'branch_ids', 'year_date',
                                         'month_date', 'plan_type', 'filters', 'company_ids', 'from_date', 'to_date'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_resource_template', data=data)


class HrResourcePlanReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_resource_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        company = data['form']['company_ids']
        partner = data['form']['partner_ids']
        branch = data['form']['branch_ids']
        department = data['form']['department_ids']
        job = data['form']['job_ids']
        filters = data['form']['filters']

        if from_date and to_date and filters == 'company' and not company:
            cid = []
            for companies in self.env['res.company'].search([]):
                cid.append(companies.id)
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('company_id', 'in', cid)])
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'department' and not department:
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('department_id.is_branch', '=', False)])
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'branch' and not branch:
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('department_id.is_branch', '=', True)])
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'job' and not job:
            jid = []
            for jobs in self.env['hr.job'].search([]):
                jid.append(jobs.id)
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('job_id', 'in', jid)])
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'company' and company:
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('company_id', 'in', company)])
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'department' and department:
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('department_id', 'in', department),
                                                                 ('department_id.is_branch', '=', False)])
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'branch' and branch:
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('department_id', 'in', branch),
                                                                 ('department_id.is_branch', '=', True)])
            if records:
                records
            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and job and filters == 'job':
            records = self.env['hr.recruitment.request'].search([('date_request', '>=', from_date),
                                                                 ('date_request', '<=', to_date),
                                                                 ('job_id', 'in', job)])
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

        return self.env['report'].sudo().render('hrms_employee.report_resource_template', docargs)
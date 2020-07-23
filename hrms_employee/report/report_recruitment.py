from odoo import models, api, fields, _
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError
import calendar


class HrRecruitmentHandler(models.TransientModel):
    _name = 'hr.recruitment.handler'

    company_ids = fields.Many2many(comodel_name="res.company", string="Company", required=False)
    department_ids = fields.Many2many(comodel_name="hr.department", string="Department", required=False)
    branch_ids = fields.Many2many(comodel_name="hr.department", string="Branch")
    job_ids = fields.Many2many(comodel_name="hr.job", string="Job Position", required=False, )
    stage_state = fields.Many2many(comodel_name="hr.recruitment.stage", string="Stage", default=lambda self: self.env['hr.recruitment.stage'].search([]))
    from_date = fields.Date(string="Start Date", required=False, default=date(date.today().year, date.today().month, 01))
    to_date = fields.Date(string="End Date", required=False, default=date(date.today().year, date.today().month, calendar.monthrange(date.today().year, date.today().month)[1]))
    responsible_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False,
                                     default=lambda self: self.env['hr.employee'].search(
                                         [('user_id', '=', self.env.user.id)], limit=1))
    filters = fields.Selection(string="Filters", selection=[('company', 'By Company'),
                                                            ('department', 'By Department'),
                                                            ('branch', 'By Branch'),
                                                            ('job', 'by Job Position'), ],
                               default='department', required=False, )
    set_all_history = fields.Boolean(string="Set Applicant History")

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

    @api.onchange('from_date', 'to_date')
    def get_validation_date(self):
        if self.from_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))
        if self.to_date:
            if self.from_date >= self.to_date:
                raise ValidationError(_('Start date cannot be greater than the ending date of report'))

    @api.multi
    def print_recruitment_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.sudo().read(['job_ids', 'company_ids', 'from_date', 'stage_state', 'department_ids', 'filters', 'branch_ids',
                                         'to_date', 'set_all_history', 'responsible_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_recruitment_template', data=data)


class HrRecruitmentReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_recruitment_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        company = data['form']['company_ids']
        job = data['form']['job_ids']
        branch = data['form']['branch_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        state = data['form']['stage_state']
        department = data['form']['department_ids']
        filters = data['form']['filters']
        set_all_history = data['form']['set_all_history']

        # Applicant Procedure
        if to_date and from_date and filters == 'company' and not company and set_all_history:
            cid = []
            for companies in self.env['res.company'].search([]):
                cid.append(companies.id)
            if cid:
                records = self.env['hr.applicant'].search([('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date),
                                                           ('company_id', 'in', company)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if to_date and from_date and state and filters == 'company' and not company:
            cid = []
            for companies in self.env['res.company'].search([]):
                cid.append(companies.id)
            if cid:
                records = self.env['hr.applicant'].search([('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date),
                                                           ('stage_id', 'in', state),
                                                           ('company_id', 'in', cid)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if company and to_date and from_date and filters == 'company' and set_all_history:
            records = self.env['hr.applicant'].search([('company_id', 'in', company),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if company and to_date and from_date and state and filters == 'company':
            records = self.env['hr.applicant'].search([('company_id', 'in', company),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date),
                                                       ('stage_id', 'in', state)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'department' and not department and set_all_history:
            dept = []
            for depart in self.env['hr.department'].search([('is_branch', '=', False)]):
                dept.append(depart.id)
            if dept:
                records = self.env['hr.applicant'].search([('department_id', 'in', dept),
                                                           ('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if state and from_date and to_date and filters == 'department':
            dept = []
            for depart in self.env['hr.department'].search([('is_branch', '=', False)]):
                dept.append(depart.id)
            if dept:
                records = self.env['hr.applicant'].search([('stage_id', 'in', state),
                                                           ('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date),
                                                            ('department_id', 'in', dept)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and department and filters == 'department' and set_all_history:
            records = self.env['hr.applicant'].search([('department_id', 'in', department),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if state and from_date and to_date and department and filters == 'department':
            records = self.env['hr.applicant'].search([('stage_id', 'in', state),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date),
                                                       ('department_id', 'in', department)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and filters == 'branch' and not branch and set_all_history:
            dept = []
            for depart in self.env['hr.department'].search([('is_branch', '=', True)]):
                dept.append(depart.id)
            if dept:
                records = self.env['hr.applicant'].search([('department_id', 'in', dept),
                                                           ('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if state and from_date and to_date and filters == 'branch':
            dept = []
            for depart in self.env['hr.department'].search([('is_branch', '=', True)]):
                dept.append(depart.id)
            if dept:
                records = self.env['hr.applicant'].search([('stage_id', 'in', state),
                                                           ('date_applied', '>=', from_date),
                                                           ('date_applied', '<=', to_date),
                                                           ('department_id', 'in', dept)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and branch and filters == 'branch' and set_all_history:
            records = self.env['hr.applicant'].search([('department_id', 'in', branch),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if state and from_date and to_date and branch and filters == 'branch':
            records = self.env['hr.applicant'].search([('stage_id', 'in', state),
                                                       ('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date),
                                                       ('department_id', 'in', branch)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if state and job and from_date and to_date and filters == 'job':
            records = self.env['hr.applicant'].search([('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date),
                                                       ('job_id', 'in', job),
                                                       ('stage_id', 'in', state)])
            print records
            if records:
                records

            else:
                raise ValidationError("No Records Found!")

        if from_date and to_date and job and filters == 'job' and set_all_history:
            records = self.env['hr.applicant'].search([('date_applied', '>=', from_date),
                                                       ('date_applied', '<=', to_date),
                                                       ('job_id', 'in', job)])
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

        return self.env['report'].sudo().render('hrms_employee.report_recruitment_template', docargs)

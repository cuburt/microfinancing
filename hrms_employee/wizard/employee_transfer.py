from odoo import models, api, fields, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

emp_stages = [('joined', 'New Employee'),
              ('probationary', 'Probationary'),
              ('employment', 'Regular'),
              ('notice_period', 'Notice Period'),
              ('relieved', 'Resigned'),
              ('terminate', 'Terminated')]


class HrEmployeeTransfer(models.TransientModel):
    _name = 'hr.employee.transfer'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, )
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification",
                                            domain="[('is_parent', '=', False)]")
    effective_date = fields.Date(string="Effective Date", required=False, )
    employee_state = fields.Selection(string="Status", selection=emp_stages, required=False, )
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", required=False,
                              default=lambda self: self.env['res.users'].search([('id', '=', self.env.user.id)], limit=1))
    msg = fields.Char(string="Message", required=False, )
    state = fields.Selection(string="State",
                             selection=[('choose', ''), ('get', ''), ('post', ''), ],
                             required=False,
                             default='choose')

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.job_id = self.employee_id.job_id
            self.emp_classification_id = self.employee_id.emp_classification_id
            self.employee_state = self.employee_id.state

    @api.multi
    def process_transfer(self):
        if self.employee_id and self.effective_date:
            self.state = 'get'
            history = self.env['hr.employee.history']
            users = self.env['res.users']
            employee = self.env['hr.employee'].browse(self.employee_id.id)
            values = {
                'assigned_date': self.effective_date,
                'employee_id': self.employee_id.id,
                'job_id': self.job_id.id,
                'dept_id': self.department_id.id,
                'company_id': self.company_id.id,
                'emp_classification_id': self.emp_classification_id.id,
                'state': self.employee_state,
                'user_id': self.user_id.id
            }
            vals = {
                'job_id': self.job_id.id,
                'department_id': self.department_id.id,
                'company_id': self.company_id.id,
                'emp_classification_id': self.emp_classification_id.id,
                'state': self.employee_state,
                'parent_id': self.department_id.manager_id.id,
                'supervisor_id': self.department_id.supervisor_id.id,
                'hr_checker_id': self.employee_id.hr_checker_id.id,
                'hr_approver_id': self.employee_id.hr_approver_id.id,
                'department_municipality_id': self.department_id.municipality_id.id,
                'address_id': self.company_id.partner_id.id
            }
            employee.sudo().write(vals)
            res = history.create(values)
            prev_history = history.search([('id', '!=', res.id), ('employee_id', '=', self.employee_id.id)], limit=1, order='assigned_date desc')
            if prev_history:
                end_date = datetime.strptime(self.effective_date, '%Y-%m-%d').date() - relativedelta(days=1)
                start_date = datetime.strptime(prev_history.assigned_date, '%Y-%m-%d').date()
                duration = (end_date - start_date).days
                prev_history.sudo().write({'end_date': end_date, 'duration': duration})
            employee.check_job_template_user()
            employee.compute_holiday_paid()
            user_id = users.browse(self.employee_id.user_id.id)
            if self.employee_id.manager or self.employee_id.supervisor:
                companies = [self.company_id.id, self.company_id.parent_id.id]
            else:
                companies = [self.company_id.id]
            user_id.write({'company_id': self.company_id.id, 'company_ids': [(6, 0, [x for x in companies])]})
            self.msg = "Transferred Complete!"
            return {"type": "ir.actions.do_nothing", }

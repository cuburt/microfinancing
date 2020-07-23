from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
import calendar, datetime

SCHEDULEPAY = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('semi-monthly', 'Semi-Monthly'),
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
    ]

PAIDPAYROLL = [
        ('daily','Daily'),
        ('monthly','Monthly')
    ]

OTHERALLOWANCES = [('no', 'N/A'), ('cola', 'ECOLA'),
                   ('probationary', 'Probationary Allowance'),
                   ('extra', 'Extra Allowance'),
                   ('housing', 'Housing Allowance'),
                   ('transportation', 'Transportation Allowance'),
                   ('Rice', 'Rice Allowance'),
                   ('others', 'Others')]

emp_stages = [('joined', 'New Employee'),
              ('probationary', 'Probationary'),
              ('employment', 'Regular'),
              ('notice_period', 'Notice Period'),
              ('relieved', 'Resigned'),
              ('terminate', 'Terminated')]


class HrContractPartial(models.Model):
    _name = 'hr.contract.partial'
    _order = 'date_filed desc, name desc'

    @api.depends('wage', 'allowance', 'cola', 'paid_payroll')
    @api.multi
    def compute_total(self):
        for record in self:
            if record.wage or record.allowance or record.cola:
                total = record.wage + record.allowance + round(record.cola)
                record.update({'total_wage': float(round(total))})
        return True

    @api.depends('previous_wage', 'previous_allowance', 'previous_cola', 'previous_paid_payroll')
    @api.multi
    def previous_compute_total(self):
        for record in self:
            if record.previous_wage or record.previous_allowance or record.previous_cola:
                total = record.previous_wage + record.previous_allowance + round(record.previous_cola)
                record.update({'previous_total_wage': float(round(total))})
        return True

    name = fields.Char(string="Reference", required=False, )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False,)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currenct", required=False, related="company_id.currency_id", store=True)
    department_id = fields.Many2one(comodel_name="hr.department", string="Branch / Department", required=False)
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False)
    street = fields.Text(string="Street", required=False, )
    location_id = fields.Many2one('config.municipality', string="Current Location")
    region_id = fields.Many2one('config.region', string="Region", related="province_id.region_id", store=True)
    province_id = fields.Many2one('config.province', string="Province", related="municipality_id.province_id",
                                  store=True)
    municipality_id = fields.Many2one('config.municipality', string="City / Municipality",
                                      related="barangay_id.municipality_id", store=True)
    barangay_id = fields.Many2one('config.barangay', string="Barangay")
    birthday = fields.Date(string="Date of Birth", required=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups='hr.group_hr_user')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups='hr.group_hr_user')
    date_hired = fields.Date(string="Date Hired", required=False,)
    date_filed = fields.Date(string="Date Prepared", required=False, default=date.today())
    date_start = fields.Date(string="Date Effective", required=False, default=date.today())
    date_end = fields.Date(string="Date Effective", required=False)
    sss_no = fields.Char(string="Social Security System",related="employee_id.sss_no", store=True)
    hdmf_no = fields.Char(string="HDMF No.",related="employee_id.hdmf_no", store=True)
    tin_no = fields.Char(string="Tax Identification No.",related="employee_id.tin_no", store=True)
    ph_no = fields.Char(string="PhilHealth Number",related="employee_id.ph_no", store=True)
    employee_state = fields.Selection(emp_stages, string='Status', default='joined', track_visibility='always', copy=False,
                             help="Employee Stages.\nNewly Hired: Joined\nProbationary : Probationary")
    employment_type = fields.Selection(string="Personal Action",
                                       selection=[('initial', 'Initial Hire'),
                                                  ('confirm', 'Confirmation of Regular Employment'),
                                                  ('rehire', 'Re-Hire'),
                                                  ('promote', 'Promotion'),
                                                  ('position', 'Change in Position'),
                                                  ('separate', 'Separation'),
                                                  ('others', 'Others')], required=False, default='confirm')
    salary_changes_type = fields.Selection(string="Salary Changes Type", selection=[('none', 'N/A'),
                                                                                    ('promotion',
                                                                                     'Promotional Increase'),
                                                                                    ('merit', 'Merit Increase'),
                                                                                    ('adjust', 'Adjustment'),
                                                                                    ('others', 'Others')],
                                           required=False)
    separation_type = fields.Selection(string="Separation Type",
                                       selection=[('none', 'N/A'), ('retire', 'Retirement'), ('death', 'Death'),
                                                  ('resign', 'Resignation'), ('dismiss', 'Dismissal')],
                                       required=False, default='none')
    retired = fields.Boolean(string="Retirement")
    death = fields.Boolean(string="Death")
    resign = fields.Boolean(string="Resignation")
    dismiss = fields.Boolean(string="Dismissal")
    other_separate = fields.Boolean(string="Others (Separation Type)")
    extra_separate = fields.Char(string="Specify Separation", required=False, )
    change_position_type = fields.Selection(string="Change of Position/Assignment",
                                            selection=[('none', 'N/A'),
                                                       ('transfer', 'Transfer'),
                                                       ('reclassify', 'Reclassification'),
                                                       ('change', 'Change of Job Title'),
                                                       ('others', 'Others')], required=False, default='none')
    transfer = fields.Boolean(string="Transfer")
    reclassify = fields.Boolean(string="Reclassification")
    change = fields.Boolean(string="Change of Job Title")
    other_transfer = fields.Boolean(string="Others (Change of Position/Assignment)")
    extra_transfer = fields.Char(string="Specify Transfer", required=False, )
    extra_salary_changes = fields.Char(string="Specify Employment Type", required=False, )
    notes = fields.Text(string="Comments", required=False, )
    initiated_by_id = fields.Many2one(comodel_name="hr.employee", string="Initiated By", required=False)
    recommended_by_id = fields.Many2one(comodel_name="hr.employee", string="Recommended By", required=False)
    evaluated_by_id = fields.Many2one(comodel_name="hr.employee", string="Evaluated By", required=False)
    approved_by_id = fields.Many2many(comodel_name="hr.employee", string="Approved By", required=False)
    initiated_by_job_id = fields.Char(string="Initiated By Job Position", required=False, compute="_onchange_initiated_by_id", store=True)
    recommended_by_job_id = fields.Char(string="Recommended By Job Position", required=False, compute="_onchange_recommended_by_id", store=True)
    evaluated_by_job_id = fields.Char(string="Evaluated By Job Position", required=False, compute="_onchange_evaluated_by_id", store=True)
    approved_by_name1 = fields.Char(string="1st Approver", required=False, )
    approved_by_name2 = fields.Char(string="2nd Approver", required=False, )
    approved_by_name3 = fields.Char(string="3rd Approver", required=False, )
    approved_by_job_id1 = fields.Char(string="1st Approved By Job Position", required=False, )
    approved_by_job_id2 = fields.Char(string="2nd Approved By Job Position", required=False, )
    approved_by_job_id3 = fields.Char(string="3rd Approved By Job Position", required=False, )
    count_approver = fields.Integer(string="Count approver", required=False, compute="compute_number_approver", store=True)
    allowance = fields.Float(string="Allowance", required=False, )
    cola = fields.Float(string="Amount of other Allowance", required=False, )
    other_allowance = fields.Selection(string="Other Allowances", selection=OTHERALLOWANCES, required=False, default='no')
    specified_other_allowances = fields.Char(string="Specified Other Allowances", required=False, )
    wage = fields.Float(string="Salary Wage Monthly",  required=False, )
    wage_daily = fields.Float(string="Salary Wage Daily", required=False, )
    is_confirm = fields.Boolean(string="Confirm?",  )
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification", domain="[('is_parent', '=', False)]")
    paid_payroll = fields.Selection(PAIDPAYROLL, string='Paid Payroll Type', default='monthly')
    schedule_pay = fields.Selection(SCHEDULEPAY, string='Scheduled Pay', default='semi-monthly')
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
                                default=lambda self: self.env['hr.payroll.structure'].browse(self.env.ref('hr_payroll.structure_base').id))
    previous_contract_id = fields.Many2one(comodel_name="hr.contract.partial", string="Previous Contract", required=False, )
    forward_to_contract = fields.Boolean(string="is Forward to Real Contract")
    working_hours = fields.Many2one('resource.calendar', string='Working Schedule')
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('refuse', 'Refuse'), ('close', 'Close')], required=False, default=False)
    total_wage = fields.Float(string="Current Total Salary Wage",  required=False, compute="compute_total", store=True)
    previous_company_id = fields.Many2one(comodel_name="res.company", string="Previous Company", required=False)
    previous_department_id = fields.Many2one(comodel_name="hr.department", string="Previous Branch / Department", required=False)
    previous_job_id = fields.Many2one(comodel_name="hr.job", string="Previous Job Position", required=False)
    previous_location_id = fields.Many2one('config.municipality', string="Previous Location")
    previous_allowance = fields.Float(string="Previous Allowance", required=False, )
    previous_cola = fields.Float(string="Previous Amount of other Allowance", required=False, )
    previous_other_allowance = fields.Selection(string="Other Allowances", selection=OTHERALLOWANCES, required=False, default='no')
    previous_specified_other_allowances = fields.Char(string="Previous Specified Other Allowances", required=False, )
    previous_wage = fields.Float(string="Previous Salary Wage Monthly", required=False, )
    previous_wage_daily = fields.Float(string="Previous Salary Wage Daily", required=False, )
    previous_total_wage = fields.Float(string="Previous Total Salary Wage", required=False, compute="previous_compute_total", store=True)
    previous_emp_classification_id = fields.Many2one('hr.employee.classification', string="Previous Employee Classification", domain="[('is_parent', '=', False)]")
    previous_paid_payroll = fields.Selection(PAIDPAYROLL, string='Previous Paid Payroll Type', default='monthly')
    previous_schedule_pay = fields.Selection(SCHEDULEPAY, string='Previous Scheduled Pay', default='semi-monthly')
    previous_struct_id = fields.Many2one('hr.payroll.structure', string='Previous Salary Structure',
                                default=lambda self: self.env['hr.payroll.structure'].browse(self.env.ref('hr_payroll.structure_base').id))
    previous_working_hours = fields.Many2one('resource.calendar', string='Previous Working Schedule')
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Contract", required=False, )
    forwarded = fields.Boolean(string="Forwarded", default=True )

    @api.onchange('employment_type', 'date_hired', 'date_start')
    def _onchange_employment_type(self):
        if self.employment_type and self.date_start and self.date_hired:
            date_start = fields.Datetime.from_string(self.date_start)
            date_hired = fields.Datetime.from_string(self.date_hired)
            name = ""
            date = (date_hired).strftime('%B %d, %Y')
            if self.employment_type == 'initial':
                name = "probationary employment"
                date = (date_hired).strftime('%B %d, %Y')
                self.salary_changes_type = None
                self.separation_type = None
                self.change_position_type = None
                self.extra_salary_changes = None
            if self.employment_type == 'confirm':
                name = "confirmation of regular employment"
                self.salary_changes_type = None
                self.separation_type = None
                self.change_position_type = None
                self.extra_salary_changes = None
                date = (date_start).strftime('%B %d, %Y')
            if self.employment_type == 'promote':
                name = "promotional upon employment"
                date = (date_start).strftime('%B %d, %Y')
                self.separation_type = None
                self.change_position_type = None
                self.extra_salary_changes = None
            if self.employment_type == 'rehire':
                name = "rehiring upon employment"
                date = (date_start).strftime('%B %d, %Y')
                self.extra_salary_changes = None
            if self.employment_type == 'position':
                name = "changing of position upon employment"
                date = (date_start).strftime('%B %d, %Y')
                self.separation_type = None
                self.salary_changes_type = None
                self.extra_salary_changes = None
            if self.employment_type == 'separate':
                name = "separation of employment"
                date = (date_start).strftime('%B %d, %Y')
                self.change_position_type = None
                self.salary_changes_type = None
                self.extra_salary_changes = None
            if self.employment_type == 'others':
                if self.extra_salary_changes:
                    name = str(self.extra_salary_changes)
                else:
                    name = "other employment"
                date = (date_start).strftime('%B %d, %Y')
            self.notes = "To record %s status effective %s." % (str(name), str(date))

    @api.onchange('wage_daily', 'paid_payroll')
    def _onchange_wage_daily(self):
        if self.wage_daily and self.paid_payroll == 'daily':
            result = (float(self.wage_daily) * 313) / 12
            self.wage = float(round(result))

    @api.onchange('previous_wage_daily', 'previous_paid_payroll')
    def _onchange_previous_wage_daily(self):
        if self.previous_wage_daily and self.previous_paid_payroll == 'daily':
            result = (float(self.previous_wage_daily) * 313) / 12
            self.previous_wage = float(round(result))

    @api.multi
    @api.depends('initiated_by_id')
    def _onchange_initiated_by_id(self):
        for record in self:
            if record.initiated_by_id.job_id:
                record.initiated_by_job_id = record.initiated_by_id.job_id.name

    @api.multi
    @api.depends('recommended_by_id')
    def _onchange_recommended_by_id(self):
        for record in self:
            if record.recommended_by_id.job_id:
                record.recommended_by_job_id = record.recommended_by_id.job_id.name

    @api.multi
    @api.depends('evaluated_by_id')
    def _onchange_evaluated_by_id(self):
        for record in self:
            if record.evaluated_by_id.job_id:
                record.evaluated_by_job_id = record.evaluated_by_id.job_id.name

    @api.multi
    @api.depends('approved_by_id')
    def compute_number_approver(self):
        for approver in self:
            if approver.approved_by_id:
                count = 0
                records = []
                for line in approver.approved_by_id.ids:
                    employee = self.env['hr.employee'].browse(line)
                    count += 1
                    values = {'count': count, 'employee_name': employee.name, 'job': employee.job_id.name}
                    records.append(values)
                approver.count_approver = count
                if records:
                    for record in records:
                        if record['count'] == 1:
                            approver.approved_by_job_id1 = record['job']
                            approver.approved_by_name1 = record['employee_name']
                            approver.approved_by_job_id2 = ''
                            approver.approved_by_name2 = ''
                            approver.approved_by_job_id3 = ''
                            approver.approved_by_name3 = ''
                        elif record['count'] == 2:
                            approver.approved_by_job_id2 = record['job']
                            approver.approved_by_name2 = record['employee_name']
                            approver.approved_by_job_id3 = ''
                            approver.approved_by_name3 = ''
                        else:
                            approver.approved_by_job_id3 = record['job']
                            approver.approved_by_name3 = record['employee_name']
                if count == 4:
                    raise ValidationError(_("Approvers cannot be greater than 3. \nPlease check the appropriate approvers for the record."))

    @api.onchange('previous_contract_id')
    def _onchange_previous_contract_id(self):
        if self.previous_contract_id:
            self.previous_allowance = self.previous_contract_id.allowance
            self.previous_cola = self.previous_contract_id.cola
            self.previous_other_allowance = self.previous_contract_id.other_allowance
            self.previous_wage = self.previous_contract_id.wage
            self.previous_total_wage = self.previous_contract_id.total_wage
            self.previous_company_id = self.previous_contract_id.company_id.id
            self.previous_department_id = self.previous_contract_id.department_id.id
            self.previous_job_id = self.previous_contract_id.job_id.id
            self.previous_location_id = self.previous_contract_id.location_id.id
            self.previous_emp_classification_id = self.previous_contract_id.emp_classification_id.id
            self.previous_paid_payroll = self.previous_contract_id.paid_payroll
            self.previous_schedule_pay = self.previous_contract_id.schedule_pay
            self.previous_struct_id = self.previous_contract_id.struct_id.id
            self.previous_working_hours = self.previous_contract_id.working_hours.id
            self.previous_wage_daily = self.previous_contract_id.wage_daily
            self.previous_specified_other_allowances = self.previous_contract_id.specified_other_allowances

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                prev_contract = self.env['hr.contract.partial'].search([('date_start', '<=', record.date_start),
                                                                ('employee_id', '=', record.employee_id.id),
                                                                ('state', 'in', ['draft', 'open'])],
                                                               order='date_start desc', limit=1)
                if prev_contract:
                    record.previous_contract_id = prev_contract.id
                record.company_id = record.employee_id.company_id.id
                record.department_id = record.employee_id.department_id.id
                record.job_id = record.employee_id.job_id.id
                record.street = record.employee_id.complete_add
                record.barangay_id = record.employee_id.barangay_id.id
                record.birthday = record.employee_id.birthday
                record.emp_classification_id = record.employee_id.emp_classification_id.id
                record.gender = record.employee_id.gender
                record.marital = record.employee_id.marital
                record.date_hired = record.employee_id.date_hired
                record.location_id = record.employee_id.department_municipality_id.id
                record.working_hours = record.employee_id.calendar_id.id
                record.previous_working_hours = record.employee_id.calendar_id.id

                if record.employee_id.supervisor_id:
                    record.initiated_by_id = record.employee_id.supervisor_id.id
                else:
                    record.initiated_by_id = record.employee_id.parent_id.id
                record.recommended_by_id = record.employee_id.parent_id.id
                record.employee_state = record.employee_id.state

    @api.model
    def create(self, values):
        if not self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of contracts. \nPlease contact your administrator!."))
        if 'emp_classification_id' in values:
            emp_classification_id = self.env['hr.employee.classification'].browse(values['emp_classification_id'])
            user = self.env['res.users'].browse(self.env.user.id)
            if user and emp_classification_id:
                if user.id not in emp_classification_id.parent_id.user_ids.ids:
                    raise ValidationError(_(
                        "You are not allowed to create the records of contracts. \nPlease contact your administrator!."))
                else:
                    if 'employee_id' in values:
                        employee = self.env['hr.employee'].browse(values['employee_id'])
                        count = self.sudo().search_count([('employee_id', '=', values['employee_id'])])
                        emp_count = '{:03}'.format(int(count + 1))
                        values['name'] = 'EC' + '-' + str(employee.identification_id) + '-' + str(emp_count)
                    values['state'] = 'draft'
                    values['forwarded'] = True

        res = super(HrContractPartial, self).create(values)
        if res:
            result = self.env['hr.contract.partial'].search([('id', '!=', res.id),
                                  ('employee_id', '=', res.employee_id.id),
                                  ('employment_type', '=', res.employment_type),
                                  ('wage', '=', res.wage), ('state', 'not in', ['refuse', 'close'])], limit=1)
            if result:
                raise ValidationError(_("Records already exists! Please review the existing record. This is to avoid duplication of the records."))
        return res

    @api.multi
    def write(self, values):
        if not self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of contracts. \nPlease contact your administrator!."))
        if 'emp_classification_id' in values:
            emp_classification_id = self.env['hr.employee.classification'].browse(values['emp_classification_id'])
            user = self.env['res.users'].browse(self.env.user.id)
            if user and emp_classification_id:
                if user.id not in emp_classification_id.parent_id.user_ids.ids:
                    raise ValidationError(_("You are not allowed to create the records of contracts. \nPlease contact your administrator!."))
        res = super(HrContractPartial, self).write(values)
        if res:
            result = self.env['hr.contract.partial'].search([('id', '!=', self.id),
                                  ('employee_id', '=', self.employee_id.id),
                                  ('employment_type', '=', self.employment_type),
                                  ('wage', '=', self.wage), ('state', 'not in', ['refuse', 'close'])], limit=1)
            if result:
                raise ValidationError(_("Records already exists! Please review the existing record. This is to avoid duplication of the records."))
        return res

    # @api.onchange('employee_id')
    # def onchange_employee_id(self):
    #     for record in self:
    #         if record.employee_id:
    #             prev_contract = self.env['hr.contract.partial'].search([('date_start', '<=', record.date_start),
    #                                                             ('employee_id', '=', record.employee_id.id),
    #                                                             ('state', 'in', ['draft', 'open'])],
    #                                                            order='date_start desc', limit=1)
    #             if prev_contract:
    #                 record.previous_contract_id = prev_contract.id

    @api.multi
    def action_draft(self):
        self.state = 'draft'
        self.forwarded = True

    @api.multi
    def action_confirm(self):
        result = self.search([('id', '!=', self.id),
                              ('employee_id', '=', self.employee_id.id),
                              ('employment_type', '=', self.employment_type),
                              ('wage', '=', self.wage)])
        if not result:
            self.state = 'confirm'
            self.is_confirm = True
            self.forwarded = False
        else:
            raise ValidationError(_("Records already exists! Please review the existing record. This is to avoid duplication of the records."))

    @api.multi
    def action_close(self):
        self.state = 'close'
        self.forwarded = True
        # contract = self.contract_id
        # contract.action_expired()

    @api.multi
    def action_refuse(self):
        self.state = 'refuse'
        self.forwarded = True

    @api.multi
    def print_paf(self):
        self.ensure_one()
        return self.env['report'].get_action(self, 'hrms_employee.report_my_paf_template')

    @api.multi
    def get_id(self, values):
        if values:
            employee = self.env['hr.employee'].browse(values)
            return employee

    @api.multi
    def get_approvers(self, values):
        result = []
        for emp in values.ids:
            employee = self.env['hr.employee'].browse(emp)
            if employee.name == self.approved_by_name1:
                line = {'count': 1, 'id': employee.id, 'name': self.approved_by_name1, 'job': self.approved_by_job_id1}
                result.append(line)
            elif employee.name == self.approved_by_name2:
                line = {'count': 2, 'id': employee.id, 'name': self.approved_by_name2, 'job': self.approved_by_job_id2}
                result.append(line)
            else:
                line = {'count': 3, 'id': employee.id, 'name': self.approved_by_name3, 'job': self.approved_by_job_id3}
                result.append(line)
        res = sorted(result, key=lambda x: x['count'])
        return res

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
    def get_other_allowances(self, allowance):
        result = ''
        if allowance:
            if allowance == 'cola':
                result = 'COLA'
            elif allowance == 'probationary':
                result = 'Probationary Allowance'
            elif allowance == 'extra':
                result = 'Extra Allowance'
            elif allowance == 'housing':
                result = 'Housing Allowance'
            elif allowance == 'transportation':
                result = 'Transportation Allowance'
            elif allowance == 'rice':
                result = 'Rice Allowance'
        if result:
            return result

    def get_text_new_line(self, text):
        if text:
            result = str(text).split(". ")
            return result

    @api.multi
    def forward_to_hr_contract(self):
        for record in self:
            if record.state == 'confirm' and record.forwarded == False:
                contract = self.env['hr.contract']
                approve = []
                for appr in record.approved_by_id.ids:
                    approve.append((4, appr))
                vals = {
                    'employee_id': record.employee_id.id,
                    'department_id': record.department_id.id,
                    'job_id': record.job_id.id,
                    'partner_ids': record.company_id.partner_id.id,
                    'emp_classification_id': record.emp_classification_id.id,
                    'paid_payroll': record.paid_payroll,
                    'schedule_pay': record.schedule_pay,
                    'municipality_id': record.location_id.id,
                    'employment_type': record.employment_type,
                    'struct_id': record.struct_id.id,
                    'date_start': record.date_start,
                    'salary_changes_type': record.salary_changes_type,
                    'separation_type': record.separation_type,
                    'change_position_type': record.change_position_type,
                    'initiated_by_id': record.initiated_by_id.id,
                    'recommended_by_id': record.recommended_by_id.id,
                    'evaluated_by_id': record.evaluated_by_id.id,
                    'approved_by_id': approve,
                    'notes': record.notes,
                    'wage': record.wage,
                    'allowance': record.allowance,
                    'working_hours': record.working_hours.id,
                }
                res_id = contract.sudo().create(vals)
                if res_id:
                    contracts = contract.sudo().browse(res_id.id)
                    print res_id.id, "TRUE"
                    contracts.action_open()
                    record.forward_to_contract = True
                    record.contract_id = contracts.id
                    record.forwarded = True
            else:
                raise ValidationError(_("Contract might be forwarded already or the procedure is not followed properly. You may check the reference from salary rate ref. %s!") % record.contract_id.name)


class HrContractPartialEmployeeToPayroll(models.TransientModel):
    _name = 'hr.contract.partial.employee.payroll'

    @api.multi
    def forward_to_hr_contract(self):
        contract_ids = self.env['hr.contract.partial'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state == 'confirm':
                if self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
                    contract.forward_to_hr_contract()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))
            else:
                raise UserError(_('Please check the status of the record(s).'))


class HrContractPartialEmployee(models.TransientModel):
    _name = 'hr.contract.partial.employee'

    @api.multi
    def action_confirm(self):
        contract_ids = self.env['hr.contract.partial'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state == 'draft':
                if self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
                    contract.action_confirm()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))

    @api.multi
    def action_refuse(self):
        contract_ids = self.env['hr.contract.partial'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state not in ('refuse', 'close'):
                if self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
                    contract.action_refuse()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))

    @api.multi
    def action_close(self):
        contract_ids = self.env['hr.contract.partial'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state != 'close':
                if self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
                    contract.action_close()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))

    @api.multi
    def action_draft(self):
        contract_ids = self.env['hr.contract.partial'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state != 'refuse':
                if self.env.user.has_group('hrms_employee.group_hr_contract_personnel'):
                    contract.action_draft()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))
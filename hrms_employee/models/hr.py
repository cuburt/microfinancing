
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import collections
from num2words import num2words

SUFFIX = [
    ('jr', 'JR'),
    ('sr', 'SR'),
    ('iii', 'III'),
    ('iv', 'IV'),
    ('v', 'V'),
    ('vi', 'VI'),
    ('vii', 'VII')
]
emp_stages = [('joined', 'New Employee'),
              ('probationary', 'Probationary'),
              ('employment', 'Regular'),
              ('notice_period', 'Notice Period'),
              ('relieved', 'Resigned'),
              ('terminate', 'Terminated')]


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    # company_id_no = fields.Char(string="Identification Number", unique=True) #already exist
    # @api.multi
    # @api.depends('identification_id')
    # def check_employee_identification(self):
    #     for record in self:
    #         if record.identification_id:
    #             record.update({'identification': True})
    #         else:
    #             record.update({'identification': False})

    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    suffix = fields.Selection(SUFFIX, string="Suffix")
    prefix = fields.Many2one('res.partner.title', string="Prefix")
    company_name = fields.Char(string="Company Name")

    sss_no = fields.Char(string="Social Security System")
    hdmf_no = fields.Char(string="HDMF No.")
    tin_no = fields.Char(string="Tax Identification No.")
    ph_no = fields.Char(string="PhilHealth Number")
    driving_license_no = fields.Char(string="Driving License Number")
    driving_restriction = fields.Char(string="Driving Restriction")
    driver_license_exp_date = fields.Date(string="DL Expiry Date")
    # pnp_psag_license_no = fields.Char(string="PNP PSAG License No.")
    # pnp_license_exp_date = fields.Date(string="PNP License")
    prc_license_no = fields.Char(string="PRC License Number")
    prc_license_exp_date = fields.Date(string="PRC License Expiry Date")

    supervisor_id = fields.Many2one('hr.employee', string="Supervisor")
    manager = fields.Boolean(string="Is Manager")
    supervisor = fields.Boolean(string="Is Supervisor")

    complete_add = fields.Text(string="Complete Address")
    region_id = fields.Many2one('config.region', string="Region", related="province_id.region_id", store=True)
    province_id = fields.Many2one('config.province', string="Province", related="municipality_id.province_id", store=True)
    municipality_id = fields.Many2one('config.municipality', string="City / Municipality",
                                      related="barangay_id.municipality_id", store=True)
    barangay_id = fields.Many2one('config.barangay', string="Barangay")
    department_municipality_id = fields.Many2one('config.municipality', string="Location",
                                      related="department_id.municipality_id", store=True)

    height = fields.Float(string="Height(cm)")
    weight = fields.Float(string="Weight(lbs)")
    religion_id = fields.Many2one('hr.religion',string="Religion")

    pyrl_date_hired = fields.Date(string="Payroll Hiring Date")
    date_hired = fields.Date(string="Date of Joining")
    date_regularized = fields.Date(string="Date of Regularization", required=False, )
    date_separated = fields.Date(string="Date of Separation", required=False, )

    blood_type = fields.Char(string="Blood Type")
    allergies = fields.Char(string="Allergies")

    marital = fields.Selection(selection_add=[('singleparent',"Single Parent"),('separated','Separated')])
    employee_status_id = fields.Many2one('hr.contract.type', string="Contract Type")
    user_check_tick = fields.Boolean(default=False) # button  # button
    state = fields.Selection(emp_stages, string='Status', default='joined', track_visibility='always', copy=False,
                             help="Employee Stages.\nNewly Hired: Joined\nProbationary : Probationary")
    stages_history = fields.One2many('hr.employee.status.history', 'employee_id', string='Stage History',
                                     help='It shows the duration and history of each stages')
    employee_history = fields.One2many('hr.employee.history', 'employee_id', string="Employee History",
                                       help='It shows the history movement of employee (Company,Branch/Dept,Job Position)')
    identification = fields.Boolean(string="Check Identification Number", default=False)
    identification_id = fields.Char(string='Identification No', groups='base.group_user')
    contractual_identification_id = fields.Char(string='Contractual Identification No', groups='base.group_user')
    regular_employees = fields.Boolean(string="Regular Employees?", related="employee_status_id.regular_employees", store=True)
    hr_checker_id = fields.Many2one('hr.employee', string="Assigned Validator", domain="[('validator','=',True)]", help='Assigned validator of Notification or Leaves.\nMust be tag as Validator to show from list.')
    hr_approver_id = fields.Many2one('hr.employee', string="Assigned Reviewer", domain="[('reviewer','=',True)]", help='Assigned Reviewer of Notification or Leaves.\nMust be tag as Reviewer to show from list.')

    validator = fields.Boolean(string="Validator",  default=False, help='To Tag as Validator of Notification and Leaves')
    reviewer = fields.Boolean(string="Reviewer",  default=False, help='To Tag as Reviewer of Notification and Leaves')

    recruitment_request = fields.Boolean(string="Recruitment Requester", default=False, help='To Tag as a Requestor of Recruitment')
    resign_approve = fields.Boolean(string="Resignation Approver", default=False, help='To Tag as a Resignation Approver of Employee')
    exemption = fields.Boolean(string="Exemptional Approver", default=False, help='To Tag as Exemption of Notification and Leaves')

    form_signatory = fields.Boolean(string="Form Signatory",  help="Signatory in any forms required during employee's deployment documents.")
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
        domain="[('partner_id', '=', address_home_id)]", help='Employee bank salary account', groups='hr.group_hr_user,hr_payroll.group_hr_payroll_user')
    is_check_template = fields.Boolean(string="Is Check Template")
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification",  domain="[('is_parent', '=', False)]")
    children = fields.Integer(string='Number of Children', groups='hr.group_hr_user', compute='_compute_no_of_relative',)
    holiday_paid = fields.Boolean(string="Holiday Paid", compute="compute_holiday_paid", store=True)
    age = fields.Float(string="Age",  required=False, )
    service_render = fields.Float(string="Service Render",  required=False)
    birthday_today = fields.Date(string="Today's Birthday", required=False, compute="get_birthday_today", store=True)
    applicable_saturday_leave = fields.Float(string="Applicable Saturday Leave", required=False, )
    is_bod = fields.Boolean(string="Board of Director")
    calendar_id = fields.Many2one(comodel_name="resource.calendar", string="Working Time", required=False)
    contract_id = fields.Many2one('hr.contract', compute='_compute_contract_id', string='Current Contract',
                                  help='Latest contract of the employee', store=True)
    prf_approval_stage = fields.Selection(string="PRF Approval Stage", selection=[('0', 'Requester'),
                                                                                  ('1', '1st or Recommendation Approval'),
                                                                                  ('2', '2nd or Higher Managerial Approval'),
                                                                                  ('3', 'Evaluation Approval')], required=False, )
    compensation_ids = fields.One2many(comodel_name="hr.employee.compensation", inverse_name="employee_id", string="Compensation(s)", required=False, )

    @api.constrains('identification_id')
    def check_employee_existence(self):
        for record in self:
            employee = self.search([('id', '!=', record.id), ('identification_id', '=', record.identification_id)])
            if employee:
                raise ValidationError(_("Identification Number already exists!"))

    def _compute_contract_id(self):
        """ get the latest contract """
        contract = self.env['hr.contract']
        today_date = date.today()
        for employee in self:
            clause_1 = ['&', ('date_end', '<=', today_date), ('date_end', '>=', today_date)]
            clause_2 = ['&', ('date_start', '<=', today_date), ('date_start', '>=', today_date)]
            clause_3 = ['&', ('date_start', '<=', today_date), '|', ('date_end', '=', False),
                        ('date_end', '>=', today_date)]
            clause_final = [('employee_id', '=', employee.id), '|', '|'] + clause_1 + clause_2 + clause_3
            employee.contract_id = contract.search(clause_final, limit=1, order='date_start desc')

    @api.onchange('job_id')
    def onchange_job_id(self):
        if self.job_id:
            self.emp_classification_id = self.job_id.emp_classification_id.id

    @api.multi
    @api.depends('emp_classification_id', 'job_id')
    def compute_holiday_paid(self):
        for record in self:
            if record.emp_classification_id:
                holiday_paid = record.emp_classification_id.holiday_paid
                record.update({'holiday_paid': holiday_paid})
                record.update({'holiday_paid': holiday_paid})
            if not record.emp_classification_id and record.job_id:
                holiday_paid = record.job_id.emp_classification_id.holiday_paid
                record.update({'holiday_paid': holiday_paid})

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.onchange('barangay_id')
    def _onchange_barangay_id(self):
        if self.barangay_id:
            self.municipality_id = self.barangay_id.municipality_id.id
            self.province_id = self.municipality_id.province_id.id
            self.region_id = self.province_id.region_id.id

    @api.multi
    def add_access(self, group_access, user_id):
        if group_access:
            self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                group_access, user_id))
            found = self._cr.fetchone()
            self._cr.execute('select * from res_users where id=%s' % (user_id))
            user_found = self._cr.fetchone()
            if not found and user_found:
                self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                    group_access, user_id))
                self._cr.commit()
            if not user_found:
                print 'not found user', user_id

    @api.multi
    def create_user(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            found = self.env['res.users'].sudo().search(['|',['login','ilike',self.identification_id],['name','ilike',self.name]])
            if not found:
                if self.company_id.parent_id:
                    if self.supervisor or self.manager or self.exemption or self.resign_approve or self.recruitment_request or self.validator or self.reviewer:
                        company = [(4, self.company_id.id), (4, self.company_id.parent_id.id)]
                    else:
                        company = [(4, self.company_id.id)]
                else:
                    company = [(4, self.company_id.id)]
                user_id = self.env['res.users'].sudo().create({'name': self.name,
                                                               'login': self.identification_id,
                                                               'password': self.identification_id,
                                                               'company_ids': company,
                                                               'company_id': self.company_id.id})
                self.address_home_id = user_id.partner_id.id
                self.user_id = user_id.id
                self.user_check_tick = True
                if self.user_id:
                    partner = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)], limit=1)
                    if partner:
                        partner.update({'email': self.work_email})

                new_uid = user_id.id

                if self.validator:
                    grp_hr_validator_id = self.env.ref('hrms_employee.group_hr_validator').id
                    self.add_access(grp_hr_validator_id, new_uid)
                    # if grp_hr_validator_id:
                    #     self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                    #         grp_hr_validator_id, new_uid))
                    #     found = self._cr.fetchone()
                    #     self._cr.execute('select * from res_users where id=%s' % (new_uid))
                    #     user_found = self._cr.fetchone()
                    #     if not found and user_found:
                    #         self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                    #             grp_hr_validator_id, new_uid))
                    #         self._cr.commit()
                    #     if not user_found:
                    #         print 'not found user', new_uid

                if self.reviewer:
                    grp_hr_reviewer_id = self.env.ref('hrms_employee.group_hr_reviewer').id
                    self.add_access(grp_hr_reviewer_id, new_uid)

                if self.exemption:
                    grp_hr_exemption_id = self.env.ref('hrms_employee.group_hr_approved').id
                    self.add_access(grp_hr_exemption_id, new_uid)

                if self.resign_approve:
                    grp_hr_resign_id = self.env.ref('hrms_employee.group_hr_resignation_clearance_approver').id
                    self.add_access(grp_hr_resign_id, new_uid)

                if self.recruitment_request:
                    grp_hr_recruit_id = self.env.ref('hrms_employee.group_hr_recruitment_requester').id
                    self.add_access(grp_hr_recruit_id, new_uid)

                if self.prf_approval_stage:
                    grp_prf_access = None
                    if self.prf_approval_stage == '0':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_user_approval').id

                    if self.prf_approval_stage == '1':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_manager_approval').id

                    if self.prf_approval_stage == '2':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_bod_approval').id

                    if self.prf_approval_stage == '3':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_hr_manager_approval').id

                    self.add_access(grp_prf_access, new_uid)
                    # if grp_hr_reviewer_id:
                    #     self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                    #         grp_hr_reviewer_id, new_uid))
                    #     found = self._cr.fetchone()
                    #     self._cr.execute('select * from res_users where id=%s' % (new_uid))
                    #     user_found = self._cr.fetchone()
                    #     if not found and user_found:
                    #         self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                    #             grp_hr_reviewer_id, new_uid))
                    #         self._cr.commit()
                    #     if not user_found:
                    #         print 'not found user', new_uid

                self.check_job_template_user()

            if found:
                found.write({'active': True})
                self.user_id = found.id
                self.user_check_tick = True
                # raise ValidationError(_('Error! User already exists with same name and or login.\n'\
                #                     'Please very from your System Administrator.'))
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    @api.multi
    def update_users_workgroup(self):
        if self.user_id:
            users = self.env['res.users'].browse(self.user_id.id)
            if users:
                partner = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)], limit=1)
                if partner:
                    partner.update({'email': self.work_email})
                if self.exemption or self.resign_approve or self.recruitment_request or self.validator or self.reviewer:
                    parent = self.company_id.parent_id
                    if parent:
                        lines = []
                        for companies in users.company_ids:
                            lines.append(companies.id)
                        if self.company_id.parent_id.id not in lines:
                                users.update({'company_ids': [4, (parent.id)]})

    @api.multi
    def check_job_template_user(self):
        if self.user_id and self.job_id:
            user = self.user_id.id
            job = self.job_id.default_user_id.id
            if job:
                history = self.env['hr.employee.history'].search([('employee_id', '=', self.id), ('job_id', '!=', None)],
                                                                 order='create_date desc', limit=1)
                prev_job = history.job_id.default_user_id.id
                if prev_job:
                    self._cr.execute("""delete from res_groups_users_rel where uid = %s and gid in 
                                        (select gid from res_groups_users_rel where uid = %s)""" % (user, prev_job))
                    self._cr.commit()
                    self._cr.execute("""select gid from res_groups_users_rel where uid = %s and 
                                        gid not in (select gid from res_groups_users_rel where uid = %s)""" % (job, user))
                    groups = self._cr.fetchall()
                    for group in groups:
                        gid = group[0]
                        self._cr.execute("""insert into res_groups_users_rel (gid,uid)values(%s,%s)""" % (gid, user))
                        self._cr.commit()

    # For Report
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

    @api.multi
    def get_months(self, date, numbers):
        if date:
            date_hired = datetime.strptime(date, '%Y-%m-%d')
            additional_date = date_hired + relativedelta(months=numbers)
            result = additional_date.strftime('%B %d, %Y')
            return result

    @api.multi
    def get_num2words(self, value):
        if value:
            salary = float(value)
            # wage = str(salary).split(".")
            result = str(num2words(salary)).upper() + " PESOS"
            return result

    @api.multi
    def print_insurance_waiver(self):
        return self.env['report'].get_action(self, 'hrms_employee.insurance_waiver_template')

    @api.onchange('address_home_id')
    def user_checking(self):
        if self.address_home_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False

        if self.user_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False

    @api.constrains('supervisor_id')  # Supervisor
    def _check_supervisor_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot assign a Supervisor to itself.'))

    @api.constrains('parent_id')  # Manager
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot assign a Manager to itself.'))

    # overide from odoo put validation
    @api.onchange('department_id')
    def _onchange_department(self):
        rec = self.env['hr.department'].browse(self.department_id.id)
        if rec:
            self.supervisor_id = rec.supervisor_id.id if rec.supervisor_id else None
            self.parent_id = rec.manager_id.id if rec.manager_id else None
            self.hr_checker_id = rec.hr_checker_id.id if rec.hr_checker_id else None
            self.hr_approver_id = rec.hr_approver_id.id if rec.hr_approver_id else None
        else:
            self.supervisor_id = None
            self.parent_id = None
            self.hr_checker_id = None
            self.hr_approver_id = None

    @api.onchange('first_name', 'middle_name', 'last_name', 'suffix')
    def onchange_name(self):

        name = ''
        sep = ', '
        if self.last_name:
            lname = self.last_name.title().strip()
        else:
            lname = ''

        if lname:
            name = '%s%s' % (lname, sep)

        if self.first_name:
            fname = self.first_name.title().strip()
        else:
            fname = ''

        if fname:
            name = '%s%s%s' % (name, ' ', fname)

        if self.suffix:
            suffix = self._get_suffix(self.suffix)
        else:
            suffix = ''

        if suffix:
            name = '%s%s%s' % (name, ' ', suffix)

        if self.middle_name:
            mname = self.middle_name.title().strip()
        else:
            mname = ''

        if mname:
            name = '%s%s%s' % (name, ' ', mname)

        # if self.name == '':
        #     self.name = ''
        # else:
        #     self.name = "%s%s %s %s %s" % (lname.title().strip(), fname.title().strip(),, mname.title().strip())

        self.name = name

        self.first_name = fname.title().strip()
        self.middle_name = mname.title().strip()
        self.last_name = lname.title().strip()

    @api.multi
    def _get_suffix(self, values):
        if values == 'jr':
            suffix = 'Jr'

        elif values == 'sr':
            suffix = 'Sr'

        elif values == 'ii':
            suffix = 'II'

        elif values == 'iii':
            suffix = 'III'

        elif values == 'iv':
            suffix = 'IV'

        elif values == 'v':
            suffix = 'V'

        elif values == 'vi':
            suffix = 'VI'

        elif values == 'vii':
            suffix = 'VII'

        else:
            suffix = ''

        return suffix

    @api.onchange('birthday')
    def _onchange_birthday(self):
        for relative in self:
            if relative.birthday:
                this_year = date.today().year
                if (this_year % 4) == 0:
                    count_days = 366.00
                else:
                    count_days = 365.00
                b_date = datetime.strptime(relative.birthday, '%Y-%m-%d').date()
                my_day = date.today()
                age = ((my_day - b_date).days + 1) / count_days
                self.age = age

    @api.onchange('date_hired')
    def _onchange_date_hired(self):
        if self.date_hired:
            date_hired = datetime.strptime(self.date_hired, '%Y-%m-%d').date()
            if date_hired.day != 1:
                pyrl_date_hired = date_hired + relativedelta(months=1)
                self.pyrl_date_hired = date(pyrl_date_hired.year, pyrl_date_hired.month, 01)
            else:
                self.pyrl_date_hired = date_hired
            self.date_regularized = date_hired + relativedelta(months=5)

    @api.depends('date_hired')
    def compute_service_render(self):
        for record in self:
            if record.date_hired:
                count_days = 365.00
                b_date = datetime.strptime(record.date_hired, '%Y-%m-%d').date()
                my_day = date.today()
                service = ((my_day - b_date).days + 1) / count_days
                record.write({'service_render': service})

    @api.onchange('work_email')
    def _onchange_work_email(self):
        if self.work_email:
            if self.user_id:
                partner = self.env['res.partner'].browse(self.user_id.partner_id.id)
                partner.write({'email': self.work_email})

    @api.model
    def get_birthday_today(self):
        for rec in self:
            if rec.birthday and rec.active == True:
                b_date = datetime.strptime(rec.birthday, '%Y-%m-%d').date()
                my_day = date.today()
                if rec.state not in ['terminate', 'relieved']:
                    rec.update({'birthday_today': date(my_day.year, b_date.month, b_date.day)})

    # new
    @api.multi
    def action_rehire(self):
        if self.state in ('relieved', 'terminate'):
            if self.env.user.has_group('hrms_employee.group_hr_personnel'):
                self.state = 'joined'
                self.active = True
                self.date_separated = None
            else:
                raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    @api.multi
    def set_as_employee(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            # contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1, order='date_start desc')
            # if contract:
            #     if contract.employment_type == 'confirm':
            self.state = 'employment'
            # self.date_regularized = date.today()
            stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                    ('state', '=', 'probationary')])
            if stage_obj:
                stage_obj.write({'end_date': date.today()})
            self.stages_history.create({'start_date': date.today(),
                                                       'employee_id': self.id,
                                                       'state': 'employment'})
                    # self.create_ewa_monthly_due()
            #     else:
            #         raise ValidationError(_("Make a Regularization Contract of %s" % self.name))
            # else:
            #     raise ValidationError(_("Make a Contract of %s" % self.name))
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    # notice period
    @api.multi
    def start_notice_period(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            self.state = 'notice_period'
            stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                    ('state', '=', 'employment')])
            if stage_obj:
                stage_obj.write({'end_date': date.today()})
            self.stages_history.create({'start_date': date.today(),
                                               'employee_id': self.id,
                                               'state': 'notice_period'})
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    # @api.multi
    # def create_ewa_monthly_due(self):
    #     ewa = self.env['hr.ewa'].search([('company_id', '=', self.company_id.id), ('active', '=', True)], limit=1)
    #     ewa_line = self.env['hr.ewa.line']
    #     ewa_res = ewa_line.search([('employee_id', '=', self.id), ('active', '=', True)], limit=1)
    #     if ewa:
    #         if ewa_res:
    #             print ewa_res
    #         else:
    #             ewa_line.sudo().create({
    #                 'ewa_id': ewa.id,
    #                 'employee_id': self.id,
    #                 'paid_amount': 50.00,
    #                 'active': True,
    #                 'date': date.today()
    #             })

    # relieved,resign
    @api.multi
    def relieved(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1, order='date_start desc')
            if contract:
                contract.sudo().write({'date_end': date.today(), 'state': 'close'})
            self.state = 'relieved'
            self.date_separated = date.today()
            # self.active = False


            result = self.env['res.users'].search([['id', '=', self.user_id.id]])
            result.sudo().write({'active': False})

            stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                    ('state', '=', 'notice_period')])
            if stage_obj:
                stage_obj.write({'end_date': date.today()})
            self.stages_history.create({'end_date': date.today(),
                                        'start_date': self.date_hired,
                                        'employee_id': self.id,
                                        'state': 'relieved'})
            history = self.employee_history.search([('employee_id', '=', self.id), ('job_id', '=', self.job_id.id),
                                                    ('dept_id', '=', self.department_id.id),
                                                    ('company_id', '=', self.company_id.id),
                                                    ('emp_classification_id', '=', self.emp_classification_id.id)], limit=1)
            if history:
                history.write({'end_date': date.today()})
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    # probationary
    @api.multi
    def start_probationary(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            # contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1, order='date_start desc')
            # if contract:
            #     if contract.employment_type == 'initial':
            self.state = 'probationary'
            self.stages_history.search([('employee_id', '=', self.id),
                                        ('state', '=', 'training')]).write({'end_date': date.today()})
            self.stages_history.create({'start_date': date.today(), 'employee_id': self.id, 'state': 'probationary'})
            #     else:
            #         raise ValidationError(_("Make an Initial Hire Contract of %s" % self.name))
            # else:
            #     raise ValidationError(_("Make a Contract of %s" % self.name))
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    # terminate
    @api.multi
    def terminate(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            emp_contract = self.env['hr.contract'].browse(self.contract_id.id)
            if emp_contract:
                emp_contract.sudo().write({'date_end': date.today(), 'state': 'close'})
            self.state = 'terminate'
            self.date_separated = date.today()
            # self.active = False
            result = self.env['res.users'].search([['id', '=', self.user_id.id]])
            result.sudo().write({'active': False})

            stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                    ('state', '=', 'employment')])

            if stage_obj:
                stage_obj.write({'end_date': date.today()})
            else:
                self.stages_history.search([('employee_id', '=', self.id),
                                            ('state', '=', 'probationary')]).write({'end_date': date.today()})
            self.stages_history.create({'end_date': date.today(),
                                        'start_date': self.date_hired,
                                        'employee_id': self.id,
                                        'state': 'terminate'})
            history = self.employee_history.search([('employee_id', '=', self.id), ('job_id', '=', self.job_id.id),
                                                    ('dept_id', '=', self.department_id.id),
                                                    ('company_id', '=', self.company_id.id),
                                                    ('emp_classification_id', '=', self.emp_classification_id.id)],
                                                   limit=1)
            if history:
                history.write({'end_date': date.today()})
        else:
            raise ValidationError(_("You are not allowed for this action. Please contact your administrator."))

    def generate_identification_id(self):
        if self.env.user.has_group('hrms_employee.group_hr_personnel'):
            if not self.identification_id:
                if self.employee_status_id:
                    if self.employee_status_id.regular_employees:
                        self.identification_id = self.get_id_number(self.employee_status_id.id, self.id)
                    else:
                        self.identification_id = self.get_id_number(self.employee_status_id.id, self.id)
                        self.contractual_identification_id = self.identification_id
                    self.identification = True
            else:
                raise ValidationError(_("You already have an ID. Please make it blank if you want to regenerate again."))
        else:
            raise ValidationError(_("You are not allowed to generate the ID of employees. Please contact the administrator!"))

    def get_id_number(self, status, id):
        emp_status = self.env['hr.contract.type'].browse(status)
        self._cr.execute(""" select count(id) from hr_employee where employee_status_id = %s and id != %s""" % (emp_status.id, id))
        count_id = self._cr.fetchone()
        self._cr.execute(""" select max(identification_id) from hr_employee where employee_status_id = %s and id != %s"""  % (emp_status.id, id))
        get_id = self._cr.fetchone()
        if int(count_id[0]) > 0:
            code = len(emp_status.code)
            if emp_status.code_type == '1':
                num_id = str(get_id[0])[int(code):]
            else:
                num_id = str(get_id[0])[-(int(code)):]
            add_id = int(num_id) + 1
        else:
            add_id = 1
        letter = str(emp_status.code).upper()
        str_digits = '{:0' + str(emp_status.digits) + '}'
        if emp_status.code_type == '1':
            identification_id = "%s%s" % (letter, str_digits.format(add_id))
        else:
            identification_id = "%s%s" % (str_digits.format(add_id), letter)

        print identification_id
        return identification_id

    @api.model
    def create(self, values):

        fname = values['first_name'].title().strip()
        mname = values['middle_name'].title().strip()
        lname = values['last_name'].title().strip()
        suffix = ''
        if suffix in values:
            suffix_ids = values['suffix']
            # prefix_id = values['prefix']
            # prefix_ids = self.env['res.partner.title'].browse(prefix_id)
            suffix = self._get_suffix(suffix_ids) #convert the value of suffix
            values['suffix'] = suffix_ids
        name = "%s, %s %s %s" % (lname, fname, suffix, mname)
        values['name'] = name
        # values['prefix'] = prefix_ids.id
        values['first_name'] = fname
        values['middle_name'] = mname
        values['last_name'] = lname

        # if 'manager' in values:
        #     values['recruitment_request'] = True

        new_uid = None
        if ('validator' in values or 'reviewer' in values or 'exemption' in values or 'resign_approve' in values or 'recruitment_request' in values or 'prf_approval_stage' in values):
            if 'user_id' in values:
                new_uid = values['user_id']
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. Please contact to the administrator."))
        rec = super(HrEmployee, self).create(values)
        # user_id = self.env['res.users'].sudo().create({
        #     'name': rec.name or '' or False,
        #     'login': rec.identification_id or '' or False,
        #     'state': 'active' or False,
        #     'password': rec.identification_id or '' or False,
        #     'active': rec.active or '' or False
        # })
        # #
        # rec.write({'user_id': user_id.id,
        #            'address_home_id': user_id.partner_id.id})
        #
        # rec.create_user()
        if rec:
            # if 'employee_status_id' in values:
            #     employee_status_id = values['employee_status_id']
            #     rec.identification_id = self.get_id_number(employee_status_id, rec.id)
            if new_uid:
                rec.update_users_workgroup()
                if 'validator' in values:
                    grp_hr_validator_id = self.env.ref('hrms_employee.group_hr_validator').id
                    if values['validator']:
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_hr_validator_id, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_validator_id, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                    else:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_validator_id, new_uid))
                        self._cr.commit()

                if 'reviewer' in values:
                    grp_hr_reviewer_id = self.env.ref('hrms_employee.group_hr_reviewer').id
                    if values['reviewer']:
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_hr_reviewer_id, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_reviewer_id, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                    else:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_reviewer_id, new_uid))
                        self._cr.commit()

                if 'exemption' in values:
                    grp_hr_exemption_id = self.env.ref('hrms_employee.group_hr_approved').id
                    if values['exemption']:
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_hr_exemption_id, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_exemption_id, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                    else:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_exemption_id, new_uid))
                        self._cr.commit()

                if 'resign_approve' in values:
                    grp_hr_resign_id = self.env.ref('hrms_employee.group_hr_resignation_clearance_approver').id
                    if values['resign_approve']:
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_hr_resign_id, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_resign_id, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                    else:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_resign_id, new_uid))
                        self._cr.commit()

                if 'recruitment_request' in values:
                    grp_hr_recruit_id = self.env.ref('hrms_employee.group_hr_recruitment_requester').id
                    if values['recruitment_request']:
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_hr_recruit_id, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_recruit_id, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                    else:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_recruit_id, new_uid))
                        self._cr.commit()
                        prf_groups = self.env['res.groups'].sudo().search([('category_id', '=', self.env.ref('hrms_employee.module_category_prf').id)])
                        if prf_groups:
                            for prf_group in prf_groups:
                                self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (prf_group.id, new_uid))
                                self._cr.commit()

                if 'prf_approval_stage' in values:
                    grp_prf_access = None
                    if self.prf_approval_stage == '0':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_user_approval').id

                    if self.prf_approval_stage == '1':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_manager_approval').id

                    if self.prf_approval_stage == '2':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_bod_approval').id

                    if self.prf_approval_stage == '3':
                        grp_prf_access = self.env.ref('hrms_employee.group_prf_hr_manager_approval').id
                    if values['prf_approval_stage'] in ('0', '1', '2', '3'):
                        self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                            grp_prf_access, new_uid))
                        found = self._cr.fetchone()
                        self._cr.execute('select * from res_users where id=%s' % (new_uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_prf_access, new_uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', new_uid
                        prf_groups = self.env['res.groups'].sudo().search([('id', '!=', grp_prf_access), ('category_id', '=', self.env.ref('hrms_employee.module_category_prf').id)])
                        if prf_groups:
                            for prf_group in prf_groups:
                                self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (prf_group.id, new_uid))
                                self._cr.commit()

            employment_date = values['employment_date'] if 'employment_date' in values else date.today()

            rec.stages_history.create({'start_date': employment_date,
                                       'employee_id': rec.id,
                                       'state': 'joined'})

            # Employment History
            if 'company_id' in values or 'department_id' in values or 'job_id' in values:
                company_id = values['company_id'] if 'company_id' in values else None
                department_id = values['department_id'] if 'department_id' in values else None
                job_id = values['job_id'] if 'job_id' in values else None

                self.env['hr.employee.history'].create({'employee_id': rec.id,
                                                        'assigned_date': employment_date,
                                                        'company_id': company_id,
                                                        'dept_id': department_id,
                                                        'job_id': job_id})
        return rec

    @api.multi
    def write(self, values):

        if 'first_name' in values or 'middle_name' in values or 'last_name' in values or 'first_name' in values or \
            'suffix' in values or 'prefix' in values:
            # # Do not allow edit to Administrator
            # if self.env.id <> 1:
        # if 'parent_id' not in values:
            if 'first_name' in values and values['first_name']:
                fname = values['first_name'].title().strip()
            elif 'first_name' not in values and self.first_name:
                fname = self.first_name.title().strip()
            else:
                fname = ''

            if 'middle_name' in values and values['middle_name']:
                mname = values['middle_name'].title().strip()
            elif 'middle_name' not in values and self.middle_name:
                mname = self.middle_name.title().strip()
            else:
                mname = ''

            if 'last_name' in values and values['last_name']:
                lname = values['last_name'].title().strip()
            elif 'last_name' not in values and self.last_name:
                lname = self.last_name.title().strip()
            else:
                lname = ''

            if 'suffix' in values and values['suffix']:
                suffix = values['suffix']
            elif 'suffix' not in values and self.suffix:
                suffix = self.suffix
            else:
                suffix = ''

            if suffix:
                suffix = self._get_suffix(suffix)

            # if 'first_name' in values and values['first_name'] or 'middle_name' in values and values[
            #     'middle_name'] or 'last_name' in values and values['last_name'] or 'suffix' in values and values['suffix']:
                # if values['first_name'] or values['middle_name'] or values['last_name']:
            values['name'] = "%s, %s %s %s" % (lname, fname, suffix, mname)
            # else:
            #     values['name'] = self.name
            values['first_name'] = fname
            values['middle_name'] = mname
            values['last_name'] = lname

        if 'manager' in values:
            values['recruitment_request'] = True

        uid = None
        if 'validator' in values or 'reviewer' in values or 'exemption' in values or 'resign_approve' in values or 'recruitment_request' in values or 'prf_approval_stage' in values:
            uid = self.user_id.id
            self.update_users_workgroup()
            if 'user_id' in values:
                values['user_id'] = uid
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        rec = super(HrEmployee, self).write(values)
        if rec and self.calendar_id and self.contract_id:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1, order='date_start desc')
            if contract:
                contract.sudo().write({'working_hours': self.calendar_id.id})
        if rec or 'first_name' in values or 'middle_name' in values or 'last_name' in values or 'first_name' in values \
                or 'suffix' in values or 'prefix' in values or 'name' in values:
            if self.user_id:
                users = self.env['res.users'].browse(self.user_id.id)
                users.sudo().write({'name': self.name})
                if self.work_email:
                    users = self.env['res.users'].browse(self.user_id.id)
                    if users:
                        partner = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)], limit=1)
                        if partner:
                            partner.update({'email': self.work_email})
        if rec and uid and ('validator' in values or 'reviewer' in values or 'exemption' in values or 'resign_approve' in values or 'recruitment_request' in values or 'prf_approval_stage' in values):
            if 'validator' in values:
                grp_hr_validator_id = self.env.ref('hrms_employee.group_hr_validator').id
                if grp_hr_validator_id:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_hr_validator_id, uid))
                    found = self._cr.fetchone()
                    if values['validator']:
                        self._cr.execute('select * from res_users where id=%s' % (uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_validator_id, uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', uid
                    elif found:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_validator_id, uid))
                        self._cr.commit()

            if 'reviewer' in values:
                grp_hr_reviewer_id = self.env.ref('hrms_employee.group_hr_reviewer').id
                if grp_hr_reviewer_id:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_hr_reviewer_id, uid))
                    found = self._cr.fetchone()
                    if values['reviewer']:
                        self._cr.execute('select * from res_users where id=%s' % (uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_reviewer_id, uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', uid
                    elif found:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_reviewer_id, uid))
                        self._cr.commit()

            if 'exemption' in values:
                grp_hr_exemption_id = self.env.ref('hrms_employee.group_hr_approved').id
                if grp_hr_exemption_id:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_hr_exemption_id, uid))
                    found = self._cr.fetchone()
                    if values['exemption']:
                        self._cr.execute('select * from res_users where id=%s' % (uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_exemption_id, uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', uid
                    elif found:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_exemption_id, uid))
                        self._cr.commit()

            if 'resign_approve' in values:
                grp_hr_resign_id = self.env.ref('hrms_employee.group_hr_resignation_clearance_approver').id
                if grp_hr_resign_id:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_hr_resign_id, uid))
                    found = self._cr.fetchone()
                    if values['resign_approve']:
                        self._cr.execute('select * from res_users where id=%s' % (uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_resign_id, uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', uid
                    elif found:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_resign_id, uid))
                        self._cr.commit()

            if 'recruitment_request' in values:
                grp_hr_recruit_id = self.env.ref('hrms_employee.group_hr_recruitment_requester').id
                if grp_hr_recruit_id:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_hr_recruit_id, uid))
                    found = self._cr.fetchone()
                    if values['recruitment_request']:
                        self._cr.execute('select * from res_users where id=%s' % (uid))
                        user_found = self._cr.fetchone()
                        if not found and user_found:
                            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                                grp_hr_recruit_id, uid))
                            self._cr.commit()
                        if not user_found:
                            print 'not found user', uid
                    elif found:
                        self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (grp_hr_recruit_id, uid))
                        self._cr.commit()
                        prf_groups = self.env['res.groups'].sudo().search([('category_id', '=', self.env.ref('hrms_employee.module_category_prf').id)])
                        if prf_groups:
                            for prf_group in prf_groups:
                                self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (prf_group.id, uid))
                                self._cr.commit()

            if 'prf_approval_stage' in values:
                grp_prf_access = None
                if self.prf_approval_stage == '0':
                    grp_prf_access = self.env.ref('hrms_employee.group_prf_user_approval').id

                if self.prf_approval_stage == '1':
                    grp_prf_access = self.env.ref('hrms_employee.group_prf_manager_approval').id

                if self.prf_approval_stage == '2':
                    grp_prf_access = self.env.ref('hrms_employee.group_prf_bod_approval').id

                if self.prf_approval_stage == '3':
                    grp_prf_access = self.env.ref('hrms_employee.group_prf_hr_manager_approval').id
                print grp_prf_access
                if self.prf_approval_stage:
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (
                        grp_prf_access, uid))
                    found = self._cr.fetchone()
                    self._cr.execute('select * from res_users where id=%s' % (uid))
                    user_found = self._cr.fetchone()
                    if not found and user_found:
                        self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (
                            grp_prf_access, uid))
                        self._cr.commit()
                    if not user_found:
                        print 'not found user', uid
                    prf_groups = self.env['res.groups'].sudo().search([('id', '!=', grp_prf_access), ('category_id', '=', self.env.ref('hrms_employee.module_category_prf').id)])
                    if prf_groups:
                        for prf_group in prf_groups:
                            self._cr.execute('delete from res_groups_users_rel where gid=%s and uid=%s' % (prf_group.id, uid))
                            self._cr.commit()

        # Employment History
        # if rec and ('company_id' in values or 'department_id' in values or 'job_id' in values or 'emp_classification_id' in values):
        #     company_id = self.company_id.id
        #     department_id = self.department_id.id
        #     job_id = self.job_id.id
        #     emp_classification_id = self.emp_classification_id.id
        #     self.check_job_template_user()
        #     self.compute_holiday_paid()
        #     history = self.env['hr.employee.history'].create({'employee_id': self.id,
        #                                                       'assigned_date': date.today(),
        #                                                       'company_id': company_id,
        #                                                       'dept_id': department_id,
        #                                                       'job_id': job_id,
        #                                                       'emp_classification_id': emp_classification_id})
        #     prev_history = self.env['hr.employee.history'].search([('id', '!=', history.id),
        #                                                            ('employee_id', '=', self.id)], limit=1,
        #                                                           order='assigned_date')
        #     if prev_history:
        #         prev_history.write({'end_date': date.today()})
        return rec


class HrJob(models.Model):
    _inherit = 'hr.job'
    _order = 'name'

    @api.multi
    @api.depends('recruit_request_line', 'state')
    def compute_no_of_recruitment(self):
        for job in self:
            count = 0
            if job.state == 'recruit':
                if job.recruit_request_line:
                    for request in job.recruit_request_line:
                        if request.state == 'validate':
                            count += request.no_of_recruitment
            else:
                count = 0
            job.no_of_recruitment = count

    is_manager = fields.Boolean(string="Is a Manager")
    is_supervisor = fields.Boolean(string="Is a Supervisor")
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification")
    default_user_id = fields.Many2one(comodel_name="res.users", string="Default Template User", required=False)
    history_ids = fields.One2many(comodel_name="hr.job.history", inverse_name="job_id", string="History", required=False, )
    recruit_request_line = fields.One2many(comodel_name="hr.recruitment.request", inverse_name="job_id", string="Personnel Requesition", required=False)
    address_id_abbr = fields.Char(string="Partner's Abbreviation", required=False, related="address_id.abbreviation",
                                  store=True)
    employee_ids = fields.One2many('hr.employee', 'job_id', string='Employees', groups='base.group_user',
                                   domain=[('state', 'not in', ['relieved', 'terminate'])])
    no_of_recruitment = fields.Integer(string='Expected New Employees', help='Number of new employees you expect to recruit.', store=True,
                                       compute='compute_no_of_recruitment')
    compensatory_line = fields.One2many(comodel_name="hr.job.compensatory", inverse_name="job_id", string="Compensation(s)", required=False, )
    hr_job_count_ids = fields.One2many(comodel_name="hr.job.count", inverse_name="job_id", string="For Manpower Plan", required=False, )
    # _sql_constraints = [('unique_job_name', 'unique(name, company_id)', 'Job Position already exists!.')]
    allocation_compensation = fields.One2many('hr.allocation.compensation', 'job_id', string="Allocation Compensation")

    @api.multi
    @api.constrains('name', 'address_id')
    def _check_unique_job_name(self):
        for record in self:
            if record.address_id and record.name:
                duplicate = self.search([('id', '!=', record.id), ('company_id', '=', record.address_id.id),
                                         ('name', '=', record.name)])
                if duplicate:
                    raise UserError("Job Position already exists!")
        return True

    @api.model
    def create(self, values):
        if 'name' in values:
            if values['name']:
                name = values.get('name').upper().strip()
                values['name'] = name
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        res = super(HrJob, self).create(values)
        if res:
            res.create_template_user()
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.address_id:
                code = record.address_id.abbreviation
            else:
                code = ''
            name = "%s [%s]" % (name, code)
            result.append((record.id, name))
        return result

    @api.constrains('compensatory_line')
    def check_notification_type_duplication(self):
        if self.compensatory_line:
            company = []
            lines = self.env['hr.job.compensatory'].search([('job_id', '=', self.id)])
            for line in lines:
                company.append(line.company_id.id)
            if company:
                value_dict1 = collections.defaultdict(int)
                for list in company:
                    value_dict1[list] += 1
                result1 = any(val > 1 for val in value_dict1.itervalues())
                if result1:
                    raise ValidationError(
                        _('Please check the company. Duplication of record already exists!'))

    @api.multi
    def write(self, values):
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        res = super(HrJob, self).write(values)
        if res:
            if not self.default_user_id:
                self.create_template_user()
        return res

    @api.multi
    def set_recruit(self):
        res = super(HrJob, self).set_recruit()
        if res:
            job_line = self.env['hr.job.history']
            job_line.create({
                'job_id': self.id,
                'recruitment_date': date.today(),
                'no_of_recruitment': self.no_of_recruitment,
                'no_of_hired_employee': self.no_of_hired_employee
            })

    @api.multi
    def set_open(self):
        res = super(HrJob, self).set_open()
        if res:
            job_line = self.env['hr.job.history']
            job_line.create({
                'job_id': self.id,
                'recruitment_date': date.today(),
                'no_of_recruitment': self.no_of_recruitment,
                'no_of_hired_employee': self.no_of_hired_employee
            })

    @api.multi
    def create_template_user(self):
        name = ''
        if self.name:
            name = '%s' % (self.name)
        if self.department_id:
            name = '%s/%s' % (name, self.department_id.name)
        if self.address_id:
            name = '%s/%s' % (name, self.address_id.abbreviation)
        data = {'name': '%s template' % name}

        if not self.default_user_id:
            data['login'] = 'hr_job_%s' % self.id,
            data['company_id'] = self.company_id.id,
            data['active'] = False
            user = self.env['res.users'].sudo().create(data)
            self.write({'default_user_id':user.id,'pass':True})
        else:
            user_rec = self.env['res.users'].sudo().browse(self.default_user_id.id)
            user_rec.write(data)

    @api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.state')
    def _compute_employees(self):
        employee_data = self.env['hr.employee'].read_group([('job_id', 'in', self.ids), ('state', 'not in', ['relieved','terminate'])], ['job_id'], ['job_id'])
        result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
        for job in self:
            job.no_of_employee = result.get(job.id, 0)
            job.expected_employees = result.get(job.id, 0) + job.no_of_recruitment

# Wala Gamit na Model (hr.allocation.compensation)


class HrAllocationCompensation(models.Model):
    _name = 'hr.allocation.compensation'

    company_ids = fields.Many2one('res.partner', string="Company",
                                  domain="[('is_company', '=', True), ('owned_company', '=', True)]")
    shared = fields.Integer(string='Percentage %')
    date_effect = fields.Date(string="Effective Date")
    contract_id = fields.Many2one('hr.contract', 'Contract Ref.', ondelete='cascade')
    job_id = fields.Many2one('hr.job', 'Job Position', ondelete='cascade')


class HrJobCompensatory(models.Model):
    _name = 'hr.job.compensatory'

    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    company_id = fields.Many2one(comodel_name="res.partner", string="Company", required=False,
                                 domain="[('owned_company', '=', True)]")
    percentage = fields.Float(string="Percentage (%)",  required=False, )
    active = fields.Boolean(string="Active", default=True)


class HrJobCount(models.Model):
    _name = 'hr.job.count'

    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    type = fields.Selection(string="Location", selection=[('MC', 'MC'), ('EPFC', 'EPFC'), ('SP', 'SP')], required=False, )
    percentage = fields.Float(string="Percentage (%)",  required=False, )


class HrJobLine(models.Model):
    _name = 'hr.job.history'

    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    recruitment_date = fields.Date(string="Recruitment Date", required=False, )
    no_of_recruitment = fields.Integer(string="No of Recruitment", required=False, )
    no_of_hired_employee = fields.Integer(string="No of Hired Employees", required=False, )


class HrJobLevel(models.Model):
    _name = 'hr.employee.classification'

    name = fields.Char(string="Employee Classification", required=True)
    parent_id = fields.Many2one('hr.employee.classification', string="Parent Employee Classification")
    is_parent = fields.Boolean(string="Is Parent?")
    child_id = fields.One2many('hr.employee.classification', 'parent_id',string="Child Employee Classification")
    active = fields.Boolean(string="Active", default=True)
    holiday_paid = fields.Boolean(string="Holiday Paid", default=True)
    code = fields.Char(string="Code", required=False, )
    user_ids = fields.Many2many(comodel_name="res.users", string="Allowed User(s)", )

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive Employee Classification.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code:
                code = record.code
            else:
                code = ''
            # if record.parent_id:
            name = "%s %s" % (name, code)
            result.append((record.id, name))

        return result

    @api.model
    def create(self, vals):
        if vals['name']:
            vals['name'] = vals['name'].upper().strip()
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        return super(HrJobLevel, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            if vals['name']:
                vals['name'] = vals.get('name').upper().strip()
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        return super(HrJobLevel, self).write(vals)

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            count = self.search_count([('parent_id', '=', self.parent_id.id)])
            if count:
                self.holiday_paid = self.parent_id.holiday_paid
                self.code = str(self.parent_id.code) + '{:02}'.format(count + 1)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True)
    is_branch = fields.Boolean(string="Is Branch")
    supervisor_id = fields.Many2one('hr.employee', string="Supervisor", domain="[('supervisor','=',True)]")
    hr_checker_id = fields.Many2one('hr.employee', string="Validator", domain="[('validator','=',True)]")
    hr_approver_id = fields.Many2one('hr.employee', string="Reviewer", domain="[('reviewer','=',True)]")
    municipality_id = fields.Many2one(comodel_name="config.municipality", string="City / Municipality", required=False, help="Fill-in for Public Holidays")
    area_id = fields.Many2one(comodel_name="hr.area", string="Area", required=False, )
    branch_id = fields.Many2one(comodel_name="res.branch", string="Related Branch", required=False)
    inter_company_id = fields.Many2one(comodel_name="res.company", string="Inter-Company", required=False)
    is_operation = fields.Boolean(string="Is Operation")

    @api.model
    def create(self, values):
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        res = super(HrDepartment, self).create(values)
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.company_id:
                code = record.company_id.partner_id.abbreviation
            else:
                code = ''
            if record.parent_id:
                name = "%s / %s" % (record.parent_id.name, name)
            name = "%s [%s]" % (name, code)
            result.append((record.id, name))
        return result

    @api.onchange('parent_id')
    def onchange_parent_department(self):
        self.manager_id = None
        self.supervisor_id = None
        self.hr_checker_id = None
        self.hr_approver_id = None
        self.municipality_id = None
        if self.parent_id:
            res = self.browse(self.parent_id.id)
            if res:
                self.manager_id = res.manager_id.id
                self.supervisor_id = res.supervisor_id.id
                self.hr_checker_id = res.hr_checker_id.id
                self.hr_approver_id = res.hr_approver_id.id
                self.municipality_id = res.municipality_id.id

    # To Apply Approvals to Employees
    @api.multi
    def write(self, values):
        id = self.id
        prev_supervisor_id = self.supervisor_id.id if self.supervisor_id else None
        prev_manager_id = self.manager_id.id if self.manager_id else None
        prev_hr_checker_id = self.hr_checker_id.id if self.hr_checker_id else None
        prev_hr_approver_id = self.hr_approver_id.id if self.hr_approver_id else None
        if not self.env.user.has_group('hrms_employee.group_hr_personnel'):
            raise ValidationError(_("You are not allowed to modified the records of employees. \nPlease contact your administrator!."))
        if 'supervisor_id' in values:
            vals = {}
            if values["supervisor_id"]:
                vals['supervisor_id'] = supervisor_id = values["supervisor_id"]
                where = [['department_id', '=', id]]
                if supervisor_id:
                    where.append(['id','!=',supervisor_id])
                if prev_supervisor_id:
                    where.append(['supervisor_id', 'in',(None,prev_supervisor_id)])
                else:
                    where.append(['supervisor_id', '=',None])
                res_emp = self.env['hr.employee'].search(where)
                for supervisor_res in res_emp:
                    supervisor_res.write(vals)

        if 'manager_id' in values:
            vals = {}
            if values["manager_id"]:
                vals['parent_id'] = manager_id = values["manager_id"]
                where = [['department_id', '=', id]]
                if manager_id:
                    where.append(['id','!=',manager_id])
                if prev_manager_id:
                    where.append(['parent_id', 'in',(None,prev_manager_id)])
                else:
                    where.append(['parent_id', '=',None])
                res_emp = self.env['hr.employee'].search(where)
                for manager_res in res_emp:
                    manager_res.write(vals)

        if 'hr_checker_id' in values:
            vals = {}
            if values["hr_checker_id"]:
                vals['hr_checker_id'] = hr_checker_id = values["hr_checker_id"]
                where = [['department_id', '=', id]]
                if hr_checker_id:
                    where.append(['id','!=',hr_checker_id])
                if prev_hr_checker_id:
                    where.append(['hr_checker_id', 'in',(None,prev_hr_checker_id)])
                else:
                    where.append(['hr_checker_id', '=',None])
                res_emp = self.env['hr.employee'].search(where)
                for checker_res in res_emp:
                    checker_res.write(vals)

        if 'hr_approver_id' in values:
            vals = {}
            if values["hr_approver_id"]:
                vals['hr_approver_id'] = hr_approver_id = values["hr_approver_id"]
                where = [['department_id', '=', id]]
                if hr_approver_id:
                    where.append(['id','!=',hr_approver_id])
                if prev_hr_approver_id:
                    where.append(['hr_approver_id', 'in',(None,prev_hr_approver_id)])
                else:
                    where.append(['hr_approver_id', '=',None])
                res_emp = self.env['hr.employee'].search(where)
                for approver_res in res_emp:
                    approver_res.write(vals)

        return super(HrDepartment, self).write(values)

class HrReligion(models.Model):
    _name = 'hr.religion'

    name = fields.Char(string="Religion")
    active = fields.Boolean(string="Active",default=True)

class EmployeeStageHistory(models.Model):
    _name = 'hr.employee.status.history'
    _description = 'Status History'

    @api.depends('end_date')
    def get_duration(self):
        for each in self:
            if each.end_date and each.start_date:
                duration = fields.Date.from_string(each.end_date) - fields.Date.from_string(each.start_date)
                each.duration = duration.days

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(compute=get_duration, string='Duration(days)')
    state = fields.Selection(emp_stages, string='Stage')
    employee_id = fields.Many2one('hr.employee', invisible=1)


class HrEmployeeHistory(models.Model):

    _name = 'hr.employee.history'
    _description = 'Employee History'
    _order = 'assigned_date desc'

    @api.depends('end_date')
    def get_duration(self):
        for each in self:
            if each.end_date and each.assigned_date:
                duration = fields.Date.from_string(each.end_date) - fields.Date.from_string(each.assigned_date)
                each.duration = duration.days

    assigned_date = fields.Date(string="Start Date")
    end_date = fields.Date(string='End Date')
    company_id = fields.Many2one('res.company',string="Company")
    dept_id = fields.Many2one('hr.department',string="Branch/Department")
    job_id = fields.Many2one('hr.job',string="Job")
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification",
                                            domain="[('is_parent', '=', False)]")
    remarks = fields.Text(string="Remarks")
    state = fields.Selection(emp_stages, string='Stage')
    employee_id = fields.Many2one('hr.employee')
    duration = fields.Integer(compute=get_duration, string='Duration(days)')
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", required=False, )


class HrArea(models.Model):
    _name = 'hr.area'

    name = fields.Char(string="Area", required=False, )
    code = fields.Char(string="Code", required=False, )
    area_line_ids = fields.One2many(comodel_name="hr.department", inverse_name="area_id", string="Branch / Department(s)", required=False, )


class RiceIncentiveMatrix(models.Model):
    _name = 'hr.rice.incentive.matrix'

    minrange = fields.Float(string="Minimum Range", required=False, digits=(12, 3))
    maxrange = fields.Float(string="Maximum Range",  required=False, digits=(12, 3))
    kilos = fields.Float(string="No. of Kilos", required=False, )
    date_effect = fields.Date(string="Date Effective", required=False, default=date.today())
    active = fields.Boolean(string="Active")


class GiftMatrix(models.Model):
    _name = 'hr.gift.check.matrix'

    minrange = fields.Float(string="Minimum Range", required=False, digits=(12, 3))
    maxrange = fields.Float(string="Maximum Range", required=False, digits=(12, 3))
    check = fields.Float(string="Gift Check", required=False)
    spouse = fields.Float(string="Spouse", required=False)
    children = fields.Float(string="Children", required=False)
    date_effect = fields.Date(string="Date Effective", required=False,  default=date.today())
    active = fields.Boolean(string="Active")


class HrEmployeeCompensation(models.Model):
    _name = 'hr.employee.compensation'
    company_id = fields.Many2one('res.company', string="Company")
    shared = fields.Integer(string='Shared %')
    date_effect = fields.Date(string="Effective Date")
    employee_id = fields.Many2one('hr.employee', 'Employee', ondelete='cascade')
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import calendar
import math
# from comm_methods import get_contribution, get_pay_vale, get_contributionec, \
#     get_contributioner, _get_rate, get_previoushdmfcont, get_previousphcont, get_previousssscont

def daterange(start_date, end_date):
    end_date = end_date + timedelta(days=1)
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)
        
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


class HrContractType(models.Model):
    _inherit = 'hr.contract.type'

    regular_employees = fields.Boolean(string="For Regular Employees", default=True)
    code = fields.Char(string="Code", required=False, )
    digits = fields.Integer(string="# of Digits", required=False, )
    code_type = fields.Selection(string="Code Type", selection=[('1', 'At Beginning'), ('2', 'At the End'), ],
                                 required=False, default='1')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char('Contract Reference', required=False,
                       readonly=True, copy=False, default='/')
    wage = fields.Float('Wage', digits=(16, 2), required=True, help="Basic Salary of the employee",track_visibility='onchange')
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False)
    partner_ids = fields.Many2one('res.partner', string="Company", store=True,
                                  domain="[('is_company', '=', True),('owned_company', '=', True)]", related="company_id.partner_id")
    holiday_policy_id = fields.Many2one('hr.holiday.policy','Holiday Policy')
    allocation_compensation = fields.One2many('hr.allocation.compensation','contract_id',string="Allocation Compensation")
    allowance_ids = fields.One2many(comodel_name="hr.contract.allowance", inverse_name="contract_id", string="Allowances", required=False, )
    philhealth_cont = fields.Boolean(string='Philhealth', default=True)
    sss_cont = fields.Boolean(string='SSS', default=True)
    hdmf_cont = fields.Boolean(string='Pagi-ibig', default=True)
    wholdtax_cont = fields.Boolean(string='Withholding Tax', default=True)
    ewa_monthly_due = fields.Float(string="EWA Monthly Dues",  required=False)
    paid_payroll = fields.Selection(PAIDPAYROLL,string='Paid Payroll Type', default='monthly')
    schedule_pay = fields.Selection(SCHEDULEPAY, string='Scheduled Pay', default='semi-monthly')
    municipality_id = fields.Many2one('config.municipality', string="City / Municipality", required=False)
    emp_classification_id = fields.Many2one('hr.employee.classification', string="Employee Classification", domain="[('parent_id', '=', False)]")
    employment_type = fields.Selection(string="Personal Action",
                                       selection=[('initial', 'Initial Hire'),
                                                  ('confirm', 'Confirmation of Regular Employment'),
                                                  ('rehire', 'Re-Hire'),
                                                  ('promote', 'Promotion'),
                                                  ('position', 'Change in Position'),
                                                  ('separate', 'Separation'),
                                                  ('others', 'Others')], required=False,)
    annual_struct_id = fields.Many2one('hr.payroll.structure', string='Annual Structure')
    annual_structure = fields.Selection(string='Annual Structure', default='annually',
                                        selection=[('semi-annually', 'Semi-annually'), ('annually', 'Annually')])
    cola_id = fields.Many2one(comodel_name="hr.setup.cola", string="Cola")
    date_regular = fields.Date(string="Actual Regular Date", required=False)
    allowance = fields.Float(string="Allowance",  required=False, )
    is_dynamic_schedule = fields.Boolean(string="Dynamic Schedule")
    previous_contract_id = fields.Many2one(comodel_name="hr.contract", string="Previous Contract", required=False)
    salary_changes_type = fields.Selection(string="Salary Changes Type", selection=[('none', 'N/A'),
                                                                                    ('promotion', 'Promotional Increase'),
                                                                                    ('merit', 'Merit Increase'),
                                                                                    ('adjust', 'Adjustment'),
                                                                                    ('others', 'Others')], required=False)
    separation_type = fields.Selection(string="Separation Type",
                                       selection=[('none', 'N/A'), ('retire', 'Retirement'), ('death', 'Death'),
                                                  ('resign', 'Resignation'), ('dismiss', 'Dismissal')],
                                       required=False, default='none')
    change_position_type = fields.Selection(string="Change of Position/Assignment",
                                            selection=[('none', 'N/A'),
                                                       ('transfer', 'Transfer'),
                                                       ('reclassify', 'Reclassification'),
                                                       ('change', 'Change of Job Title'),
                                                       ('others', 'Others')], required=False, default='none')
    initiated_by_id = fields.Many2one(comodel_name="hr.employee", string="Initiated By", required=False,
                                      related="employee_id.supervisor_id", store=True)
    recommended_by_id = fields.Many2one(comodel_name="hr.employee", string="Recommended By", required=False,
                                        related="employee_id.parent_id", store=True)
    evaluated_by_id = fields.Many2one(comodel_name="hr.employee", string="Evaluated By", required=False)
    approved_by_id = fields.Many2many(comodel_name="hr.employee", string="Approved By", required=False)
    identification_id = fields.Char(string="Identification No.", required=False, )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id
            self.department_id = self.employee_id.department_id
            self.company_id = self.employee_id.company_id
            self.emp_classification_id = self.employee_id.emp_classification_id if self.employee_id.emp_classification_id else self.employee_id.job_id.emp_classification_id
            if self.employee_id.department_municipality_id:
                self.municipality_id = self.employee_id.department_municipality_id
            self.struct_id = self.env['hr.payroll.structure'].browse(self.env.ref('hr_payroll.structure_base').id)
            if self.employee_id.state == 'employment':
                self.ewa_monthly_due = 50.0
            # if self.employee_id.compensation_ids:
            #     lines = []
            #     for line in self.employee_id.compensation_ids:
            #         values = {
            #             'company_ids': line.company_id.partner_id.id,
            #             'shared': line.shared,
            #             'date_effect': line.date_effect
            #         }
            #         lines.append((0, 0, values))
            #     self.allocation_compensation = lines

    @api.onchange('is_dynamic_schedule')
    def _onchange_is_dynamic_schedule(self):
        result = {}
        if self.is_dynamic_schedule:
            result['domain'] = {'working_hours': [('dynamic_sched', '=', True)]}
        return result

    @api.multi
    def action_open(self):
        employee = self.env['hr.employee'].browse(self.employee_id.id)
        # compensation = self.env['hr.allocation.compensation']
        if employee:
            # if employee.compensation_ids:
            #     for comp in employee.compensation_ids:
            #         vals = {
            #             'company_ids': comp.company_id.partner_id.id,
            #             'contract_id': self.id,
            #             'shared': comp.shared,
            #             'date_effect': comp.date_effect
            #         }
            #         compensation.create(vals)
            # else:
            #     raise ValidationError(_("Please make the HR a head count for the employee"))
            employee.update({
                    'employee_status_id': self.type_id.id,
                    'department_id': self.department_id.id,
                    'job_id': self.job_id.id,
                    'emp_classification_id':  self.emp_classification_id.id,
                    'hr_checker_id': self.department_id.hr_checker_id.id,
                    'hr_approver_id': self.department_id.hr_approver_id.id,
                    'parent_id': self.department_id.manager_id.id,
                    'supervisor_id':  self.department_id.supervisor_id.id,
                    'calendar_id': self.working_hours,
                    'holiday_paid': self.emp_classification_id.holiday_paid
            })

            # if employee.state == 'joined' and self.employment_type == 'initial':
            #     employee.start_probationary()
            # if employee.state == 'probationary' and self.employment_type == 'confirm':
            #     employee.set_as_employee()
            # if employee.state == 'employment' and self.employment_type == 'separate':
            #     employee.relieved()

            # previous_contract = self.search([('id', '!=', self.id), ('employee_id', '=', self.employee_id.id),
            #                                  ('state', 'in', ['draft', 'open']), ('date_end', '=', False)], order='dat_start desc', limit=1)
            if self.previous_contract_id:
                prev = self.previous_contract_id
                prev.write({'date_end': date.today(), 'state': 'close'})
            self.write({'state': 'open'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('employment_type', 'employee_id', 'date_start')
    def _onchange_employment_type(self):
        if self.employment_type and self.date_start and self.employee_id:
            date_start = fields.Datetime.from_string(self.date_start)
            date_hired = fields.Datetime.from_string(self.employee_id.date_hired)
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

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_expired(self):
        self.write({'state': 'close', 'date_end': date.today()})

    @api.onchange('employee_id')
    def _onchange_partner_id(self):
        if self.employee_id:
            self.partner_ids = self.employee_id.company_id.partner_id
            self.working_hours = self.employee_id.calendar_id
            self.municipality_id = self.employee_id.department_id.municipality_id

    # @api.multi
    # def _get_previous_contract(self):
    #     for record in self:
    #         if record.employee_id:
    #             prev_contract = self.env['hr.contract'].search([('id', '!=',record.id),
    #                                                             ('date_start', '<=', record.date_start),
    #                                                             ('employee_id', '=', record.employee_id.id),
    #                                                             ('state', 'in', ['draft', 'open'])], order='date_start desc', limit=1)
    #             if prev_contract:
    #                 record.previous_contract_id = prev_contract.id

    @api.multi
    def _president_signatory(self, approve):
        if approve:
            result = self.env['hr.employee'].browse(approve)
            if result:
                return result

    @api.multi
    def write(self, values):
        if not self.env.user.has_group('hrms_employee.group_hr_contract_payroll'):
            raise ValidationError(_("You are not allowed to modified the records of contracts. \nPlease contact your administrator!."))
        res = super(HrContract, self).write(values)
        if res:
            previous_contract_id = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id)], limit=1, order='date_start desc')
            if previous_contract_id:
                if previous_contract_id.date_start < self.date_start:
                    values['previous_contract_id'] = previous_contract_id.id
                    date_end = datetime.strptime(self.date_start, '%Y-%m-%d').date()
                    previous_contract_id.write({'state': 'close', 'date_end': date_end - relativedelta(days=1)})
        return res

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('hrms_employee.group_hr_contract_payroll'):
            raise ValidationError(_("You are not allowed to modified the records of contracts. \nPlease contact your administrator!."))
        if vals.get('number', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('contract.ref')
        if 'identification_id' in vals:
            identification_id = vals['identification_id']
            emp_id = self.env['hr.employee'].search([['identification_id', '=', identification_id]], limit=1)
            if emp_id:
                vals['employee_id'] = emp_id.id
                if emp_id.state == 'employment' and emp_id.company_id.partner_id.abbreviation not in ('RBN', 'CARE'):
                    vals['ewa_monthly_due'] = 50.0
        res = super(HrContract, self).create(vals)
        if res:
            res_id = self.browse(res.id)
            employee_id = self.env['hr.employee'].browse(vals['employee_id'])
            previous_contract_id = self.search([('employee_id', '=', vals['employee_id']), ('id', '!=', res_id.id)], limit=1, order='date_start desc')
            vals['job_id'] = res_id.employee_id.job_id.id
            vals['department_id'] = res_id.employee_id.department_id.id
            vals['company_id'] = res_id.employee_id.company_id.id
            vals['emp_classification_id'] = res_id.employee_id.emp_classification_id.id if res_id.employee_id.emp_classification_id.id else res_id.employee_id.job_id.emp_classification_id.id
            if res_id.employee_id.department_municipality_id:
                vals['municipality_id'] = res_id.employee_id.department_municipality_id.id
            if res_id.employee_id.employee_status_id:
                vals['type_id'] = res_id.employee_id.employee_status_id.id
            if previous_contract_id:
                if previous_contract_id.date_start < vals['date_start']:
                    vals['previous_contract_id'] = previous_contract_id.id
                    date_end = datetime.strptime(vals['date_start'], '%Y-%m-%d').date()
                    previous_contract_id.write({'state': 'close', 'date_end': date_end - relativedelta(days=1)})
            # for compensation in employee_id.compensation_ids:
            #     values = {
            #         'contract_id': res_id.id,
            #         'company_ids': compensation.company_id.partner_id.id,
            #         'shared': compensation.shared,
            #         'date_effect': compensation.date_effect
            #     }
            #     self.env['hr.allocation.compensation'].create(values)
            # res._get_previous_contract()
        return res

    @api.multi
    def count_contract_of_days(self):
        result = 0.0
        if self.working_hours:
            days = []
            for line in self.working_hours.attendance_ids:
                if int(line.dayofweek) not in days:
                    days.append(int(line.dayofweek))
            start = date(date.today().year, 01, 01)
            end = date(date.today().year, 12, 31)
            for dates in daterange(start, end):
                if dates.weekday() in days:
                    result += 1
        return result
        
    def basic_wage(self, payslip, worked_days):
        payslip_date = datetime.strptime(payslip.date_from, '%Y-%m-%d').date()
        emp_sched_pay = self.schedule_pay
        emp_paid_pay = self.paid_payroll
        result = 0.00
        date_start = datetime.strptime(self.date_start, '%Y-%m-%d').date()
        days_per_year = 313
        if self.partner_ids.days_per_year:
            days_per_year = self.partner_ids.days_per_year
        if date_start <= payslip_date:
            salary = self.wage
            if emp_paid_pay == 'daily':
                if emp_sched_pay == 'weekly':
                    if worked_days:
                        # result = worked_days.ATTN.number_of_days * salary
                        result = (worked_days.WORK100.number_of_days * salary)
                elif emp_sched_pay == 'semi-monthly':
                    result = (worked_days.WORK100.number_of_days * salary)
                elif emp_sched_pay == 'monthly':
                    result = (worked_days.WORK100.number_of_days * salary)
            else:
                if emp_sched_pay == 'monthly':
                    result = salary
                elif emp_sched_pay == 'semi-monthly':
                    result = salary / 2
                elif emp_sched_pay == 'weekly':
                    if worked_days:
                        emp_wage = round((salary * 12) / days_per_year, 2)
                        result = (worked_days.WORK100.number_of_days * emp_wage)
        else:
            previous_contract = self.search([('id', '!=', self.id), ('employee_id', '=', self.employee_id.id)],
                                            order='date_start desc', limit=1)
            salary = previous_contract.wage
            if emp_paid_pay == 'daily':
                if emp_sched_pay == 'weekly':
                    if worked_days:
                        result = (worked_days.WORK100.number_of_days * salary)
                elif emp_sched_pay == 'semi-monthly':
                    result = salary * 15
                elif emp_sched_pay == 'monthly':
                    result = salary * 30
            else:
                if emp_sched_pay == 'monthly':
                    result = salary
                elif emp_sched_pay == 'semi-monthly':
                    result = salary / 2
                elif emp_sched_pay == 'weekly':
                    if worked_days:
                        emp_wage = round((salary * 12) / days_per_year, 2)
                        result = (worked_days.WORK100.number_of_days * emp_wage)
        return round(result, 2)

    # employee philhealth
    def phcontribution(self,worked_days, payslip):
        cont_for = 'philhealth'
        share_for = 'eeshare'
        emp_sched_pay = self.schedule_pay
        rpartner = self.partner_ids.id
        table = 'hr.philhealth.table'
        result = 0.00
        code = 'PHEE'

        if self.philhealth_cont:
            # comp_partner = self.env['res.partner'].search([('id', '=', rpartner)])
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(phic, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(phic, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = phic - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(phic, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(phic, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = phic - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

        result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'PHEE', round(result, 2)

        return round(result, 2)

    # employee sss
    def ssscontribution(self, worked_days, payslip):
        cont_for = 'sss'
        share_for = 'eeshare'
        emp_sched_pay = self.schedule_pay
        rpartner = self.partner_ids.id
        table = 'hr.sss.table'
        code = 'SSSEE'
        result = 0.00
        if self.sss_cont:
            # comp_partner = self.env['res.partner'].search([('id', '=', rpartner)])
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(sss, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(sss, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(sss, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(sss, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

        result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'SSSEE', round(result, 2)

        return round(result, 2)

    # employee hdmf
    def hdmfcontribution(self, worked_days,payslip):
        cont_for = 'hdmf'
        share_for = 'eeshare'
        emp_wage = self.basic_wage(payslip, worked_days)
        rpartner = self.partner_ids.id
        emp_sched_pay = self.schedule_pay
        table = 'hr.hdmf.table'
        code = 'HDMFEE'
        result = 0.00
        if self.hdmf_cont:
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    hdmf = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(hdmf, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(hdmf, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    hdmf = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(hdmf, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(hdmf, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contribution(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

        result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'HDMFEE', round(result, 2)
        return round(result, 2)

    # employer philhealth
    def phcompanycont(self, worked_days, payslip):
        cont_for = 'philhealth'
        share_for = 'ershare'
        emp_sched_pay = self.schedule_pay
        table = 'hr.philhealth.table'
        code = 'PHER'
        result = 0.0
        if self.philhealth_cont:
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    print schedpay
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(phic, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(phic, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = phic - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    result = contr
                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    print schedpay
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(phic, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(phic, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = phic - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    phic = round(results / schedpay, 2)
                    contr = round(phic / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'PHER', round(result, 2)
        return round(result,2)

    # ec_er and ershare
    def sssercompanycont(self, worked_days, payslip):
        cont_for = 'sss'
        share_for = 'ershare'
        emp_sched_pay = self.schedule_pay
        table = 'hr.sss.table'
        code = 'SSSER'
        result = 0.0
        if self.sss_cont:
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(sss, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(sss, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr
                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(sss, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(sss, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr
                else:
                    result = 0.00

            result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'SSSER', round(result, 2)
        return round(result, 2)

    def ssseccompanycont(self, worked_days, payslip):
        emp_sched_pay = self.schedule_pay
        table = 'hr.sss.table'
        code = 'SSSEC'
        result = 0.0
        if self.sss_cont:
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        contr = round(sss, 2)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        contr = round(sss, 2)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00
            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    sss = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        contr = round(sss, 2)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        contr = round(sss, 2)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributionec(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

        print 'SSSEC', round(result, 2)
        return round(result, 2)

    # hdmf
    def hdmfercompanycont(self, worked_days, payslip):
        cont_for = 'hdmf'
        share_for = 'ershare'
        emp_wage = self.basic_wage(payslip, worked_days)
        emp_sched_pay = self.schedule_pay
        table = 'hr.hdmf.table'
        code = 'HDMFER'
        rpartner = self.partner_ids.id

        # if worked_days.ATTN.number_of_days == 0.00:
        #     result = 0.00
        # else:
        # comp_partner = self.env['res.partner'].search([('id', '=', rpartner)])
        result = 0.0
        if self.hdmf_cont:
            if self.paid_payroll == 'monthly':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    hdmf = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(hdmf, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(hdmf, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            if self.paid_payroll == 'daily':
                if emp_sched_pay == 'weekly':
                    # date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
                    # schedpay = len([1 for i in calendar.monthcalendar(date_payment.year, date_payment.month) if
                    #                 i[int(date_payment.weekday())] != 0])
                    schedpay = 4
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    hdmf = round(results / schedpay, 2)
                    if schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
                        rounds = 2
                        contr = round(hdmf, rounds)
                        resultz = results - (contr * (schedpay - 1))
                        additional_cont = results - (self.get_additional_contribution(payslip, worked_days, schedpay, code) + resultz)
                        result = resultz + additional_cont
                    else:
                        rounds = 0
                        contr = round(hdmf, rounds)
                        result = contr

                elif emp_sched_pay == 'semi-monthly':
                    schedpay = 2
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    if payslip.payslip_run_id.hr_period_id.vale_period == 2:
                        result = contr
                    else:
                        result = results - contr

                elif emp_sched_pay == 'monthly':
                    schedpay = 1
                    results = self.get_contributioner(payslip, worked_days, schedpay, table)
                    contr = round(results / schedpay, 2)
                    result = contr

                else:
                    result = 0.00

            result = result + self.getcontributionadjustment(payslip, cont_for, share_for)
        print 'HDMFER', round(result, 2)
        return round(result, 2)

    def get_additional_contribution(self, payslip, worked_days, schedpay, code):
        result = 0.0
        weekly_wage = self.get_gross_wage(payslip, worked_days)
        if weekly_wage > 0.0:
            cont = True
        else:
            cont = False
        if cont and schedpay == payslip.payslip_run_id.hr_period_id.vale_period:
            date_payment = datetime.strptime(payslip.payslip_run_id.date_payment, '%Y-%m-%d')
            date_start = date(date_payment.year, date_payment.month, 01)
            date_end = date(date_payment.year, date_payment.month, calendar.monthrange(date_payment.year, date_payment.month)[1])
            all_contributions = self.env['hr.payslip'].search([('id', '!=', payslip.id),
                                                               ('employee_id', '=', self.employee_id.id),
                                                               ('payslip_run_id.date_payment', '>=', date_start),
                                                               ('payslip_run_id.date_payment', '<=', date_end)])
            if all_contributions:
                for all in all_contributions:
                    for line in all.line_ids:
                        if line.code == code:
                            result += line.total
        return round(result, 2)

    def compute_net_payslip(self):
        result = True
        if self.paid_payroll == 'daily' and self.schedule_pay == 'weekly':
            result = False
        return result

    def getcontributionadjustment(self, payslip, cont_for, share_for):
        emp_ids = self.employee_id.id
        date_from = datetime.strptime(payslip.date_from, "%Y-%m-%d").date()
        date_to = datetime.strptime(payslip.date_to, "%Y-%m-%d").date()

        chklist = self.env['hr.contribution.adjustment.list'].search([('datefrom','<=',date_from),
                                                                      ('dateto','>=',date_to),
                                                                      ('state','=','done'),
                                                                      ('contribution_for','=',cont_for),
                                                                      ('share','=',share_for)])
        if chklist == '':
            result = 0.00
        else:
            result = 0

            for xx in chklist:
                for x in xx.emp_list_ids:
                    list = x.id
                    emp_list = self.env['hr.contribution.adjustment'].search([('id', '=', list),
                                                                              ('emp_id', '=', emp_ids)])

                    result = result + emp_list.amount

        return round(result, 2)

    # =============================withholdingtax=============================
    # annual tax

    def withholdingtax(self, payslip, worked_days):
        dfrom = datetime.strptime(payslip.date_from, "%Y-%m-%d").date()
        dto = datetime.strptime(payslip.date_to, "%Y-%m-%d").date()
        date_from = dfrom.strftime("%Y-01-01")
        date_to = dto.strftime("%Y-%m-%d")
        curyear = dto.year
        contributions = 0
        result = 0.0
        if self.wholdtax_cont:
            employee_id = self.employee_id.id
            clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
            clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
            clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
            clause_final = [('employee_id', '=', employee_id), '|', '|'] + clause_1 + clause_2 + clause_3
            contract_ids = self.env['hr.contract'].sudo().search(clause_final)
            # end_of_month = 0
            # start_of_months = 0
            # salary = 0
            # contract_id = None
            if contract_ids:
                payslips = self.env['hr.payslip'].search([('id', '!=', payslip.id), ('set_as_regular_payroll', '=', True),
                                                          ('employee_id', '=', employee_id),
                                                          ('date_from', '>=', date_from), ('date_to', '<=', date_to)])

                basic = 0.0
                sss_contribution = 0.0
                hdmf_contribution = 0.0
                phic_contribution = 0.0
                for contract in contract_ids:
                    if contract.paid_payroll == 'monthly':
                        salary_wage = contract.wage
                    else:
                        salary_wage = (contract.wage * contract.partner_ids.days_per_year) / 12.0
                    get_date_start = datetime.strptime(contract.date_start, "%Y-%m-%d").date()
                    if contract.date_end:
                        get_date_end = datetime.strptime(contract.date_end, "%Y-%m-%d").date()
                        end_of_the_year = date(curyear, 12, 31)
                        if len(contract_ids) == 1 and end_of_the_year > get_date_end:
                            get_date_end = date(curyear, 12, 31)

                    else:
                        get_date_end = date(curyear, 12, 31)
                    old_date_start_month = get_date_start.month
                    old_date_start_year = get_date_start.year
                    if old_date_start_year != curyear:
                        old_date_start_month = 1
                        if contract.date_end:
                            old_date_end_month = get_date_end.month
                        else:
                            old_date_end_month = 12
                    else:
                        if contract.date_end:
                            old_date_end_month = get_date_end.month
                        else:
                            old_date_end_month = 12

                    # end_of_month = old_date_end_month
                    # salary = salary_wage
                    # start_of_months = old_date_start_month
                    # contract_id = contract

                    get_old_date_count = (old_date_end_month - old_date_start_month) + 1
                    basic += salary_wage * get_old_date_count
                    beginning_month = date(old_date_start_year, old_date_start_month, get_date_start.day)
                    ending_month = date(old_date_start_year, old_date_end_month, get_date_end.day)

                    for month_of_year in range(beginning_month.month, ending_month.month + 1):
                        end = date(curyear, month_of_year, calendar.monthrange(curyear, month_of_year)[1])
                        sss_contribution += contract.get_previousssscont(end, salary_wage)
                        hdmf_contribution += contract.get_previoushdmfcont(end, salary_wage)
                        phic_contribution += (contract.get_previousphcont(end, salary_wage))
                # if end_of_month != 12:
                #     end_of_months = 12 - end_of_month
                #     get_old_date_counts = (end_of_months - start_of_months) + 1
                #     basic += salary * get_old_date_counts
                #     for month_of_year in range(start_of_months, end_of_months + 1):
                #         end = date(curyear, month_of_year, calendar.monthrange(curyear, month_of_year)[1])
                #         sss_contribution += contract_id.get_previousssscont(end, salary)
                #         hdmf_contribution += contract_id.get_previoushdmfcont(end, salary)
                #         phic_contribution += (contract_id.get_previousphcont(end, salary))
                contributions = sss_contribution + hdmf_contribution + phic_contribution
                absences = self.getabsence(payslip)
                premium_pay = 0
                adjustment = 0.0
                holidays = self.env['hr.payslip.holidays.employee'].sudo().search([('employee_id', '=', employee_id),
                                                                                    ('date_payment', '>=', date_from),
                                                                                    ('date_payment', '<=', date_to)])

                if holidays:
                    for holiday in holidays:
                        premium_pay += holiday.regular_premium + holiday.special_premium
                adjustments = self.env['hr.adjustment.employee'].sudo().search([('emp_id', '=', employee_id),
                                                                                 ('payment_date', '>=', date_from),
                                                                                 ('payment_date', '<=', date_to)])

                if adjustments:
                    for adj in adjustments:
                        if adj.adjustment_type_id.is_taxable:
                            adjustment += adj.amount
                overtime = self._get_overtime(payslip)
                previous_withholding_tax = 0.0
                if payslip.adjustment_list_ids:
                    for adj in payslip.adjustment_list_ids:
                        if adj.adjustment_type_id.is_taxable:
                            adjustment += adj.amount
                if payslips:
                    for p in payslips:
                        for line in p.line_ids:
                            if line.code == 'OT':
                                overtime += line.total
                            if line.code == 'ABS':
                                absences += line.total
                            if line.code == 'WHTAX':
                                previous_withholding_tax += line.total

                total_wage = (((basic - absences) + (premium_pay + adjustment + overtime)) - contributions)
                print (basic - absences, premium_pay, adjustment, overtime, contributions, total_wage)
                tax_schedule = self.env['hr.tax.annual'].sudo().search([('minrange', '<=', total_wage),
                                                                        ('maxrange', '>=', total_wage),
                                                                        ('dateeffect', '<=', date_to)])
                if tax_schedule:
                    print tax_schedule.rate, total_wage
                    if tax_schedule.rate > 0.00:
                        annual_rate = tax_schedule.rate / 100.00
                        annual_fix_tax = tax_schedule.fixed_tax
                    # check if annual wage is less than 250,000 automatic 0.00
                    # if total_wage >= 250000.00:
                        total_less_base_range = total_wage - round(tax_schedule.minrange, 2)
                        total_time_rate = total_less_base_range * annual_rate
                        total_add_base = total_time_rate + annual_fix_tax

                        tax_still_due = total_add_base - previous_withholding_tax
                        #     divided by remaining # of vales
                        remain_vales = self.getremainingvale(payslip)
                        print 'REMVALES', remain_vales
                        result = tax_still_due / remain_vales

                else:
                    result = 0.00

        print 'WHTAX', round(result, 2)
        if result < 0.0000:
            result = 0.00
        return round(result, 2)

    def getremainingvale(self, payslip):
        fiscal_year = payslip.payslip_run_id.hr_period_id.fiscalyear_id
        actual_period = 0
        if fiscal_year:
            actual_period = len(fiscal_year.period_ids)
        result = (actual_period - payslip.payslip_run_id.hr_period_id.number) + 1
        return result

    def seventy_percent_gross(self, payslip, worked_days):
        addititions = self.basic_wage(payslip, worked_days) + self._get_allowance(payslip, worked_days) + \
                      self.getadjustment(payslip) + self._get_regular_holiday(payslip) + \
                      self._get_special_holiday(payslip)
        subtractions = self.getabsence(payslip)
        gross = (addititions - subtractions)
        print (gross)
        contribution = self.hdmfcontribution(worked_days, payslip) + self.ssscontribution(worked_days, payslip) + self.phcontribution(worked_days, payslip)
        loans = self.get_loans(payslip)
        print ("LOANS", loans)
        if loans:
            result = (gross - (contribution + loans)) * (70.0 / 100.0)
        else:
            result = (gross - contribution) * (70.0 / 100.0)
        return result

    # =============================end of withholdingtax=============================
    # get from employee

    def getdeduction(self, payslip, worked_days):
        result = 0.0
        emp_ids = self.env['hr.deduction.employee'].sudo().search([('emp_id', '=', self.employee_id.id),
                                                                   ('payment_date', '<=', payslip.date_to),
                                                                   ('payment_date', '>=', payslip.date_from)], order='id')
        seventy_percent = self.seventy_percent_gross(payslip, worked_days)
        if emp_ids and seventy_percent > 0.0:
            if self.schedule_pay == 'monthly':
                add_days = relativedelta(months=1)
            elif self.schedule_pay == 'semi-monthly':
                add_days = relativedelta(days=16)
            else:
                add_days = relativedelta(days=7)

            deduction = 0.0
            for emp_ded_ids in emp_ids:
                date_payment = datetime.strptime(emp_ded_ids.payment_date, '%Y-%m-%d').date() + add_days
                remaining_balance = seventy_percent - deduction
                if remaining_balance > 0.0:
                    if remaining_balance > emp_ded_ids.actual_deduction:
                        result += emp_ded_ids.actual_deduction
                        deduction += emp_ded_ids.actual_deduction
                        installment = self.env['hr.deduction.installment.line'].browse(emp_ded_ids.hr_deduction_installment_line_id.id)
                        if installment:
                            installment.write({'payslip_id': payslip.id, 'paid': True})
                        emp_ded_ids.write({'payroll_ded_id': payslip.id, 'paid': True})
                    else:
                        actual_deduction = emp_ded_ids.actual_deduction - remaining_balance
                        deduction += remaining_balance
                        result += actual_deduction
                        unsettled_deduction = emp_ded_ids.actual_deduction - actual_deduction
                        emp_ded_ids.write({'payroll_ded_id': payslip.id, 'paid': True, 'amount': actual_deduction,
                                           'unsettled_deduction': unsettled_deduction, 'ud_payment_date': date_payment})

                else:
                    emp_ded_ids.write({'paid': False, 'amount': 0.0,  'unsettled_deduction': emp_ded_ids.actual_deduction,
                                       'ud_payment_date': date_payment})

            print "NETDED", result
        return round(result, 2)

    def getadjustment(self, payslip):
        result = 0.0
        adj_list = payslip.adjustment_list_ids
        if adj_list:
            for ids in adj_list:
                if ids.paid:
                    result += ids.amount
                print 'Adjustment'
        return round(result, 2)

    def get_loans(self, payslip):
        result = 0.0
        loan_ids = self.env['hr.loan.line'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                           ('paid_date', '>=', payslip.date_from),
                                                           ('paid_date', '<=', payslip.date_to)])
        print loan_ids

        for loan in loan_ids:
            if loan.loan_type_id.set_as_priority:
                result += loan.paid_amount
        # loan_list = payslip.loan_ids
        # if loan_list:
        #     for ids in loan_list:
        #         if ids.paid:
        #             result += ids.amount
        print ('LOAN', result)
        return round(result, 2)

#     how to get absence

    def getabsence(self, payslip):
        start_date = datetime.strptime(payslip.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(payslip.date_to, '%Y-%m-%d')
        absences = self.env['hr.absences.employee'].search([('employee_id', '=', self.employee_id.id),
                                                            ('absent_list_id.date_start', '=', start_date),
                                                            ('absent_list_id.date_end', '=', end_date),
                                                            ('paid', '=', False)])
        result = 0.00
        if absences:
            for absent in absences:
                result += absent.amount

        return round(result, 2)

    def get_undeducted_absence(self, payslip):
        start_date = datetime.strptime(payslip.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(payslip.date_to, '%Y-%m-%d')
        undeducted_absences = self.env['hr.absences.employee'].search([('employee_id', '=', self.employee_id.id),
                                                                ('absent_list_id.date_start', '=', start_date),
                                                                ('absent_list_id.date_end', '=', end_date),
                                                                ('paid', '=', False)])
        if undeducted_absences:
            result = undeducted_absences.undeducted_absences
        else:
            result = 0.00

        return round(result, 2)

    def _get_regular_holiday(self, payslip):
        start_date = datetime.strptime(payslip.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(payslip.date_to, '%Y-%m-%d')
        holidays = self.env['hr.payslip.holidays.employee'].search([('employee_id', '=', self.employee_id.id),
                                                                ('holiday_list_id.date_start', '=', start_date),
                                                                ('holiday_list_id.date_end', '=', end_date),
                                                                ('paid', '=', False)])
        result = 0.00
        if holidays:
            for holiday in holidays:
                    result += holiday.regular_premium

        return round(result, 2)

    def _get_special_holiday(self, payslip):
        start_date = datetime.strptime(payslip.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(payslip.date_to, '%Y-%m-%d')
        holidays = self.env['hr.payslip.holidays.employee'].search([('employee_id', '=', self.employee_id.id),
                                                                    ('holiday_list_id.date_start', '=', start_date),
                                                                    ('holiday_list_id.date_end', '=', end_date),
                                                                    ('paid', '=', False)])
        result = 0.00
        if holidays:
            for holiday in holidays:
                result += holiday.special_premium

        return round(result, 2)

    def _get_overtime(self, payslip):
        start_date = datetime.strptime(payslip.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(payslip.date_to, '%Y-%m-%d')
        overtime = self.env['hr.payslip.overtime.employee'].search([('employee_id', '=', self.employee_id.id),
                                                                    ('overtime_list_id.date_start', '=', start_date),
                                                                    ('overtime_list_id.date_end', '=', end_date),
                                                                    ('paid', '=', False)])
        result = 0.00
        if overtime:
            for ot in overtime:
                result += ot.amount

        return round(result, 2)

    # EWA
    def _get_ewa_monthly_due(self, payslip):
        result = 0.0
        employee = self.employee_id
        if employee.state == 'employment':
            date_from = datetime.strptime(payslip.date_from, "%Y-%m-%d").date()
            date_to = datetime.strptime(payslip.date_to, "%Y-%m-%d").date()
            ewa_line = self.env['hr.ewa.line'].search([('employee_id', '=', employee.id), ('active', '=', True)], limit=1)
            if date_from.day >= 1 and date_to.day <= 15 and ewa_line:
                result = float(ewa_line.paid_amount)
            else:
                result = 0.00
        print 'EWA', round(result, 2)
        return round(result, 2)

    # COLA
    def _get_cola(self, payslip, worked_days):
        result = 0.00
        if self.cola_id:
            cola = self.cola_id
            date_from = datetime.strptime(payslip.date_from, '%Y-%m-%d').date()
            cola_effect = datetime.strptime(cola.date_effect, '%Y-%m-%d').date()
            days = self.count_contract_of_days()
            if cola_effect <= date_from:
                if payslip.contract_id.schedule_pay == 'weekly':
                    working_days = (self.basic_wage(payslip, worked_days) / self.wage)
                else:
                    working_days = worked_days.WORK100.number_of_days
                result = ((cola.cola * 12) / days) * working_days

        print 'COLA', result
        return round(result, 2)

    def _get_allowance(self, payslip, worked_days):
        payslip_date = datetime.strptime(payslip.date_from, '%Y-%m-%d').date()
        emp_sched_pay = self.schedule_pay
        emp_paid_pay = self.paid_payroll
        result = 0.00
        date_start = datetime.strptime(self.date_start, '%Y-%m-%d').date()
        if date_start <= payslip_date:
            allowance = self.allowance
            if emp_paid_pay == 'daily':
                if emp_sched_pay == 'weekly':
                    if worked_days:
                        # result = worked_days.ATTN.number_of_days * allowance
                        result = (self.basic_wage(payslip, worked_days) / self.wage) * allowance
                elif emp_sched_pay == 'semi-monthly':
                    result = allowance * 15
                elif emp_sched_pay == 'monthly':
                    result = allowance * 30
            else:
                if emp_sched_pay == 'monthly':
                    result = allowance
                elif emp_sched_pay == 'semi-monthly':
                    result = allowance / 2
                elif emp_sched_pay == 'weekly':
                    if worked_days:
                        days_per_year = 313
                        if self.partner_ids.days_per_year:
                            days_per_year = self.partner_ids.days_per_year
                        emp_wage = round((self.wage * 12) / days_per_year, 2)
                        result = (worked_days.WORK100.number_of_days * emp_wage)
        return round(result, 2)


class HrContractAllowance(models.Model):
    _name = 'hr.contract.allowance'

    contract_id = fields.Many2one('hr.contract', 'Contract Ref.', ondelete='cascade')
    name = fields.Char(string="Name", required=False, )
    allowance = fields.Float(string="Allowance",  required=False, )
    date_start = fields.Date(string="Date Start", required=False, )
    date_end = fields.Date(string="Date End", required=False)




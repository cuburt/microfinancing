from odoo import models, api, fields, _
from datetime import date,datetime
from dateutil.relativedelta import relativedelta


class HRMemorandumAgreement(models.TransientModel):
    _name = 'hr.memorandum.agreement'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False)
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Signatory", required=False, domain=[('form_signatory', '=', True)])
    signatory_job_id = fields.Char( string="Position", required=False, )
    salary = fields.Float(string="Salary",  required=False, )
    emp_valid_id = fields.Selection(string="Employee Valid ID", selection=[('TIN', 'TIN'), ('SSS', 'SSS'),
                                                                           ('PHILHEALTH', 'PHILHEALTH'), ('HDMF', 'HDMF'),
                                                                           ('OTHERS', 'OTHERS')], required=False, )
    emp_valids = fields.Char(string="Employee ID", required=False, )
    emp_valid_details = fields.Char(string="Details", required=False, )
    signatory_valid_id = fields.Selection(string="Signatory Valid ID", selection=[('TIN', 'TIN'), ('SSS', 'SSS'),
                                                                           ('PHILHEALTH', 'PHILHEALTH'),
                                                                           ('HDMF', 'HDMF'),
                                                                           ('OTHERS', 'OTHERS')], required=False, )
    signatory_valids = fields.Char(string="Signatory ID", required=False, )
    signatory_valid_details = fields.Char(string="Signatory", required=False, )

    @api.onchange('emp_valid_id', 'employee_id')
    def _onchange_emp_valid_ids(self):
        if self.emp_valid_id:
            if self.emp_valid_id != 'OTHERS':
                self.emp_valids = self.emp_valid_id
            else:
                self.emp_valids = ""
            if self.emp_valid_id == 'TIN':
                self.emp_valid_details = self.employee_id.tin_no
            elif self.emp_valid_id == 'SSS':
                self.emp_valid_details = self.employee_id.sss_no
            elif self.emp_valid_id == 'PHILHEALTH':
                self.emp_valid_details = self.employee_id.ph_no
            elif self.emp_valid_id == 'HDMF':
                self.emp_valid_details = self.employee_id.hdmf_no
            else:
                self.emp_valid_details = ""

    @api.onchange('signatory_valid_id', 'signatory_id')
    def _onchange_signatory_valid_ids(self):
        if self.signatory_valid_id:
            if self.signatory_valid_id != 'OTHERS':
                self.signatory_valids = self.signatory_valid_id
            else:
                self.signatory_valids = ""
            if self.signatory_valid_id == 'TIN':
                self.signatory_valid_details = self.signatory_id.tin_no
            elif self.signatory_valid_id == 'SSS':
                self.signatory_valid_details = self.signatory_id.sss_no
            elif self.signatory_valid_id == 'PHILHEALTH':
                self.signatory_valid_details = self.signatory_id.ph_no
            elif self.signatory_valid_id == 'HDMF':
                self.signatory_valid_details = self.signatory_id.hdmf_no
            else:
                self.signatory_valid_details = ""

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id.id
            self.salary = self.employee_id.contract_id.wage

    @api.onchange('signatory_id')
    def _onchange_signatory_id(self):
        if self.signatory_id:
            self.signatory_job_id = self.signatory_id.job_id.name

    @api.multi
    def get_months(self, date, numbers):
        if date:
            date_hired = datetime.strptime(date, '%Y-%m-%d')
            additional_date = date_hired + relativedelta(months=numbers)
            result = additional_date.strftime('%B %d, %Y')
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

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['employee_id', 'company_id', 'signatory_job_id', 'signatory_id',
                                  'salary', 'emp_valids', 'emp_valid_details', 'signatory_valids',
                                  'signatory_valid_details'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_memorandum_agreement_template', data=data)


# PDF FILE REPORT
class HRMemorandumAgreementReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_memorandum_agreement_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        company_id = data['form']['company_id']
        employee_id = data['form']['employee_id']
        signatory_id = data['form']['signatory_id']
        if company_id:
            company_id = data['form']['company_id'][0]
        if employee_id:
            employee_id = data['form']['employee_id'][0]
        if signatory_id:
            signatory_id = data['form']['signatory_id'][0]
        company = self.env['res.company'].browse(company_id)
        signatory = self.env['hr.employee'].browse(signatory_id)
        employee = self.env['hr.employee'].browse(employee_id)
        signatory_job_id = data['form']['signatory_job_id']
        emp_valids = data['form']['emp_valids']
        emp_valid_details = data['form']['emp_valid_details']
        salary = data['form']['salary']
        signatory_valids = data['form']['signatory_valids']
        signatory_valid_details = data['form']['signatory_valid_details']

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'employee_id': employee,
            'company_id': company,
            'signatory_id': signatory,
            'signatory_job_id': signatory_job_id,
            'salary': salary,
            'emp_valids': emp_valids,
            'emp_valid_details': emp_valid_details,
            'signatory_valids': signatory_valids,
            'signatory_valid_details': signatory_valid_details
        }

        return self.env['report'].render('hrms_employee.report_memorandum_agreement_template', docargs)

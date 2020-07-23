from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
import calendar, datetime


class GiftCheckHandler(models.TransientModel):
    _name = 'hr.gift.check.handler'

    date_event = fields.Date(string="Date Event", required=False, )
    name = fields.Char(string="Event Description", required=False, )
    department_ids = fields.Many2many(comodel_name="hr.department", string="Branch / Department")
    company_ids = fields.Many2many(comodel_name="res.company", string="Company")
    event_type = fields.Selection(string="Event Type", selection=[('check', 'Gift Check'), ('rice', 'Rice Incentive'), ], required=False, default='check')
    filters = fields.Selection(string="Filter By", selection=[('department', 'Branch / Department'), ('company', 'Company')],
                               required=False, default='department')
    user_id = fields.Many2one(comodel_name="hr.employee", string="User(s)", required=False,
                              default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))

    @api.multi
    def get_sorted(self, list):
        if list:
            result = sorted(list, key=lambda x: x.name)
            return result

    @api.multi
    def get_rice_incentive(self):
        if self.event_type == 'rice':
            res = self.env['hr.rice.incentive.matrix'].search([])
            return res

    @api.multi
    def company_env(self, company_id):
        if company_id:
            res = self.env['res.company'].browse(company_id)
            return res

    @api.multi
    def department_env(self, department_id):
        if department_id:
            res = self.env['hr.department'].browse(department_id)
            return res

    @api.multi
    def print_check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['company_ids', 'date_event', 'department_ids', 'name', 'filters', 'user_id', 'event_type'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_check_template', data=data)

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


class GiftCheckReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_check_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        company = data['form']['company_ids']
        date_event = data['form']['date_event']
        department = data['form']['department_ids']
        event_type = data['form']['event_type']
        records = []
        # ALL
        datas = {}
        if company and date_event:
            datas = self.env['hr.employee'].search([('date_hired', '<=', date_event)])
        # Company
        if company and date_event:
            datas = self.env['hr.employee'].search([('company_id', 'in', company),
                                                    ('date_hired', '<=', date_event)])
        # Department
        if department and date_event:
            datas = self.env['hr.employee'].search([('department_id', 'in', department),
                                                    ('date_hired', '<=', date_event)])
        if datas:
            for line in datas:
                # emp_included = False
                if not line.active:
                    if line.date_separated <= date_event:
                        emp_included = False
                    else:
                        emp_included = True
                else:
                    emp_included = True
                if emp_included:
                    amount = 0.0
                    children = 0.0
                    spouse = 0.0
                    check = 0.0
                    kilos = 0.0
                    count_days = 365.00
                    if line.date_hired and event_type == 'check':
                        service = datetime.datetime.strptime(line.date_hired, '%Y-%m-%d').date()
                        event = datetime.datetime.strptime(date_event, '%Y-%m-%d').date()
                        total_service = (event - service).days / count_days
                        print total_service
                        gift_check = self.env['hr.gift.check.matrix'].search([('minrange', '<=', total_service),
                                                                             ('maxrange', '>=', total_service),
                                                                             ('active', '=', True)])
                        print gift_check
                        check = float(gift_check.check)
                        if line.marital == 'married':
                            spouse = float(gift_check.spouse)
                        if line.relative_ids:
                            count = 0
                            for child in line.relative_ids:
                                if child.is_children:
                                    bday = datetime.datetime.strptime(child.birthday, '%Y-%m-%d').date()
                                    event = datetime.datetime.strptime(date_event, '%Y-%m-%d').date()
                                    age = (event - bday).days / count_days
                                    if age < 18.0 and count < 2:
                                        count += 1
                                        children += float(gift_check.children)
                        amount = float(check) + float(spouse) + float(children)
                    if line.date_hired and event_type == 'rice':
                        service = datetime.datetime.strptime(line.date_hired, '%Y-%m-%d').date()
                        event = datetime.datetime.strptime(date_event, '%Y-%m-%d').date()
                        total_service = ((event - service).days + 1) / count_days
                        print total_service
                        rice = self.env['hr.rice.incentive.matrix'].search([('minrange', '<', total_service),
                                                                            ('maxrange', '>', total_service),
                                                                            ('active', '=', True)])
                        kilos = float(rice.kilos)
                        print rice
                    values = {
                            'id': line.identification_id,
                            'employee_name': line.name,
                            'employee_id': line.id,
                            'date_hired': line.date_hired,
                            'job': line.job_id.name,
                            'department_name': line.department_id.name,
                            'department_id': line.department_id.id,
                            'company_name': line.company_id.name,
                            'company_id': line.company_id.id,
                            'service': round(check, 2),
                            'wife': round(spouse, 2),
                            'children': round(children, 2),
                            'amount': round(amount, 2),
                            'sack': round(kilos, 2),
                    }
                    print'VALUES', values
                    records.append(values)
        print 'RECORD', records
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'records': records,

        }

        return self.env['report'].render('hrms_employee.report_check_template', docargs)


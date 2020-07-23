from odoo import models, api, fields, _


class HRNonDisclosureAgreement(models.TransientModel):
    _name = 'hr.non.disclosure.agreement'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False)
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Signatory", required=False, domain=[('form_signatory', '=', True)])
    signatory_job_id = fields.Char( string="Position", required=False, )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id.id

    @api.onchange('signatory_id')
    def _onchange_signatory_id(self):
        if self.signatory_id:
            self.signatory_job_id = self.signatory_id.job_id.name

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
        data['form'] = self.read(['employee_id', 'company_id', 'signatory_job_id', 'signatory_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_non_disclosure_template', data=data)


# PDF FILE REPORT
class HRNonDisclosureAgreementReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_non_disclosure_template'

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
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'employee_id': employee,
            'company_id': company,
            'signatory_id': signatory,
            'signatory_job_id': signatory_job_id
        }

        return self.env['report'].render('hrms_employee.report_non_disclosure_template', docargs)

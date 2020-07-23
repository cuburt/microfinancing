from odoo import models, api, fields, _
from datetime import datetime, date


class HrRecruitmentAgreement(models.TransientModel):
    _name = 'hr.recruitment.agreement'

    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="Applicant", required=False, )
    superior_id = fields.Many2one(comodel_name="hr.job", string="Superior Position", required=False, )
    date_filed = fields.Date(string="Date Filed", required=False, default=date.today())
    time_start = fields.Float(string="Start of Work",  required=False, default=8.0)
    time_end = fields.Float(string="End of Work",  required=False, default=17.0)
    work_start = fields.Datetime(string="Start Working Date", required=False, )
    calendar_id = fields.Many2one(comodel_name="resource.calendar", string="Working Time", required=False, )
    hr_manager_id = fields.Many2one(comodel_name="hr.employee", string="Hr Manager", required=False, )

    @api.onchange('applicant_id')
    def _onchange_applicant_id(self):
        if self.applicant_id:
            self.superior_id = self.applicant_id.recruitment_request_id.requester_id.job_id.id
            self.hr_manager_id = self.applicant_id.recruitment_request_id.requester_id.hr_approver_id.id

    @api.multi
    def print_agreement_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.sudo().read(['applicant_id', 'superior_id', 'date_filed', 'work_start',
                                         'calendar_id', 'hr_manager_id', 'time_start', 'time_end'])[0]

        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].sudo().get_action(self, 'hrms_employee.report_recruitment_agreement_template', data=data)


class HrRecruitmentAgreementReport(models.AbstractModel):
    _name = 'report.hrms_employee.report_recruitment_agreement_template'

    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,

        }

        return self.env['report'].sudo().render('hrms_employee.report_recruitment_agreement_template', docargs)

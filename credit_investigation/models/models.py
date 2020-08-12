# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanApplication(models.Model):
    _inherit = 'credit.loan.application'

    status = fields.Selection(string="Status", selection_add=[('investigate','Investigation')], required=True,
                             track_visibility='onchange')
    client_investigations = fields.One2many('credit.client.investigation', 'loan_application', 'Client Investigation')

    @api.one
    def investigate_form(self):
        if not self.env['credit.client.investigation'].search([('loan_application','=',self.id)], limit=1):
            self.env['credit.client.investigation'].create({
                'loan_application':self.id,
                'name':'CI/BI Group '+ self.name,
                'status':'ongoing',
                'investigation_date':fields.Datetime.now(),
            })

        self.status = 'investigate'

class ClientInvestigation(models.Model):
    _name = 'credit.client.investigation'

    name = fields.Char()
    status = fields.Selection([('draft','Draft'),
                               ('ongoing','Ongoing'),
                               ('done','Done'),
                               ('cancel','Cancelled')], default='draft')
    loan_application = fields.Many2one('credit.loan.application','Loan Application')
    investigation_date = fields.Datetime('Investigation Date', default=fields.Datetime.now())
    questions = fields.One2many('credit.client.investigation.questionnaire','ci_id','Questions')
    ave_score = fields.Float(digits=(0,2), string='Average Score')

    @api.one
    def draft_form(self):
        self.status = 'draft'

    @api.one
    def confirm_form(self):
        self.status = 'ongoing'

    @api.one
    def cancel_form(self):
        self.status = 'cancel'

    @api.one
    def done_form(self):
        self.status = 'done'


class CIQuestionnaire(models.Model):
    _name = 'credit.client.investigation.questionnaire'

    ci_id = fields.Many2one('credit.client.investigation', 'CI/BI Form', required=True)
    question = fields.Text('Question',required=True)
    score = fields.Selection([('0','Bad'),
                              ('1','Not Bad'),
                              ('2','Fair'),
                              ('3','Good'),
                              ('4','Very Good'),
                              ('5','Excellent')], default='0', string='Score')
    remarks = fields.Text('Remarks')

    # @api.depends('score')
    # def _change_state(self):
    #     for rec in self:
    #         if rec.score == 0:
    #             rec.status = 'unanswered'
    #         else:
    #             rec.status = 'answered'
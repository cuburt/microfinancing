# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError


#TODO: VALIDATION ON DRAFT

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string="Status", selection_add=[('investigate','Investigation')], required=True,
                             track_visibility='onchange')
    client_investigations = fields.One2many('credit.client.investigation', 'loan_application', 'Client Investigation')
    investigation_status = fields.Boolean(default=False, compute='get_inv_status', readonly=True)
    attachments = fields.Many2many('ir.attachment', string='Attachment')
    date_investigated = fields.Datetime('Investigation Date Ended')

    @api.one
    def get_inv_status(self):
        for rec in self:
            rec.investigation_status = self.env['credit.client.investigation'].search([('loan_application','=',self.id),('status','=','done')], order='investigation_date desc', limit=1).is_passed

    @api.one
    def investigate_form(self):
        try:
            if not self.env['credit.client.investigation'].search([('loan_application','=',self.id)], limit=1):
                self.env['credit.client.investigation'].create({
                    'loan_application':self.id,
                    'name':'CI/BI Group '+ self.name,
                    'status':'ongoing',
                    'investigation_date':fields.Datetime.now(),
                })
            self.status = 'investigate'
        except Exception as e:
            raise UserError(_("ERROR: 'investigate_form' "+str(e)))

class ClientInvestigation(models.Model):
    _name = 'credit.client.investigation'

    name = fields.Char()
    status = fields.Selection([('draft','Draft'),
                               ('ongoing','Ongoing'),
                               ('done','Done'),
                               ('cancel','Cancelled')], default='draft')
    is_passed = fields.Boolean(default=False, compute='set_result')
    loan_application = fields.Many2one('crm.lead','Loan Application')
    partner_id = fields.Many2one('res.partner', related='loan_application.partner_id', string='Applicant')
    investigation_date = fields.Datetime('Investigation Date Started', default=fields.Datetime.now())
    questions = fields.One2many('credit.client.investigation.questionnaire','ci_id','Questions')
    character = fields.One2many('credit.client.investigation.questionnaire', compute='sort_questions')
    capacity = fields.One2many('credit.client.investigation.questionnaire', compute='sort_questions')
    capital = fields.One2many('credit.client.investigation.questionnaire', compute='sort_questions')
    condition = fields.One2many('credit.client.investigation.questionnaire', compute='sort_questions')
    collateral = fields.One2many('credit.client.investigation.questionnaire', compute='sort_questions')
    ave_score = fields.Float(digits=(0,2), string='Average Score', compute='_get_mean_score')
    product_id = fields.Many2one('product.template', related='loan_application.product_id')

    @api.depends('questions')
    def sort_questions(self):
        self.character = self.questions.search([('category','=','Character'),('ci_id','=',self.id)])
        self.capacity = self.questions.search([('category','=','Capacity'),('ci_id','=',self.id)])
        self.capital = self.questions.search([('category','=','Capital'),('ci_id','=',self.id)])
        self.condition = self.questions.search([('category','=','Condition'),('ci_id','=',self.id)])
        self.collateral = self.questions.search([('category','=','Collateral'),('ci_id','=',self.id)])

    def set_result(self):
        self.is_passed = bool(self.ave_score>=4)

    def _get_mean_score(self):
        for rec in self:
            try:
                rec.ave_score = (sum([question.score_value for question in rec.questions]))/len([question.score_value for question in rec.questions])
            except ZeroDivisionError as zde:
                raise ValidationError(_('There are no available questions. Please add questions.'))
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
        #TODO: ALLOW PRINT FUNCTION
        self.status = 'done'
        self.loan_application.date_investigated = fields.Datetime.now()
        self.loan_application.status = 'evaluate'
        self.loan_application.stage_id = self.env['crm.stage'].sudo().search([('name','=','Qualified')])

    @api.model
    def create(self, values):
        ci = super(ClientInvestigation, self).create(values)
        question = self.env['credit.client.investigation.questionnaire'].search([('ci_id','=',ci.id)], limit=1)
        if not question:
            try:
                questions = self.env['credit.client.investigation.question'].search([('product_category.id', '=', ci.product_id.id)])
                for q in questions:
                    self.env['credit.client.investigation.questionnaire'].create({
                        'ci_id':ci.id,
                        'question_id':q.id,
                    })
            except Exception as e:
                raise UserError(_("ERROR: 'create' "+str(e)))
        return ci

class CIQuestionCategory(models.Model):
    _name = 'credit.client.investigation.question.category'

    name = fields.Char('Category', required=True)
    questions = fields.One2many('credit.client.investigation.question', 'category_id', 'Questions')
    product_category = fields.Many2one('product.template', 'Category')

class CIQuestion(models.Model):
    _name = 'credit.client.investigation.question'

    name = fields.Char(compute='set_name')
    category_id = fields.Many2one('credit.client.investigation.question.category','Category')
    category = fields.Char(related='category_id.name')
    question = fields.Text('Question',required=True, index=True)
    product_category = fields.Many2one('product.template', related='category_id.product_category')


    @api.depends('category_id')
    def set_name(self):
        for i,rec in enumerate(self):
            if not i != 0 and rec[i].id != rec[-i].id:
                i = 0
            rec.name = rec.category_id.name+' Question '+str(i+1)

class CIQuestionnaire(models.Model):
    _name = 'credit.client.investigation.questionnaire'

    name = fields.Char(related='question_id.name')
    ci_id = fields.Many2one('credit.client.investigation', 'CI/BI Form')
    question_id = fields.Many2one('credit.client.investigation.question', 'Question')
    category = fields.Char(related='question_id.category', store=True)
    question = fields.Text(related='question_id.question')
    score = fields.Selection([('0','Bad'),
                              ('1','Not Bad'),
                              ('2','Fair'),
                              ('3','Good'),
                              ('4','Very Good'),
                              ('5','Excellent')], default='0', string='Score')
    score_value = fields.Float(digits=(0,2), compute='_get_score')
    remarks = fields.Text('Remarks')

    @api.depends('score')
    def _get_score(self):
        for rec in self:
            rec.score_value = int(rec.score)


    # @api.depends('score')
    # def _change_state(self):
    #     for rec in self:
    #         if rec.score == 0:
    #             rec.status = 'unanswered'
    #         else:
    #             rec.status = 'answered'
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _
from lxml import etree
from odoo.exceptions import ValidationError, UserError


#TODO: VALIDATION ON DRAFT

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string="Status", selection_add=[('investigate','Investigation'),("approve_bm","BM's Approval"),("approve_gm","GM's Approval"),("approve_crecom","CRECOM's Approval"),("approve_execom","EXECOM's Approval"),("approve_bod","BOD's Approval"),('passed','Passed'),('failed','Failed')], required=True,
                             track_visibility='onchange')
    client_investigations = fields.One2many('credit.client.investigation', 'application_id', 'Client Investigation')
    investigation_status = fields.Boolean(default=False, compute='get_inv_status', readonly=True)
    attachments = fields.Many2many('ir.attachment', string='Attachment')
    date_investigated = fields.Datetime('Investigation Date Ended', readonly=True)

    @api.multi
    def approve_bm(self):
        if self.status == 'approve_bm':
            self.status = 'approve_gm'
        return True

    @api.multi
    def approve_gm(self):
        if self.status == 'approve_gm':
            self.status = 'approve_crecom'
        return True

    @api.multi
    def approve_crecom(self):
        if self.status == 'approve_crecom':
            self.status = 'approve_execom'
        return True

    @api.multi
    def approve_execom(self):
        if self.status == 'approve_execom':
            self.status = 'approve_bod'
        return True

    @api.multi
    def approve_bod(self):
        if self.status == 'approve_bod':
            self.status = 'passed'
            self.stage_id = self.env['crm.stage'].sudo().search([('name','=','Approved')])
        return True

    @api.one
    def get_inv_status(self):
        for rec in self:
            rec.investigation_status = self.env['credit.client.investigation'].search([('application_id','=',self.id),('status','=','done')], order='investigation_date desc', limit=1).is_passed

    @api.multi
    def investigate_form(self):
        try:
            if not self.env['credit.client.investigation'].search([('application_id','=',self.id)], limit=1):
                # CREATION OF INDIVIDUAL CI FORM BASED FROM THE QUESTIONS SELECTED FOR THE APPLIED PRODUCT. SEE CREATE FUNCTION FOR THIS MODEL.
                self.env['credit.client.investigation'].create({
                    'application_id':self.id,
                    'name':'CI/BI Group '+ self.name,
                    'status':'ongoing',
                    'investigation_date':fields.Datetime.now(),
                })
            self.status = 'investigate'
            self.stage_id = self.env['crm.stage'].sudo().search([('name','=','Credit Investigation')])
        except Exception as e:
            raise UserError(_("ERROR: 'investigate_form' "+str(e)))

        # name = 'Credit Investigation'
        # context = {'default_application_id': self.id,
        #            'default_investigation_id': ci.id}
        # return {'type': 'ir.actions.act_window',
        #         'name': name,
        #         'view_type': 'tree',
        #         'view_mode': 'tree',
        #         'res_model': 'wizard.client.investigation',
        #         'target': 'new',
        #         'context': context}

class ClientInvestigation(models.Model):
    _name = 'credit.client.investigation'

    name = fields.Char()
    status = fields.Selection([('draft','Draft'),
                               ('ongoing','Ongoing'),
                               ('done','Done'),
                               ('cancel','Cancelled')],
                                default='draft')
    is_passed = fields.Boolean(default=False, compute='set_result')
    application_id = fields.Many2one('crm.lead','Loan Application')
    partner_id = fields.Many2one('res.partner', related='application_id.partner_id', string='Applicant')
    investigation_date = fields.Datetime('Investigation Date Started', default=fields.Datetime.now(), readonly=True)
    character = fields.One2many('credit.client.investigation.questionnaire', 'character', string='Character')
    capacity = fields.One2many('credit.client.investigation.questionnaire', 'capacity', string='Capacity')
    capital = fields.One2many('credit.client.investigation.questionnaire', 'capital', string='Capital')
    condition = fields.One2many('credit.client.investigation.questionnaire', 'condition', string='Condition')
    collateral = fields.One2many('credit.client.investigation.questionnaire', 'collateral', string='Collateral')
    character_remarks = fields.Text('Character')
    capacity_remarks = fields.Text('Character')
    capital_remarks = fields.Text('Character')
    condition_remarks = fields.Text('Character')
    collateral_remarks = fields.Text('Character')
    ave_score = fields.Float(digits=(0,2), string='Average Score', compute='_get_mean_score')
    product_id = fields.Many2one('product.template', related='application_id.product_id')

    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     view = super(ClientInvestigation, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         doc = etree.XML(view['arch'])
    #         notebook = doc.xpath("//notebook")
    #         page = notebook.addnext(etree.Element('page'))
    #         page.addnext(etree.Element())
    #
    #         print(doc)
    #     return view

    def set_result(self):
            self.is_passed = bool(self.ave_score>=4) #TODO: CHANGE FOR PASSING THRESHOLD

    def _get_mean_score(self):
        for rec in self:
            try:
                print(rec.character)
                print(rec.capacity)
                print(rec.capital)
                print(rec.condition)
                print(rec.collateral)
                sum_question_score = (sum([question.score_value for question in rec.character]))+(sum([question.score_value for question in rec.capacity]))+(sum([question.score_value for question in rec.capital]))+(sum([question.score_value for question in rec.condition]))+(sum(question.score_value for question in rec.collateral))
                len_question_score = (len(rec.character))+(len(rec.capacity))+(len(rec.capital))+(len(rec.condition))+(len(rec.collateral))
                rec.ave_score = sum_question_score/len_question_score
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
        #TODO: ALLOW PRINT FUNCTION IF INVESTIGATION STATUS IS 'DONE'
        category_id = self.env['credit.client.investigation.question.category'].search([])
        category_ids = [category.id for category in category_id]
        categories = category_id.search([('id', 'in', category_ids)])
        for category in categories:
            try:
                for x in eval('self.'+category.name.lower()):
                    if ((x.score_1 if x else x) +
                        (x.score_2 if x else x) +
                        (x.score_3 if x else x) +
                        (x.score_4 if x else x) +
                        (x.score_5 if x else x)) > 1:
                        raise UserError(_('You cannot have multiple ratings per criterion. Kindly review your ratings. Otherwise, contact the administrator.'))
                    if ((x.score_1 if x else x) +
                        (x.score_2 if x else x) +
                        (x.score_3 if x else x) +
                        (x.score_4 if x else x) +
                        (x.score_5 if x else x)) < 1:
                        raise UserError(_('You may have left a criterion unrated, kindly fill the form out completely. Otherwise, contact the administrator.'))
            except KeyError: pass
            except Exception as e:
                raise ValidationError(_("ERROR: 'done_form' Contact the administrator immediately. "+ str(e)))
        self.status = 'done'
        self.application_id.date_investigated = fields.Datetime.now()
        self.application_id.is_investigated = True
        if self.is_passed:
            self.application_id.status = 'approve_bm'
            self.application_id.stage_id = self.env['crm.stage'].sudo().search([('name', '=', 'Approval')])
        else:
            self.application_id.status = 'failed'
            self.application_id.stage_id = self.env['crm.stage'].sudo().search([('name', '=', 'Failed Application')])


    @api.model
    def create(self, values):
        application = self.env['crm.lead'].search([('id','=',values['application_id'])])

        try:
            category_id = self.env['credit.client.investigation.question.category'].search([])
            category_ids = [category.id for category in category_id if application.product_id.id in [product.id for product in category.allowed_products]]
            categories = category_id.search([('id','in',category_ids)])
            question_id = self.env['credit.client.investigation.question'].search([])
            question_ids = [question.id for question in question_id if application.product_id.id in [product.id for product in question.allowed_products]]

            for category in categories:
                values[str(category.name).lower()] = [(0, 0, {
                        'question_id': question.id
                    }) for question in category.questions if question.id in question_ids or (not question.id in question_ids and question.allow_based_on_category)]

                print(values)
        except Exception as e:
            raise UserError(_("ERROR: 'create' "+str(e)))
        return super(ClientInvestigation, self).create(values)

    @api.multi
    def write(self, values):

        return super(ClientInvestigation, self).write(values)

class Product(models.Model):
    _inherit = 'product.template'

    category_id = fields.Many2many('credit.client.investigation.question.category','category_product_rel')
    question_id = fields.Many2many('credit.client.investigation.question','question_product_rel')

class CIQuestionCategory(models.Model):
    _name = 'credit.client.investigation.question.category'

    name = fields.Char('Category', required=True)
    questions = fields.One2many('credit.client.investigation.question', 'category_id', 'Questions')
    allowed_products = fields.Many2many(comodel_name='product.template', relation='category_product_rel')

class CIQuestion(models.Model):
    _name = 'credit.client.investigation.question'

    name = fields.Char(compute='set_name')
    category_id = fields.Many2one('credit.client.investigation.question.category','Category')
    category = fields.Char(related='category_id.name')
    question = fields.Text('Question',required=True, index=True)
    allowed_products = fields.Many2many(comodel_name='product.template', relation='question_product_rel')
    allow_based_on_category = fields.Boolean('Allow products from category?', default=True)

    @api.depends('category_id')
    def set_name(self):
        print(self.env['credit.client.investigation.question'].sudo().search([]))
        for i,rec in enumerate(self.env['credit.client.investigation.question'].sudo().search([])):
            if not i != 0 and rec[i].id != rec[-i].id:
                i = 0
            print('QUESTION NO.', i)
            print('QUESTION:', rec.question)
            print('CATEGORY:', rec.category_id.name)
            rec.name = rec.category_id.name+' Question '+str(i+1)

class CIQuestionnaire(models.Model):
    _name = 'credit.client.investigation.questionnaire'

    name = fields.Char(related='question_id.name')
    character = fields.Many2one('credit.client.investigation')
    capacity = fields.Many2one('credit.client.investigation')
    capital = fields.Many2one('credit.client.investigation')
    condition = fields.Many2one('credit.client.investigation')
    collateral = fields.Many2one('credit.client.investigation')
    question_id = fields.Many2one('credit.client.investigation.question', 'Question', domain="[('category_id.id','=',"+str(lambda self:self.category_id.id)+")]")
    question = fields.Text(related='question_id.question')
    category_id = fields.Many2one(related='question_id.category_id')
    category = fields.Char(related='category_id.name')
    score_1 = fields.Boolean('1')
    score_2 = fields.Boolean('2')
    score_3 = fields.Boolean('3')
    score_4 = fields.Boolean('4')
    score_5 = fields.Boolean('5')
    score_value = fields.Float(digits=(0,2), compute='_get_score')

    @api.depends('score_1','score_2','score_3','score_4','score_5')
    def _get_score(self):
        for rec in self:
            rec.score_value = int((int(rec.score_1)*1)+(int(rec.score_2)*2)+(int(rec.score_3)*3)+(int(rec.score_4)*4)+(int(rec.score_5)*5))
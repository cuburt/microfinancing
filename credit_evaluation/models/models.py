# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError

# TODO: VALIDATION ON DRAFT
class GroupEvaluation(models.Model):
    _name = 'credit.loan.evaluation'

    name = fields.Char()
    registration_ids = fields.One2many('event.registration','evaluation_id','Loan History')
    indicator_ids = fields.One2many('credit.loan.evaluation.form', 'evaluation_id')
    group_id = fields.Many2one('credit.loan.group', 'Group', default=False)
    application_id = fields.Many2one('crm.lead','Application', default=False)
    area_id = fields.Many2one('res.area',related='group_id.area_id')
    branch_id = fields.Many2one('res.branch', related='area_id.branch_id')
    application_ids = fields.One2many('crm.lead', related='group_id.application_ids')
    is_complete = fields.Boolean(default=False)
    evaluation_date = fields.Datetime('Evaluation Date Started',default=fields.Datetime.now())
    group_product_id = fields.Many2one('product.template', related='group_id.product_id', string='Loan Type')
    product_id = fields.Many2one('product.template', related='application_id.product_id', string='Loan Type')
    attachments = fields.Many2many('ir.attachment', string='Prerequisites')
    total_score = fields.Integer('Total', compute='_get_mean_score')
    decision = fields.Selection([('approve','Approved'),
                                 ('reject','Rejected'),
                                 ('evaluate','For further evaluation')], 'Quality Strategic Decision')
    crecoms = fields.One2many('credit.loan.evaluation.crecom','evaluation_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('ongoing', 'Ongoing'),
                               ('done', 'Done'),
                               ('cancel', 'Cancelled')], default='draft')

    @api.depends('indicator_ids')
    def _get_mean_score(self):
        for rec in self:
            try:
                rec.total_score = sum([indicator.weighted_score for indicator in rec.indicator_ids])
            except ZeroDivisionError as zde:
                raise ValidationError(_("ZeroDivisionError: '_get_mean_score' "+str(zde)))
            except Exception as e:
                raise UserError(_("ERROR: '_get_mean_score' "+str(e)))
    @api.one
    def draft_form(self):
        self.status = 'draft'

    @api.one
    def confirm_form(self):
        if (1-(len(self.application_ids) == len(self.registration_ids)))*(self.group_id):
            raise ValidationError(_('Make sure that all members have attended the Membership Education'))
        self.status = 'ongoing'

    @api.one
    def cancel_form(self):
        self.status = 'cancel'

    @api.onchange('is_complete')
    def set_done(self):
        if self.is_complete:
            self.status = 'done'

    # @api.depends('application_ids','registration_ids','total_score','group_product_id','application_id','group_id')
    # def set_complete(self):
    #     try:
    #         for rec in self:
    #             rec.is_complete =
    #             print('VALIDATION COMPLETE?', bool((((len(rec.application_ids) == len(rec.registration_ids))*(bool(rec.group_id)))+(bool(rec.application_id))) * (rec.total_score>=4)))
    #             if rec.group_id:
    #                 print('This is a group evaluation.')
    #                 for application in rec.application_ids:
    #                     application.status = 'approve'
    #             else:
    #                 rec.application_id.status = 'approve'
    #     except Exception as e:
    #         raise UserError(_("ERROR: 'set_complete' "+str(e)))

    @api.one
    def set_done(self):
        self.is_complete = self.total_score >= 4
        if self.is_complete:
            self.status = 'done'
            if self.group_id:
                self.group_id.sudo().write({
                    'date_approved': fields.Datetime.now() if self.decision == 'approve' else False,
                    'status':'qualify',
                })
                for application_id in self.group_id.application_ids:
                    print(application_id.name)
                    application_id.sudo().write({
                        'date_approved': fields.Datetime.now() if self.decision == 'approve' else False,
                        'stage_id':self.env['crm.stage'].sudo().search([('name', '=', 'Proposition')]).id,
                        'status':'approve',
                    })
            else:
                self.application_id.sudo().write({
                    'date_approved': fields.Datetime.now() if self.decision == 'approve' else False,
                    'stage_id': self.env['crm.stage'].sudo().search([('name', '=', 'Proposition')]).id,
                    'status': 'approve'
                })
        else:
            raise UserError(_("Evaluation must be completed with a passing score first!"))

    @api.model
    def create(self, values):
        ev = super(GroupEvaluation, self).create(values)
        form = self.env['credit.loan.evaluation.form'].search([('evaluation_id','=',ev.id)],limit=1)
        if not form:
            try:
                for i in self.env['credit.loan.evaluation.csi'].search([]):
                    self.env['credit.loan.evaluation.form'].create({
                        'evaluation_id': ev.id,
                        'cs_indicator_id':i.id
                    })
                ev['status'] = 'ongoing'
                if values['group_product_id']:
                    ev['name'] = self.env['credit.loan.group'].sudo().search([('id','=',values['group_id'])]).name
                else:
                    ev['name'] = self.env['crm.lead'].sudo().search([('id','=',values['application_id'])]).name
            except Exception as e:
                raise UserError(_('ERROR 3 '+str(e)))
    #     return ev

# No idea what this is for. LMAO
# class LoanApplicationRemarks(models.Model):
#     _name = 'credit.loan.application.remarks'
#
#     name = fields.Char()
#     content = fields.Text()

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    #NOTE: the status 'Evaluation' is 'Loan Processing' in kanban
    status = fields.Selection(string='Status', selection_add=[('evaluate','Evaluation')], required=True, track_visibility='onchange')
    registration_ids = fields.One2many('event.registration','application_id')
    # performance_id = fields.Many2one('credit.loan.application.remarks','Performance')
    stage = fields.Char(compute='_get_stage')
    date_evaluated = fields.Datetime('Evaluation Date Ended', readonly=True)
    date_approved = fields.Datetime('Date Approved', readonly=True)
    evaluation_ids = fields.One2many('credit.loan.evaluation', 'application_id', 'Evaluations')
    is_investigated = fields.Boolean(default=False, string='State')
    loanclass = fields.Selection(related='product_id.loanclass')

    @api.depends('stage_id')
    def _get_stage(self):
        for rec in self:
            rec.stage = rec.stage_id.name

    @api.multi
    def process_application(self):
        if self.checklist_ids:
            #all requirements encoded in the system for this application
            documents = sum([int(rec.is_complied) for rec in self.checklist_ids if rec.document_id.stage == 'application'])
            #all non-optional requirements for loan processing
            template_docs = sum([1-(rec.is_optional) for rec in self.product_id.checklist_id.document_ids if rec.stage == 'application'])
            print('DOCUMENTS:', documents, template_docs)
            if documents == template_docs:
                self.generate_loan_details()
                self.status = 'evaluate'
                self.stage_id = self.env['crm.stage'].sudo().search([('name','=','Loan Processing')], limit=1)
            else:
                raise ValidationError(_('Requirements for loan processing must be complied.'))
        else:
            self.generate_loan_details()
            self.status = 'evaluate'
            self.stage_id = self.env['crm.stage'].sudo().search([('name', '=', 'Loan Processing')], limit=1)
        return True

    @api.multi
    def generate_loan_details(self):
        # THIS FUNCTION CREATES COLLECTION (IE, MONTHLY AMORT.) FOR THIS APPLICATION AND EACH APPLICATION IN A GROUP
        # GENERATE LOAN DETAILS: EDITABLE
        try:
            # if self.stage_id.id != self.env['crm.stage'].sudo().search([('name', '=', 'Approved')]).id and self.status != 'passed':
            #     raise UserError(_("The application must be approved first!"))
            if self.product_id.loanclass == 'group':
                for application in self.group_id.application_ids:
                    print('CREATING COLLECTION FOR:', application.partner_id.name)
                    self.env['credit.loan.collection'].sudo().create({
                        'application_id': application.id,
                        'status': 'active',
                    })
                    # application.write({
                        # 'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                    #     'status': 'disburse'
                    # })
                print('COLLECTION FOR GROUP MEMBERS CREATED!')
                return True

            elif self.product_id.loanclass == 'individual':

                print('CREATING COLLECTION FOR:', self.partner_id.name)

                # THIS LINE CALLS THE CREATE FUNCTION IN COLLECTION MODEL/TABLE
                self.env['credit.loan.collection'].sudo().create({'application_id': self.id,'status': 'draft'})

                # self.write({
                #     # 'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                #     'status': 'confirm'
                # })
                try:
                    self.planned_revenue = sum([rec.amortization for rec in self.collection_line_ids]) - self.loan_amount
                except Exception as e:
                    print(str(e))
                    pass
                print('COLLECTION FOR APPLICANT CREATED!')
                return True
        except Exception as e:
            raise UserError(_(str(e)))

    @api.multi
    def evaluate_applicant(self):
        if self.is_investigated:
            try:

                ev = self.evaluation_ids.search([('application_id.id','=',self.id)], order='evaluation_date desc', limit=1)
                if not ev:
                    self.env['credit.loan.evaluation'].create({
                            'application_id': self.id,
                            'group_product_id': False,
                            'product_id': self.product_id.id
                        })

                    if self.stage_id.name != 'Qualified':
                        raise UserError(_('\nInvestigate applicant first!'))

            except Exception as e:
                raise UserError(_("ERROR 'evaluate_applicant' "+str(e)))
        else:
            raise ValidationError(_('Application must be approved'))

        return True

    @api.multi
    def blacklist_applicant(self):
        self.env['credit.loan.blacklist'].sudo().create({
            'name':self.partner_id.name,
            'application_id':self.id
        })
        self.financing_id.status = 'blacklist'

    @api.multi
    def request_reapplication(self):
        self.env['credit.loan.reapplication'].sudo().create({
            'name': self.partner_id.name,
            'application_id': self.id
        })
        self.financing_id.status = 'archive'

    # @api.depends('investigation_status')
    # def set_approved(self):
    #     try:
    #         for rec in self:
    #             if rec.status != 'evaluate':
    #                 rec.is_approved = rec.investigation_status
    #                 if rec.is_approved:
    #                     rec.status = 'evaluate'
    #     except Exception as e:
    #         raise ValidationError(_("ERROR: 'set_approved' "+str(e)))

#TODO: replace this with SO
class Collection(models.Model):
    _name = 'credit.loan.collection'

    name = fields.Char()
    application_id = fields.Many2one('crm.lead', 'Application Seq.')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    partner_id = fields.Many2one('res.partner', related='application_id.partner_id')
    financing_id = fields.Many2one('credit.loan.financing', related='application_id.financing_id')
    savings_id = fields.Many2one('credit.loan.savings', related='application_id.savings_id')
    product_id = fields.Many2one('product.template', related='application_id.product_id', string='Applied Product')
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    term_id = fields.Many2one('account.payment.term', related='product_id.payment_term')
    interest_id = fields.Many2one('credit.loan.interest', related='product_id.interest_id')
    surcharge_id = fields.Many2one('credit.loan.surcharge', related='product_id.surcharge_id')
    penalty_id = fields.Many2one('credit.loan.penalty', related='product_id.penalty_id')
    collateral_id = fields.Many2one('credit.loan.collateral', related='product_id.collateral_id')
    fund_id = fields.Many2one('credit.loan.fund', related='product_id.fund_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('complete', 'Complete')])
    @api.multi
    def action_active(self):
        if self.status == 'draft':
            self.status = 'active'

    @api.multi
    def action_draft(self):
        if self.status == 'active':
            self.status = 'draft'

    @api.multi
    def action_complete(self):
        if self.status == 'active':
            self.status = 'complete'

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    status = fields.Selection(selection_add=[('evaluate', 'Evaluation'),('qualify','Qualified')], required=True, track_visibility='onchange')
    is_investigated = fields.Boolean(default=False, string='State', compute='set_investigated')
    # is_complete = fields.Boolean(default=False, compute='set_approved')
    evaluation_ids = fields.One2many('credit.loan.evaluation','group_id', 'Evaluations')

    @api.one
    def evaluate_group(self):
        if self.is_investigated:
            try:

                me = self.env['event.event'].search(
                    [('event_type_id.name', '=', 'Membership Education'), ('state', '=', 'confirm')],
                    order='date_begin desc', limit=1)

                if not me:
                    raise UserError(_('Set Membership Education Event first!'))

                ev = self.evaluation_ids.search([('group_id','=',self.id),('status','in',['draft','cancel'])], order='evaluation_date desc', limit=1)
                if not ev:
                    ev = self.env['credit.loan.evaluation'].create({
                            'group_id': self.id,
                            'group_product_id': self.product_id.id,
                            'product_id': False,
                        })
                for application_id in self.application_ids:
                    application = self.env['crm.lead'].search(
                        [('partner_id', '=', application_id.partner_id.id), ('group_id', '=', self.id), ('state', '=', True)])
                    self.env['event.registration'].create({
                        'event_id': me.id,
                        'evaluation_id': ev.id,
                        'application_id': application.id,
                        'partner_id': application_id.partner_id.id,
                    })
                    try:
                        self.env['crm.lead'].search([('id', '=', application.id)]).stage_id = \
                        self.env['crm.stage'].search([('name', '=', 'Qualified')])
                    except ValueError as ve:
                        raise UserError(_(str(ve) + '\nConfirm group first!'))
                    except Exception as e:
                        raise UserError(_("ERROR: '(evaluate_group)'"+str(e)))
                    application.write({
                        'status':'evaluate'
                    })
            except Exception as e:
                raise UserError(_("ERROR 'evaluate_group' "+str(e)))
            self.status = 'evaluate'
        else:
            raise ValidationError(_('All members\'s application must be approved'))


    @api.depends('application_ids')
    def set_investigated(self):
        try:
            for rec in self:
                if rec.application_ids:
                    rec.is_investigated = (len(rec.application_ids) == sum([_bool.investigation_status for _bool in rec.application_ids]))
                    # print('NO. OF APPROVED APPLICATIONS:', len(rec.application_ids) == sum([_bool.investigation_status for _bool in rec.application_ids]))
                    # if rec.is_investigated:
                    #
                    #     if rec.status != 'qualify':
                    #         for application in rec.application_ids:
                    #             application.write({
                    #                 'status':'evaluate',
                    #                 'stage_id':self.env['crm.stage'].search([('name', '=', 'Qualified')]).id,
                    #             })
                    #             print(self.env['crm.stage'].search([('name', '=', 'Qualified')]).id)
                    #         rec.write({'status':'qualify'})
                    # self.is_complete = (len(rec.members) == sum([((int(self.env['credit.loan.application'].search([('partner_id','=',member.id),('group_id','=',rec.id),('state','=',True)], order='application_date desc', limit=1).partner_id.id) for member in members) for members in evaluation)for evaluation in self.evaluation_ids]))
        except Exception as e:
            raise ValidationError(_("ERROR: 'set_approved' "+str(e)))

    @api.onchange('application_ids')
    def set_approved(self):
        try:
            self.is_approved = (
                        len(self.application_ids) == sum([_bool.investigation_status for _bool in self.application_ids]))
            if self.is_approved:
                for application in self.application_ids:
                    application.write({
                        'status': 'qualify',
                        'stage_id': self.env['crm.stage'].search([('name', '=', 'Proposition')]).id,
                    })
                    print( self.env['crm.stage'].search([('name', '=', 'Proposition')]).id)
                self.status = 'qualify'
                # self.is_complete = (len(rec.members) == sum([((int(self.env['credit.loan.application'].search([('partner_id','=',member.id),('group_id','=',rec.id),('state','=',True)], order='application_date desc', limit=1).partner_id.id) for member in members) for members in evaluation)for evaluation in self.evaluation_ids]))
        except Exception as e:
            raise ValidationError(_("ERROR: 'set_approved' "+str(e)))

class CrecomEvaluation(models.Model):
    _name = 'credit.loan.evaluation.crecom'

    name = fields.Char()
    evaluation_id = fields.Many2one('credit.loan.evaluation')
    is_passed = fields.Boolean(default=False)
    others = fields.Text()

class CriticalSuccessSubIndicators(models.Model):
    _name = 'credit.loan.evaluation.cssi'

    name = fields.Char()
    indicator_id = fields.Many2one('credit.loan.evaluation.csi')

class CriticalSuccessIndicators(models.Model):
    _name = 'credit.loan.evaluation.csi'

    name = fields.Char()
    form_id = fields.Many2one('credit.loan.evaluation.form')
    weight = fields.Float(digits=(0,2),string='Weight')
    subindicators = fields.One2many('credit.loan.evaluation.cssi','indicator_id')

class GroupEvaluationForm(models.Model):
    _name = 'credit.loan.evaluation.form'

    name = fields.Char(related='cs_indicator_id.name')
    weight = fields.Float(related='cs_indicator_id.weight')
    evaluation_id = fields.Many2one('credit.loan.evaluation')
    cs_indicator_id = fields.Many2one('credit.loan.evaluation.csi', 'Critical Success Indicators')
    subindicators = fields.One2many('credit.loan.evaluation.cssi',related='cs_indicator_id.subindicators')
    rating = fields.Integer('Rating')
    weighted_score = fields.Float('Weighted Score', compute='_compute_score')
    proof = fields.Text('Proof of Evidence')

    @api.depends('rating', 'weight')
    def _compute_score(self):
        try:
            for rec in self:
                rec.weighted_score = rec.rating * rec.weight
        except Exception as e:
            raise ValidationError(_("ERROR: '_compute_score' "+str(e)))

class EventRegistration(models.Model):
    _inherit = 'event.registration'

    application_id = fields.Many2one('crm.lead','Application')
    evaluation_id = fields.Many2one('credit.loan.evaluation','Evaluation')
    application = fields.Char(related='application_id.name')
    application_status = fields.Selection(related='application_id.status')

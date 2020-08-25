# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError

#TODO: VALIDATION ON DRAFT

class GroupEvaluation(models.Model):
    _name = 'credit.group.evaluation'

    name = fields.Char(related='group_id.name')
    registration_ids = fields.One2many('event.registration','evaluation_id','Loan History')
    indicator_ids = fields.One2many('credit.group.evaluation.form', 'evaluation_id')
    group_id = fields.Many2one('credit.loan.group', 'Group')
    area_id = fields.Many2one('res.area',related='group_id.area_id')
    branch_id = fields.Many2one('res.branch', related='area_id.branch_id')
    members = fields.One2many('res.partner', related='group_id.members')
    is_complete = fields.Boolean(default=False, compute='set_complete')
    evaluation_date = fields.Datetime(default=fields.Datetime.now())
    product_id = fields.Many2one('product.product', related='group_id.product_id', string='Loan Type')
    attachments = fields.Many2many('ir.attachment', string='Prerequisites')
    total_score = fields.Integer('Total', compute='_get_mean_score')
    decision = fields.Selection([('approve','Approved'),
                                 ('reject','Rejected'),
                                 ('evaluate','For further evaluation')], 'Quality Strategic Decision')
    crecoms = fields.One2many('credit.group.evaluation.crecom','evaluation_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('ongoing', 'Ongoing'),
                               ('done', 'Done'),
                               ('cancel', 'Cancelled')], default='draft')
    def set_complete(self):
        for rec in self:
            self.is_complete = (len(rec.members) == len(rec.registration_ids))

    def _get_mean_score(self):
        for rec in self:
            try:
                rec.total_score = sum([indicator.weighted_score for indicator in rec.indicator_ids])
            except ZeroDivisionError as zde:
                raise ValidationError(_(str(zde)))

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

    @api.model
    def create(self, values):
        ev = super(GroupEvaluation, self).create(values)
        form = self.env['credit.group.evaluation.form'].search([('evaluation_id','=',ev.id)],limit=1)
        if not form:
            try:
                for i in self.env['credit.group.evaluation.csi'].search([]):
                    self.env['credit.group.evaluation.form'].create({
                        'evaluation_id': ev.id,
                        'cs_indicator_id':i.id
                    })
            except Exception as e:
                raise UserError(_('ERROR 3 '+str(e)))
        return ev

class LoanApplicationRemarks(models.Model):
    _name = 'credit.loan.application.remarks'

    name = fields.Char()
    content = fields.Text()

class LoanApplication(models.Model):
    _inherit = 'credit.loan.application'

    status = fields.Selection(string='Status', selection_add=[('confirm', 'Done')], required=True, track_visibility='onchange')
    registration_ids = fields.One2many('event.registration','application_id')
    performance_id = fields.Many2one('credit.loan.application.remarks','Performance')

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    status = fields.Selection(selection_add=[('evaluate', 'Evaluation')], required=True, track_visibility='onchange')
    is_approved = fields.Boolean(default=False, compute='set_approved', string='State')
    # is_complete = fields.Boolean(default=False, compute='set_approved')
    evaluation_ids = fields.One2many('credit.group.evaluation','group_id', 'Evaluations')

    #TODO: does not create form
    @api.one
    def evaluate_group(self):
        if self.is_approved:
            me = self.env['event.event'].search([('event_type_id.name','=','Membership Education'),('state','=','confirm')], order='date_begin desc', limit=1)
            try:
                ev = self.evaluation_ids.search([('group_id','=',self.id)], order='evaluation_date desc', limit=1)
                if not ev:
                    self.env['credit.group.evaluation'].create({
                            'group_id': self.id,
                        })
                    ev = self.evaluation_ids.search([('group_id', '=', self.id)], order='evaluation_date desc', limit=1)
                for member in self.members:
                    application = self.env['credit.loan.application'].search(
                        [('partner_id', '=', member.id), ('group_id', '=', self.id), ('state', '=', True)])
                    self.env['event.registration'].create({
                        'event_id': me.id,
                        'evaluation_id': ev.id,
                        'application_id': application.id,
                        'partner_id': member.id,
                    })
                    try:
                        self.env['crm.lead'].search([('application_id', '=', application.id)]).stage_id = \
                        self.env['crm.stage'].search([('name', '=', 'Qualified')])
                    except ValueError as ve:
                        raise UserError(_(str(ve) + '\nConfirm group first!'))
            except Exception as e:
                raise UserError(_('ERROR 1 '+str(e)))
            self.status = 'evaluate'
        else:
            raise ValidationError(_('All members\'s application must be approved'))


    @api.depends('members')
    def set_approved(self):
        for rec in self:
            self.is_approved = (len(rec.members) == sum([int(member.financing_ids.search([('member_id', '=', member.id),('group_id','=',rec.id)],limit=1,order='date_created desc').loan_applications.search([('partner_id', '=', member.id),('group_id','=',rec.id)],limit=1,order='application_date desc').status == 'confirm') for member in rec.members]))
            # self.is_complete = (len(rec.members) == sum([((int(self.env['credit.loan.application'].search([('partner_id','=',member.id),('group_id','=',rec.id),('state','=',True)], order='application_date desc', limit=1).partner_id.id) for member in members) for members in evaluation)for evaluation in self.evaluation_ids]))

class CrecomEvaluation(models.Model):
    _name = 'credit.group.evaluation.crecom'

    name = fields.Char()
    evaluation_id = fields.Many2one('credit.group.evaluation')
    is_passed = fields.Boolean(default=False)
    others = fields.Text()

class CriticalSuccessSubIndicators(models.Model):
    _name = 'credit.group.evaluation.cssi'

    name = fields.Char()
    indicator_id = fields.Many2one('credit.group.evaluation.csi')

class CriticalSuccessIndicators(models.Model):
    _name = 'credit.group.evaluation.csi'

    name = fields.Char()
    form_id = fields.Many2one('credit.group.evaluation.form')
    weight = fields.Float(digits=(0,2),string='Weight')
    subindicators = fields.One2many('credit.group.evaluation.cssi','indicator_id')

class GroupEvaluationForm(models.Model):
    _name = 'credit.group.evaluation.form'

    name = fields.Char(related='cs_indicator_id.name')
    weight = fields.Float(related='cs_indicator_id.weight')
    evaluation_id = fields.Many2one('credit.group.evaluation')
    cs_indicator_id = fields.Many2one('credit.group.evaluation.csi', 'Critical Success Indicators')
    subindicators = fields.One2many('credit.group.evaluation.cssi',related='cs_indicator_id.subindicators')
    rating = fields.Integer('Rating')
    weighted_score = fields.Integer('Weighted Score')
    proof = fields.Text('Proof of Evidence')



class EventRegistration(models.Model):
    _inherit = 'event.registration'

    application_id = fields.Many2one('credit.loan.application','Application')
    evaluation_id = fields.Many2one('credit.group.evaluation','Evaluation')
    application = fields.Char(related='application_id.name')
    application_status = fields.Selection(related='application_id.status')

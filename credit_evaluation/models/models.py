# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError

#TODO: VALIDATION ON DRAFT

class LoanApplication(models.Model):
    _inherit = 'credit.loan.application'

    status = fields.Selection(string='Status', selection_add=[('confirm', 'Done')], required=True, track_visibility='onchange')
    registration_ids = fields.One2many('event.registration','application_id')

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    status = fields.Selection(selection_add=[('evaluate', 'Evaluation')], required=True, track_visibility='onchange')
    is_approved = fields.Boolean(default=False, compute='set_approved', string='State')
    # is_complete = fields.Boolean(default=False, compute='set_approved')
    evaluation_ids = fields.One2many('credit.group.evaluation','group_id', 'Evaluations')

    @api.one
    def evaluate_group(self):
        print(self.is_approved)
        if self.is_approved:
            try:
                me = self.env['event.event'].search([('event_type_id.name','=','Membership Education'),('state','=','confirm')], order='date_begin desc', limit=1)
                try:
                    if not self.env['credit.group.evaluation'].search([('group_id','in',[self.evaluation_ids])], order='evaluation_date desc', limit=1):
                        ev = self.env['credit.group.evaluation'].create({
                                'group_id': self.id
                            })
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
                            self.env[
                                'crm.stage'].search([('name', '=', 'Qualified')])
                        except ValueError as ve:
                            raise UserError(_(str(ve) + '\nConfirm group first!'))

                except Exception as e:
                    raise UserError(_(str(e)))

            except Exception as e:
                raise UserError(_(str(e)))
            self.status = 'evaluate'
        else:
            raise ValidationError(_('All members\'s application must be approved'))


    @api.depends('members')
    def set_approved(self):
        for rec in self:
            self.is_approved = (len(rec.members) == sum([int(member.financing_ids.search([('member_id', '=', member.id),('group_id','=',rec.id)],limit=1,order='date_created desc').loan_applications.search([('partner_id', '=', member.id),('group_id','=',rec.id)],limit=1,order='application_date desc').status == 'confirm') for member in rec.members]))
            # self.is_complete = (len(rec.members) == sum([((int(self.env['credit.loan.application'].search([('partner_id','=',member.id),('group_id','=',rec.id),('state','=',True)], order='application_date desc', limit=1).partner_id.id) for member in members) for members in evaluation)for evaluation in self.evaluation_ids]))

class GroupEvaluation(models.Model):
    _name = 'credit.group.evaluation'

    registration_ids = fields.One2many('event.registration','evaluation_id')
    group_id = fields.Many2one('credit.loan.group', 'Group')
    members = fields.One2many('res.partner', related='group_id.members')
    is_complete = fields.Boolean(default=False, compute='set_complete')
    evaluation_date = fields.Datetime(default=fields.Datetime.now())

    def set_complete(self):
        for rec in self:
            self.is_complete = (len(rec.members) == len(rec.registration_ids))

class EventRegistration(models.Model):
    _inherit = 'event.registration'

    application_id = fields.Many2one('credit.loan.application','Application')
    evaluation_id = fields.Many2one('credit.group.evaluation','Evaluation')


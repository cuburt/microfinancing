# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

#
# [res.partner]-|---<HAS>---|<[loan.financing]-|---<HAS>----O<[crm.lead]>|----<HAS>----O-[loan.group]
#

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    group_id = fields.Many2one('credit.loan.group','Group', required_if_loantype='group')
    member_count = fields.Integer('# Members', compute='_compute_member_count')

    @api.multi
    def _compute_member_count(self):
        if self.group_id.application_ids:
            for rec in self:
                rec.member_count = len(rec.group_id.application_ids)
        else: self.member_count = 0

class LoanGroup(models.Model):
    _name = 'credit.loan.group'
    _inherit = 'mail.thread'

    name = fields.Char(track_visibility='always')
    index = fields.Integer()
    code = fields.Char(readonly=True)
    state = fields.Selection([('active', 'Active'),('inactive','Inactive')], default='active', track_visibility='onchange')
    status = fields.Selection([('draft','Draft'),('confirm','Confirmed')], default='draft', track_visibility='onchange')
    application_ids = fields.One2many('crm.lead','group_id','Members')
    date_organized = fields.Datetime(string='Date organized', default=fields.Datetime.now(),readonly=True)
    date_approved = fields.Datetime(string='Date approved', readonly=True)

    #RELATED
    application_id = fields.Many2one('crm.lead', 'Application Seq.', readonly=True)
    financing_id = fields.Many2one('credit.loan.financing', 'Loan Account', related='application_id.financing_id')
    partner_id = fields.Many2one('res.partner', related='application_id.partner_id')
    street = fields.Char(related='partner_id.street')
    street2 = fields.Char(related= 'partner_id.street2')
    zip = fields.Char(change_default=True, related= 'partner_id.zip')
    city = fields.Char(related= 'partner_id.city')
    state_id = fields.Many2one(related='partner_id.state_id')
    country_id = fields.Many2one(related='partner_id.country_id')

    branch_id = fields.Many2one('res.branch', 'Branch', related='application_id.branch_id')
    area_id = fields.Many2one('res.area','Area', related='application_id.area_id')
    do = fields.Many2one('res.partner', 'Assigned DO')

    @api.one
    def confirm_group(self):
        try:
            if self.event_registration_ids:
                for application_id in self.application_ids:

                    finance = self.env['credit.loan.financing'].search([('id', '=', application_id.financing_id.id)], limit=1)
                    finance.write({
                        'branch_id': self.area_id.branch_id.id,
                        'area_id': self.area_id.id,
                        'status': 'active',
                        })
                    print('Financing Account for {} is {}'.format(application_id.partner_id.name, finance.id))
                    print('Lead Account for {} is {}'.format(application_id.partner_id.name, application_id.id))
                    application_id.write({
                        'state': True
                    })

                self.status = 'confirm'

            else:
                raise ValidationError(_('Group Leader hasn\'t attended any of the information meeting yet.'))
        except Exception as e:
            raise UserError(_("ERROR: 'confirm_group' "+str(e)))

    @api.one
    def draft_group(self):
        try:
            self.env['credit.loan.financing'].search([('group_id.id','=',self.id)]).write({
                'status':'archive'
            })
            for application_id in self.application_ids:

                application = self.env['crm.lead'].search([('financing_id', '=', self.env['credit.loan.financing'].search([('group_id.id', '=', self.id), ('member_id.id', '=', application_id.partner_id.id)],
                                                               limit=1).id)], limit=1)
                try:
                    if self.env['crm.lead'].search([('application_id.id', '=', application.id)], limit=1):
                        lead = self.env['crm.lead'].search([('application_id.id', '=', application.id)], limit=1)
                        order = self.env['sale.order'].search([('opportunity_id.id', '=', lead.id)], limit=1)
                        if order:
                            order.unlink()
                        lead.unlink()
                    if self.env['credit.client.investigation'].search([('loan_application', '=', application.id)],limit=1):
                        raise UserError(_('Cancel all investigations for this group first!'))
                    if self.env['credit.member.evaluation'].search([('application_id.id', '=', application.id)],limit=1):
                        raise UserError(_('Cancel all evaluations for this group first!'))
                except:
                    pass
                finally:
                    application.write({
                        'state': False,
                        'status': 'draft'
                    })
            self.status = 'draft'
        except Exception as e:
            raise UserError(_("ERROR: 'draft_group' "+str(e)))

    @api.multi
    def unlink(self):
        try:
            if self.status != 'draft':
                raise UserError(_('Set to draft first before deleting.'))
            return super(LoanGroup, self).unlink()
        except Exception as e:
            raise UserError(_("ERROR: 'unlink' "+str(e)))


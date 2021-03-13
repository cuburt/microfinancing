# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
import logging
import datetime
_logger = logging.getLogger(__name__)

#
# [res.partner]-|---<HAS>---|<[loan.financing]-|---<HAS>----O<[crm.lead]>|----<HAS>----O-[loan.group]
#

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    group_id = fields.Many2one('credit.loan.group','Group', required_if_loantype='group')
    member_count = fields.Integer('# Members', compute='_compute_member_count')

    @api.depends('group_id')
    def _compute_member_count(self):
        for rec in self:
            rec.member_count = len(rec.group_id.application_ids)

class MembersTransient(models.TransientModel):
    _name = 'crm.lead.transient'

    application_id = fields.Many2one('crm.lead')
    financing_id = fields.Many2one('crm.lead', related='application_id.financing_id')
    partner_id = fields.Many2one('res.partner', related='financing_id.partner_id')
    group_id = fields.Many2one('credit.loan.group',related='application_id.group_id')

class LoanGroupBatch(models.Model):
    _name = 'credit.loan.group.batch'

    name = fields.Char('Batch')
    # code = fields.Char('Code')
    status = fields.Selection([('active','Active'),('archive','Archived'),('potential','Potential')], string='Status')
    group_ids = fields.One2many('credit.loan.group','batch_id','Batch')
    comment = fields.Text()

class LoanGroup(models.Model):
    _name = 'credit.loan.group'
    _inherit = 'mail.thread'

    name = fields.Char(track_visibility='always')
    index = fields.Integer()
    code = fields.Char(readonly=True)
    state = fields.Selection([('active', 'Active'),('inactive','Inactive')], default='active', track_visibility='onchange')
    status = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('cancel','Cancelled')], default='draft', track_visibility='onchange')
    transient_application_ids = fields.One2many('crm.lead.transient','group_id','Members')
    application_ids = fields.One2many('crm.lead','group_id','Members')
    date_organized = fields.Datetime(string='Date organized', default=fields.Datetime.now(),readonly=True)
    date_confirmed = fields.Datetime('Date Confirmed', readonly=True)
    date_approved = fields.Datetime(string='Date approved', readonly=True)
    batch_id = fields.Many2one('credit.loan.group.batch', 'Batch')
    application_id = fields.Many2one('crm.lead', 'Application Seq.', domain="['&',('group_id','=', None),('loanclass','=','group')]")
    financing_id = fields.Many2one('credit.loan.financing', 'Loan Account', related='application_id.financing_id')
    partner_id = fields.Many2one('res.partner', related='application_id.partner_id')
    street = fields.Char(related='partner_id.street')
    street2 = fields.Char(related= 'partner_id.street2')
    zip = fields.Char(related= 'partner_id.zip')
    city = fields.Char(related= 'partner_id.city')
    state_id = fields.Many2one(related='partner_id.state_id')
    country_id = fields.Many2one(related='partner_id.country_id')
    branch_id = fields.Many2one('res.branch', 'Branch', related='application_id.branch_id')
    area_id = fields.Many2one('res.area','Area', related='application_id.area_id')
    officer_id = fields.Many2one('res.partner', 'Assigned Officer',required=True)

    def return_domain(self, application):
        return {'domain': {'application_ids': ['&',('branch_id.id', '=', application.branch_id.id),
                                               '&',('officer_id.id', '=', self.officer_id.id), #TODO: CHANGE THIS BASED ON CRITERIA
                                               '&',('product_id.id', '=', application.product_id.id),
                                               '&',('group_id', '=', None),
                                               ('partner_id.id', '!=', application.partner_id.id)]}}

    @api.onchange('application_id')
    def load_members(self):
        self.officer_id = self.application_id.officer_id

    @api.onchange('officer_id')
    def onchange_officer(self):
        domain = self.return_domain(self.application_id)
        self.application_ids = self.env['crm.lead'].sudo().search(domain['domain']['application_ids'])
        return domain

    @api.onchange('area_id','officer_id')
    def onchange_area(self):
        return {'domain':{'officer_id':[('area_ids.id','=',self.application_id.area_id.id)]}}

    @api.multi
    def write(self, values):
        try:
            #the group may still be able to change its leader.
            application = self.env['crm.lead'].sudo().search([('id', '=', values['application_id'])])
            application.write({
                'group_id':self.id
            })
        except Exception as e:
            print(str(e))
            pass
        return super(LoanGroup, self).write(values)

    @api.model
    def create(self, values):
        try:
            application = self.env['crm.lead'].sudo().search([('id','=',values['application_id'])])
            officer = application.officer_id
            area = application.area_id
            values['financing_id'] = application.financing_id.id
            values['partner_id'] = application.partner_id.id
            values['street'] = application.partner_id.street
            values['street2'] = application.partner_id.street2
            values['zip'] = application.partner_id.zip
            values['city'] = application.partner_id.city
            values['state_id'] = application.partner_id.state_id
            values['country_id'] = application.partner_id.country_id
            values['branch_id'] = application.branch_id.id
            values['area_id'] = application.area_id.id
            values['officer_id'] = officer.id

            values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
            values['code'] = '%s-%s-%s' % ("{0:0=2d}".format(area.index), "{0:0=2d}".format(officer.index), "{0:0=2d}".format(values['index']))
            values['name'] = values['code']
            group = super(LoanGroup, self).create(values)
            application.write({
                'group_id':group.id
            })
            print(self.env['crm.lead'].search([('id','=',values['application_id'])]).group_id.name)
            print('GROUP CREATE IN GROUPS:', values)
            return group

        except Exception as e:
            raise UserError(_("ERROR: 'create group' " + str(e)))

    @api.one
    def confirm_group(self):
        try:
            if self.event_registration_ids:
                for application_id in self.application_ids:
                    finance = self.env['credit.loan.financing'].search([('id', '=', application_id.financing_id.id)], limit=1)
                    finance.write({
                        'status': 'active',
                        })
                    application_id.write({
                        'state': True
                    })
                    print('Financing Account for {} is {}'.format(application_id.partner_id.name, finance.id))
                    print('Lead Account for {} is {}'.format(application_id.partner_id.name, application_id.id))

                self.date_confirmed = fields.Datetime.now()
                self.status = 'confirm'

            else:
                raise ValidationError(_('Group Leader hasn\'t attended any of the information meeting yet.'))
        except Exception as e:
            raise UserError(_("ERROR: 'confirm_group' "+str(e)))

    @api.one
    def draft_group(self):
        try:
            self.state = 'inactive'
            if self.env['credit.loan.evaluation'].search([('group_id.id', '=', self.id), ('status', '=', 'ongoing')],
                                                          limit=1):
                raise UserError(_('Cancel all evaluations for this group first!'))
            for application in self.application_ids:
                order = self.env['sale.order'].search([('opportunity_id.id', '=', application.id)], limit=1)
                if self.env['crm.lead'].search([('id', '=', application.id)], limit=1):
                    try:
                        if order:
                            order.unlink()
                        if self.env['credit.client.investigation'].search([('application_id', '=', application.id),('status','=','ongoing')],limit=1):
                            raise UserError(_('Cancel all investigations for this group first!'))

                    except Exception as e:
                        raise UserError(_("ERROR: 'draft_group' "+str(e)))
                    finally:
                        application.write({
                            'state': False,
                            'status': 'draft'
                        })
            self.status = 'draft'
        except Exception as e:
            raise UserError(_("ERROR: 'draft_group' "+str(e)))

    @api.one
    def cancel_group(self):
        return True

    @api.multi
    def unlink(self):
        try:
            if self.status != 'draft':
                raise UserError(_('Set to draft first before deleting.'))

            for application in self.application_ids:
                application.unlink()

            return super(LoanGroup, self).unlink()
        except Exception as e:
            raise UserError(_("ERROR: 'unlink' "+str(e)))


# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)

class LoanClient(models.Model):
    _inherit = 'res.partner'

    group_id = fields.Many2one('credit.loan.group','Group', required_if_type='member')

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    group_id = fields.Many2one('credit.loan.group','Group', required_if_type='group')
    name = fields.Char(related="group_id.name", string="Name", required=False, store=True,
                       readonly=True, track_visibility='onchange')

class LoanGroup(models.Model):
    _name = 'credit.loan.group'

    name = fields.Char()
    index = fields.Integer()
    code = fields.Char(readonly=True)
    state = fields.Selection([('active', 'Active'),('inactive','Inactive')], default='active')
    status = fields.Selection([('draft','Draft'),('confirm','Confirmed')], default='draft')
    members = fields.One2many('res.partner','group_id','Members', domain=[('type','=','member')], default=lambda self:self.contact_person)
    creator = fields.Many2one('res.partner', domain=[('type','=','member')], string='Created by:', default = lambda self:self.env.user.partner_id)
    date_organized = fields.Datetime(string='Date organized', default=fields.Datetime.now())
    date_approved = fields.Datetime(string='Date approved')
    contact_person = fields.Many2one('res.partner', domain=[('type','=','member')],string='Contact Person', default= lambda self:self.env.user.partner_id)
    group_leader = fields.Many2one('res.partner', 'Group Leader', domain=[('type','=','member')])
    street = fields.Char(related= 'contact_person.street')
    street2 = fields.Char(related= 'contact_person.street2')
    zip = fields.Char(change_default=True, related= 'contact_person.zip')
    city = fields.Char(related= 'contact_person.city')
    state_id = fields.Many2one(related='contact_person.state_id')
    country_id = fields.Many2one(related='contact_person.country_id')
    area_id = fields.Many2one('res.area','Area',default=lambda self:self.default_area(), store=True)
    do = fields.Many2one('res.partner', 'Development Officer', default=lambda self:self.default_do(), store=True)

    @api.onchange('contact_person')
    def _get_area(self):
        if self.contact_person.area_id:
            self.area_id = self.contact_person.area_id
        else:
            self.area_id = self.env['res.area'].search([('street2','=',self.street2),
                                            ('city','=',self.city)], order='name desc', limit=1)
    @api.multi
    def default_area(self):
        return self.env['res.area'].search([('street2','=',self.street2),
                                            ('city','=',self.city)], order='name desc', limit=1)

    @api.multi
    def default_do(self):
        return self.area_id.officer_id

    @api.onchange('contact_person')
    def _get_do(self):
        self.do = self.area_id.officer_id

    @api.model
    def create(self, values):
        print(values)
        if self.search([('contact_person.id','=',values.get('contact_person'))]):
            raise ValidationError(_('Contact person/member already in a group.'))
        else:
            values['index'] = int(self.search([], order='index desc',limit=1).index)+1
            values['code'] = '%s-%s%s' % (self.env['res.partner'].search([('id','=',values.get('do'))],limit=1).code,str(self.env['res.partner'].search([('id','=',values.get('do'))],limit=1).index),"{0:0=2d}".format(values['index']))
            values['name'] = values['code']
            group = super(LoanGroup, self).create(values)
            self.env['res.partner'].search([('id','=', group.contact_person.id)]).write({'group_id':group.id, 'area_id':group.area_id.id})
            return group


    @api.one
    def confirm_group(self):
        if self.event_registration_id:
            for member in self.members:
                finance = self.env['credit.loan.financing'].search([('group_id','=',self.id),('member_id','=',member.id)], limit=1)
                print(finance)
                if finance:
                    finance.write({
                        'branch_id': self.area_id.branch_id.id,
                        'status': 'active',
                    })
                    application = self.env['credit.loan.application'].search([('financing_id','=',finance.id)], limit=1)
                    print(application)
                    if application:
                        application.write({
                            'state': True
                        })
                    else:
                        self.env['credit.loan.application'].create({
                            'financing_id': finance.id,
                            'state': True
                        })
                else:

                    financing = self.env['credit.loan.financing'].create({
                        'group_id':self.id,
                        'branch_id': self.area_id.branch_id.id,
                        'status':'active',
                        'member_id': member.id
                    })
                    self.env['credit.loan.application'].create({
                        'financing_id': financing.id,
                        'state': True
                    })

            if self.env['credit.loan.financing'].search(
                    [('group_id', '=', self.id), ('member_id', 'not in', [m.id for m in self.members])], limit=1):
                for rec in self.env['credit.loan.financing'].search(
                        [('group_id', '=', self.id), ('member_id', 'not in', [m.id for m in self.members])]):
                    try:
                        for loan_application in rec.loan_applications:
                            loan_application.unlink()
                        rec.unlink()
                    except Exception as e:
                        raise ValidationError(_(str(e)))

            self.status = 'confirm'

        else:
            raise ValidationError(_('Group Leader hasn\'t attended any of the information meeting yet.'))

    @api.one
    def draft_group(self):
        self.env['credit.loan.financing'].search([('group_id.id','=',self.id)]).write({
            'status':'archive'
        })
        self.status = 'draft'

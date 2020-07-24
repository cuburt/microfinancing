# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

class ResPartnerSuffix(models.Model):
    _name = 'res.partner.suffix'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    _mail_post_access = 'read'

    _sql_constraints = [('unique_name', 'unique(name)', 'Suffix Already exists.')]
    name = fields.Char(string="Suffix", required=True, index=True)
    shortcut = fields.Char(string="Abbreviation", required=True)

    @api.constrains('name')
    def _validate_name(self):
        id = self.id
        name = self.name
        res = self.search([['name', '=ilike', name], ['id', '!=', id]])
        if res:
            raise ValidationError(_("Suffix Name already exists."))

    @api.constrains('shortcut')
    def _validate_name(self):
        id = self.id
        shortcut = self.shortcut
        res = self.search([['shortcut', '=ilike', shortcut], ['id', '!=', id]])
        if res:
            raise ValidationError(_("Suffix Abbreviation already exists."))

class LoanClient(models.Model):
    _inherit = 'res.partner'

    code = fields.Char()
    short_code = fields.Char()
    index = fields.Integer()
    type = fields.Selection([('member','Member'),
                             ('do','Development Officer'),
                             ('ds','Development Supervisor'),
                             ('ao','Account Officer'),
                             ('bm','Branch Manager'),
                             ('gm','General Manager')], default='member', string='User Type')

    branch_id = fields.Many2one('res.branch','Branch', required_if_type=['bm','ao','ds','do'])
    parent_id = fields.Many2one('res.partner','Supervisor', required_if_type='do', domain=[('type','=','ds')])
    # @api.model
    # def hash_code(self, code):
    #     return str(base64.b64encode(str(code).encode('UTF-8')), 'UTF-8')
    #
    # @api.model
    # def decode_hash(self, code):
    #     return int(base64.b64decode(code if code else self.hash_code(0)))
    #
    # @api.model
    # def create(self, values):
    #     values['code'] = self.hash_code((int(self.decode_hash(self.search([], order='code asc', limit=1).code)) +1))
    #     return super(LoanClient, self).create(values)

    @api.model
    def create(self, values):
        values['index'] = int(self.search(['type','=', values.get('type')]).index)+1
        values['code'] = '%s-%s' % ("{0:0=2d}".format(values.get('branch_id').index),"{0:0=2d}".format(values['index']))
        values['short_code'] = '%s-%s' % ("{0:0=2d}".format(values.get('branch_id').index),"{0:0=2d}".format(values['index']))
        return super(LoanClient, self).create(values)

class LoanFinancing(models.Model):
    _name = 'credit.loan.financing'
    _rec_name = 'name'
    _description = 'Loan Microfinancing'
    _order = 'write_date desc'

    # client_id = fields.Many2one(comodel_name='credit.loan.client', string='Client', required=True)
    code = fields.Char()
    type = fields.Selection([('group','Group/Selda Loan')], default='group')
    cosigner_id = fields.Many2one(comodel_name='res.partner', string='Cosigner')
    date_created = fields.Datetime(default=fields.Datetime.now())
    branch_id = fields.Many2one('res.branch','Branch')

class ResBranch(models.Model):
    _name = 'res.branch'

    name = fields.Char()
    index = fields.Integer()
    code = fields.Char()
    financing_ids = fields.One2many('credit.loan.financing','branch_id','Loan Accounts')
    area_ids = fields.One2many('res.area','branch_id','Area')
    bm = fields.Many2one('res.partner','Branch Manager',domain=[('type','=','bm')])
    gm = fields.Many2one('res.partner','General Manager',domain=[('type','=','gm')])
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    @api.model
    def create(self, values):
        values['index'] = int(self.search([]).index)+1
        values['name'] = '%s - %s' % (values.get('name'), values.get('code'))
        return super(ResBranch, self).create(values)

class ResArea(models.Model):
    _name = 'res.area'

    name = fields.Char(compute='_get_name')
    code = fields.Char(related='do.short_code')
    branch_id = fields.Many2one('res.branch','Branch')
    group_ids = fields.One2many('credit.loan.group','area_id','Groups')
    do = fields.Many2one('res.partner','Assigned DO',domain=[('type','=','do')])
    city = fields.Char(related='branch_id.city',string='City')
    street2 = fields.Char()

    @api.depends('street2','code')
    def _get_name(self):
        self.name = '%s - %s' % (self.code,self.street2)





# class CapacityAssesssment(models.Model):
#     _name = 'credit.capacity.assessment'
#
#
# class CreditTicket(models.Model):
#     _name = 'credit.credit.ticket'
#
#
# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'




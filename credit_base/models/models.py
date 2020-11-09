# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


#
# [loan.financing]>O---<HAS>----|-[res.branch]-|---<HAS>---O<[res.area]
#

class LoanFinancing(models.Model):
    _name = 'credit.loan.financing'
    _description = 'Loan Microfinancing'
    _order = 'write_date desc'

    name = fields.Char(readonly=True, compute='get_name')
    code = fields.Char(readonly=True)
    state = fields.Boolean(default=False)
    status = fields.Selection([('active','Active'),('archive','Archived')], default='archive')
    date_created = fields.Datetime(default=fields.Datetime.now(), readonly=True, required=True)
    member_id = fields.Many2one('res.partner','Client', required=True)
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch', 'Branch', related='member_id.branch_id')
    area_id = fields.Many2one('res.area', 'Area', related='member_id.area_id')

    @api.depends('code', 'member_id')
    def get_name(self):
        try:
            for rec in self:
                rec.name = '%s - %s' % (rec.code, rec.member_id.name)
        except Exception as e:
            raise UserError(_(str(e)))

    @api.onchange('member_id')
    def set_defaults(self):
        try:
            self.branch_id = self.member_id.branch_id
            self.area_id = self.member_id.area_id
        except Exception as e:
            raise UserError(_("ERROR: 'set_defaults' "+str(e)))

    @api.model
    def create(self, values):
        try:
            member_id = self.env['res.partner'].search([('id','=', values.get('member_id'))], limit=1)
            values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
            print(values)
            values['code'] = '%s %s - %s' % ('[TEMP]' if not bool(values.get('state')) else None,
                                               self.env['res.branch'].search([('id', '=', member_id.branch_id.id)]).code,
                                               "{0:0=2d}".format(values.get('index')))
            return super(LoanFinancing, self).create(values)
        except Exception as e:
            raise UserError(_('HERE'+ str(e)))

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


    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    code = fields.Char(readonly=True)
    short_code = fields.Char(readonly=True)
    index = fields.Integer()
    type = fields.Selection(selection_add=[('member','Member'),
                             ('do','Development Officer'),
                             ('ds','Development Supervisor'),
                             ('ao','Account Officer'),
                             ('as','Account Supervisor'),
                             ('aa','Admin Assistant'),
                             ('bm','Branch Manager'),
                             ('gm','General Manager')], default='member', string='User Type')
    type_str = fields.Char(default=lambda self:self.default_type())
    branch_id = fields.Many2one('res.branch','Branch', required_if_type=['member','bm','aa','as','ao','ds','do'], store=True)
    area_id = fields.Many2one('res.area','Area', required_if_type=['member','do'], store=True)
    area = fields.Char(related='area_id.name', string='Area')
    supervisor_id = fields.Many2one('res.partner','Supervisor', domain=[('type','in',['ds','as','aa','bm','gm'])])
    email = fields.Char(required=True)
    mobile = fields.Char(required=True)
    employees = fields.One2many('res.partner', 'parent_id', 'Employees',default=lambda self:self.child_ids, domain=[('type','!=','member')])
    members = fields.One2many('res.partner', 'parent_id', 'Members', default=lambda self:self.child_ids, domain=[('type','=','member')])

    @api.depends('name')
    def _compute_display_name(self):
        try:
            for partner in self:
                partner.display_name = partner.name
        except Exception as e:
            raise UserError(_("ERROR: '_compute_display_name' "+str(e)))

    @api.onchange('type')
    def _set_type(self):
        try:
            self.type_str = dict(self._fields['type'].selection).get(self.type)
        except Exception as e:
            raise UserError(_("ERROR: '_set_type' "+str(e)))

    @api.multi
    def default_type(self):
        try:
            return dict(self._fields['type'].selection).get(self.type)
        except Exception as e:
            raise UserError(_("ERROR: 'default_type' "+str(e)))

    # @api.multi
    # def default_branch(self):
    #     try:
    #         if self.type == 'do':
    #             return self.parent_id.branch_id
    #         else:
    #             return self.env['res.branch'].search([('street2','=',self.street2),('city','=', self.city)], limit=1)
    #     except Exception as e:
    #         raise UserError(_(str(e)))

    @api.onchange('street2', 'city', 'type')
    def _get_branch(self):
        try:
            if self.type == 'member':
                self.branch_id = self.env['res.branch'].search([('city','=', self.city)], limit=1)
                self.area_id = self.env['res.area'].search([('street2','=', self.street2)], limit=1)
            elif self.type == 'gm':
                self.branch_id = None
            else:
                self.branch_id = self.parent_id.branch_id
        except Exception as e:
            raise UserError(_("ERROR: '_get_branch' "+str(e)))

    @api.model
    def create(self, values):
        try:
            if not values['is_company']:
                group = self.env['res.groups'].sudo().search([('name', '=', values.get('type_str'))], limit=1)
                values['index'] = int(self.search([('type', '=', values.get('type'))], order='index desc', limit=1).index) + 1
                values['employee'] = True
                values['customer'] = False
                if values['type'] == 'gm':
                    company = self.env['res.company'].search([('id', '=', values.get('company_id'))], limit=1)

                    values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
                    values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
                    parent = company.partner_id
                    values['parent_id'] = parent.id

                else:
                    branch = self.env['res.branch'].search([('id', '=', values.get('branch_id'))], limit=1)

                    values['code'] = '%s-%s' % (
                    "{0:0=2d}".format(branch.index),
                    "{0:0=2d}".format(values['index']))
                    values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
                    parent = branch.related_partner
                    values['parent_id'] = parent.id

                    if values['type'] == 'member':
                        values['employee'] = False
                        values['customer'] = True

                partner = super(LoanClient, self).create(values)
                user = self.env['res.users'].sudo().create({
                    'partner_id': partner.id,
                    'login': values.get('email'),
                    'groups_id': group,
                    'company_ids': [partner.parent_id.company_id.id],
                    'company_id': parent.company_id.id
                })
                self.write({'user_id':user.id})

                return partner
            else:
                return super(LoanClient, self).create(values)
        except Exception as e:
            raise UserError(_("ERROR: 'create' "+str(e)))

class ResBranch(models.Model):
    _name = 'res.branch'

    name = fields.Char(readonly=True)
    company_id = fields.Many2one('res.company', 'Related Company', readonly=True)
    related_partner = fields.Many2one(related='company_id.partner_id', readonly=True)
    index = fields.Integer()
    code = fields.Char('Code')
    financing_ids = fields.One2many('credit.loan.financing','branch_id','Loan Accounts')
    area_ids = fields.One2many('res.area','branch_id','Area')
    manager_id = fields.One2many('res.partner','branch_id','Branch Manager',domain=[('type','=','bm')])
    manager = fields.Char(related='manager_id.name', string='Branch Manager')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char(related='manager_id.email', store=True, readonly=False)
    phone = fields.Char(related='manager_id.phone', store=True, readonly=False)
    website = fields.Char()
    vat = fields.Char(string="Tax ID", readonly=False)

    @api.model
    def create(self, values):
        try:
            if values.get('partner_id'):
                self.clear_caches()
                return super(ResBranch, self).create(values)
            values['index'] = int(self.search([], order='index desc',limit=1).index)+1
            values['name'] = '%s - %s' % (values.get('code'), "{0:0=2d}".format(values.get('index')))
            company = self.env['res.company'].create({
                'name': values.get('name'),
                'email': values.get('email'),
                'phone': values.get('phone'),
                'website': values.get('website'),
                'vat': values.get('vat')
            })

            values['company_id'] = company.id

            return super(ResBranch, self).create(values)
        except Exception as e:
            raise UserError(_(str(e)))

class ResArea(models.Model):
    _name = 'res.area'

    name = fields.Char(compute='_get_name')
    code = fields.Char(related='officer_id.short_code', store=True, readonly=True)
    branch_id = fields.Many2one('res.branch','Branch', store=True)
    group_ids = fields.One2many('credit.loan.group','area_id','Groups')
    officer_id = fields.One2many('res.partner','area_id','Assigned DO', domain=[('type','=','do')])
    officer = fields.Char(related='officer_id.name', string='Assigned DO')
    city = fields.Char(related='branch_id.city',string='City', store=True)
    street2 = fields.Char()

    @api.depends('street2','code')
    def _get_name(self):
        try:
            for rec in self:
                rec.name = '%s - %s' % (rec.code,rec.street2)
        except Exception as e:
            raise UserError(_(str(e)))


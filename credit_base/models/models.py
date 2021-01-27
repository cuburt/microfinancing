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
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True, store=True)
    area_id = fields.Many2one('res.area', 'Area', readonly=True, store=True)
    savings_ids = fields.One2many('credit.loan.savings','financing_id','Savings Account', required=True)

    # @api.depends('member_id')
    # def _compute_branch_area(self):
    #     for rec in self:
    #         rec.branch_id = rec.member_id.branch_id.id
    #         rec.area_id = rec.member_id.area_id.id
    #         print('LOAN ACCOUNT FUCCKKKK!!!!')

    @api.depends('code', 'member_id')
    def get_name(self):
        try:
            for rec in self:
                rec.name = '%s - %s' % (rec.code, rec.member_id.name)
        except Exception as e:
            raise UserError(_(str(e)))

    # @api.onchange('member_id')
    # def set_defaults(self):
    #     try:
    #         self.branch_id = self.member_id.branch_id
    #         self.area_id = self.member_id.area_id
    #     except Exception as e:
    #         raise UserError(_("ERROR: 'set_defaults' "+str(e)))

    @api.model
    def create(self, values):
        try:
            member_id = self.env['res.partner'].search([('id','=', values.get('member_id'))], limit=1)
            values['branch_id'] = member_id.branch_id.id
            values['area_id'] = member_id.area_id.id
            values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
            print('LOAN ACCOUNT CREATED', values)
            values['code'] = '%s %s-%s' % ('[TEMP]' if not bool(values.get('state')) else None,
                                               self.env['res.branch'].search([('id', '=', member_id.branch_id.id)]).code,
                                               "{0:0=2d}".format(values.get('index')))
            financing= super(LoanFinancing, self).create(values)
            self.env['credit.loan.savings'].sudo().create({
                'member_id':member_id.id,
                'financing_id':financing.id,
                'branch_id':member_id.branch_id.id,
                'area_id':member_id.area_id.id
            })
            return financing
        except Exception as e:
            raise UserError(_('HERE'+ str(e)))

#SAVINGS ACCOUNT
class LoanSavings(models.Model):
    _name = 'credit.loan.savings'
    _description = 'Savings Microfinancing'
    _order = 'write_date desc'

    name = fields.Char(readonly=True, compute='get_name')
    code = fields.Char(readonly=True)
    state = fields.Boolean(default=False)
    status = fields.Selection([('active', 'Active'), ('archive', 'Archived')], default='archive')
    date_created = fields.Datetime(default=fields.Datetime.now(), readonly=True, required=True)
    financing_id = fields.Many2one('credit.loan.financing','Loan Account')
    member_id = fields.Many2one('res.partner', 'Client')
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch', 'Branch', store=True)
    area_id = fields.Many2one('res.area', 'Area', store=True)

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
            values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
            print('LOAN SAVINGS CREATED', values)
            values['code'] = '%s %s-%s' % ('[TEMP]' if not bool(values.get('state')) else None,
                                             self.env['res.branch'].search([('id', '=', values['branch_id'])]).code,
                                             "{0:0=2d}".format(values.get('index')))
            return super(LoanSavings, self).create(values)
        except Exception as e:
            raise UserError(_('HERE' + str(e)))

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
                             ('gm','General Manager')], default='member', string='User Type', readonly=True)
    type_str = fields.Char(default=lambda self:self.default_type())
    branch_id = fields.Many2one('res.branch','Branch', required_if_type=['member','bm','aa','as','ao','ds','do'], compute='_compute_branch_area', store=True, readonly=True)
    area_id = fields.Many2one('res.area','Area', compute='_compute_branch_area',store=True)
    area = fields.Char(related='area_id.name', string='Area')
    supervisor_id = fields.Many2one('res.partner','Supervisor', domain=[('type','in',['ds','as','aa','bm','gm'])], readonly=True)
    email = fields.Char(required=True)
    phone = fields.Char(required=True)
    employees = fields.One2many('res.partner', 'parent_id', 'Employees',default=lambda self:self.child_ids, domain=[('type','!=','member')])
    members = fields.One2many('res.partner', 'parent_id', 'Members', default=lambda self:self.child_ids, domain=[('type','=','member')])
    employee = fields.Boolean(default=bool(lambda r:r.type != 'member'), help="Check this box if this contact is an Employee.")

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

    @api.depends('street2', 'city')
    def _compute_branch_area(self):
        for rec in self:
            rec.branch_id = self.env['res.branch'].sudo().search([('city', '=', rec.city)], limit=1).id
            rec.area_id = self.env['res.area'].sudo().search([('street2', '=', rec.street2)], limit=1).id
    # @api.multi
    # def default_branch(self):
    #     try:
    #         if self.type == 'do':
    #             return self.parent_id.branch_id
    #         else:
    #             return self.env['res.branch'].search([('street2','=',self.street2),('city','=', self.city)], limit=1)
    #     except Exception as e:
    #         raise UserError(_(str(e)))
    #
    # @api.onchange('street2', 'city', 'type')
    # def _get_area(self):
    #     try:
    #         if self.type in ['member','do']:
    #             self.area_id = self.env['res.area'].search([('street2','=', self.street2)], limit=1)
    #
    #     except Exception as e:
    #         raise UserError(_("ERROR: '_get_area' "+str(e)))

    # @api.model
    # def create(self, values):
    #     try:
    #         partner = super(LoanClient, self).create(values)
    #         type = values.get('type')
    #         if not values['is_company']:
    #             company = self.env['res.company'].search([('id','=',values.get('company_id'))], limit=1)
    #             values['index'] = int(
    #                 self.search([('type', '=', values.get('type'))], order='index desc', limit=1).index) + 1
    #
    #             if values['employee']:
    #                 values['customer'] = False
    #                 if type == 'gm':
    #                     values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
    #                     values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
    #                     parent = company.partner_id
    #                     values['parent_id'] = parent.id
    #
    #                 else:
    #                     branch = self.env['res.branch'].search([('related_partner','=',company.partner_id.id)], limit=1)
    #                     print(company.partner_id.id)
    #                     print(branch)
    #                     values['branch_id'] = branch.id
    #                     values['code'] = '%s-%s' % ("{0:0=2d}".format(branch.index),"{0:0=2d}".format(values['index']))
    #                     values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
    #
    #             # MEMBER
    #             else:
    #                 values['customer'] = True
    #
    #                 values['area_id'] = self.env['res.area'].search([('street2', '=', self.street2)], limit=1).id
    #
    #                 branch_id = self.env['res.branch'].search([('city', '=', values['city'])], limit=1).id
    #                 branch = self.env['res.branch'].search([('id', '=', branch_id)], limit=1)
    #
    #                 values['code'] = '%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(values['index']))
    #                 values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
    #                 parent = branch.related_partner
    #                 values['parent_id'] = parent.id
    #
    #         print(values['branch_id'])
    #         if not values['branch_id'] and type!= 'gm':
    #             pass
    #         else:
    #             return partner
    #
    #     except Exception as e:
    #         raise UserError(_("ERROR: 'create' "+str(e)))

    @api.multi
    def write(self, values):
        partner = super(LoanClient, self).write(values)
        print(values)
        try:
            type = values.get('type')
            try:
                is_company = values['is_company']
                employee = values['employee']
                print('dipuga')
            except:
                is_company = False
                employee = False
                print('yawa')
            if not is_company:
                company = self.env['res.company'].search([('id','=',values.get('company_id'))], limit=1)
                values['index'] = int(
                    self.search([('type', '=', values.get('type', 'member'))], order='index desc', limit=1).index) + 1

                if employee:
                    values['customer'] = False
                    if type == 'gm':
                        values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
                        values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
                        parent = company.partner_id
                        values['parent_id'] = parent.id

                    else:
                        branch = self.env['res.branch'].search([('id','=',values['branch_id'])])
                        values['code'] = '%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(values['index']))
                        values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))

                        if type == 'do' and values['area_id']:
                            area = self.env['res.area'].search([('id', '=', values['area_id'])], limit=1)
                            values['code'] = '%s-%s' % ("{0:0=2d}".format(area.index), "{0:0=2d}".format(partner.index))
                            values['short_code'] = '%s' % ("{0:0=2d}".format(partner.index))
                # MEMBER
                else:
                    values['customer'] = True
                    if values['city'] and values['street2']:
                        branch = self.env['res.branch'].search([('id', '=', values['branch_id'])], limit=1)
                        values['code'] = '%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(values['index']))
                        values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
                        values['parent_id'] = branch.related_partner.id
                        self.env['res.users'].sudo().search([('login', '=', values['email'])]).write({
                            'company_id':branch.company_id.id,
                            'company_ids':[(4, branch.company_id.id)],
                        })
        except Exception as e:
            print(str(e))
        finally:
            print(values)
            return partner

class ResUser(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, values):
        try:
            user = super(ResUser, self).create(values)
            partner = user.partner_id
            company = user.company_id
            company_partner = company.partner_id
            print('PARTNER_ID',partner.id)
            print('COMPANY_ID',company.id)
            print('COMPANY_PARTNER',company_partner.id)
            type = partner.type
            supervisor_type = 'ds'
            # user_type = [cat for cat in user.groups_id.search([('category_id.name','=','User types')], order='id asc')]
            # type_field = 'sel_groups'+(''.join(map(str, ['_'+str(user_type.id) for user_type in user_type])))
            try:
                category = [cat for cat in user.groups_id.search([('category_id.name', '=', 'CARE')], order='id asc')]
                category_field = 'sel_groups' + (''.join(map(str, ['_' + str(category.id) for category in category])))
                group = self.env['res.groups'].search([('id','=',values[str(category_field)])])

                if group.name == 'General Manager':
                    type = 'gm'
                    supervisor_type = False
                if group.name == 'Branch Manager':
                    type = 'bm'
                    supervisor_type = 'gm'
                if group.name == 'Admin Assistant':
                    type = 'aa'
                    supervisor_type = 'bm'
                if group.name == 'Account Supervisor':
                    type = 'as'
                    supervisor_type = 'aa'
                if group.name == 'Account Officer':
                    type = 'ao'
                    supervisor_type = 'as'
                if group.name == 'Development Supervisor':
                    type = 'ds'
                    supervisor_type = 'aa'
                if group.name == 'Development Officer':
                    type = 'do'
                    supervisor_type = 'ds'

                if supervisor_type == 'gm':
                    supervisor = self.env['res.partner'].search(
                        [('type', '=', supervisor_type), ('company_id.id', '=', company.parent_id.id)])
                else:
                    supervisor = self.env['res.partner'].search(
                        [('type', '=', supervisor_type), ('company_id.id', '=', company.id)])

                print(supervisor.name)

                if not supervisor and type == 'bm':
                    raise UserError(_('Please assign a general manager first.'))
                if not supervisor and type == 'aa':
                    raise UserError(_('Please assign a branch manager first.'))
                if not supervisor and type in ['as', 'ds']:
                    raise UserError(_('Please assign an admin assistant first.'))
                if not supervisor and type == 'ao':
                    raise UserError(_('Please assign an account supervisor first.'))
                if not supervisor and type == 'do':
                    raise UserError(_('Please assign a development supervisor first.'))

                updates = {
                'name':values.get('name'),
                'email':values.get('email'),
                'parent_id':company_partner.id,
                'company_id':company.id,
                'branch_id':self.env['res.branch'].search([('related_partner', '=', company_partner.id)], limit=1).id if type != 'gm' else False,
                'supervisor_id':supervisor.id,
                'type':type,
                'function':group.name,
                'is_company':False,
                'employee':True
            }
            except UserError as e:
                raise UserError(_(str(e)))
            except:
                print('User is member')
                updates = {
                    'name': values.get('name'),
                    'email': values.get('email'),
                    'type': type,
                    'function':'Member',
                    'is_company': False,
                    'employee': False
                }
                # print(values[str(type_field)])
                # values[str(type_field)] = self.env['res.groups'].search([('name', '=', 'Portal')]).id
            print(updates['is_company'])
            partner.sudo().write(updates)
            print('WRITTEN!')

            return user

        except Exception as e:
            raise UserError(_("ERROR: 'create' "+str(e)))

class ResBranch(models.Model):
    _name = 'res.branch'

    name = fields.Char(readonly=True)
    company_id = fields.Many2one('res.company', 'Related Company', readonly=True)
    related_partner = fields.Many2one(related='company_id.partner_id', readonly=True, store=True)
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
            values['name'] = '%s-%s' % (values.get('code'), "{0:0=2d}".format(values.get('index')))
            parent = self.env['res.company'].search([('name','=','CARE Foundation Inc.')])
            if not parent:
                raise UserError(_("Please create a company named 'CARE Foundation Inc.' first."))
            company = self.env['res.company'].create({
                'parent_id':parent.id,
                'name': values.get('name'),
                'email': values.get('email'),
                'phone': values.get('phone'),
                'website': values.get('website'),
                'vat': values.get('vat'),
            })

            values['company_id'] = company.id
            print(values['index'], values['name'], values['company_id'])
            print('PUTANGINA 5')
            return super(ResBranch, self).create(values)
        except Exception as e:
            raise UserError(_(str(e)))

    @api.multi
    def unlink(self):
        print(self)
        partner_id = self.related_partner.id
        self.env['res.company'].search([('id','=',self.company_id.id)]).unlink()
        self.env['res.partner'].search([('id','=',partner_id)]).unlink()
        return super(ResBranch, self).unlink()
    # @api.multi
    # def write(self, values):
    #     values['company_id'] = self.search([('id','=',values['id'])]).company_id.write({
    #
    #     })
    #
    #
    #     return super(ResBranch, self).write(values)

class ResArea(models.Model):
    _name = 'res.area'

    name = fields.Char(readonly=True)
    code = fields.Char(readonly=True)
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch','Branch', store=True)
    group_ids = fields.One2many('credit.loan.group','area_id','Groups')
    officer_id = fields.One2many('res.partner','area_id','Assigned DO', domain=[('type','=','do')], required=True)
    officer = fields.Char(related='officer_id.name', string='Assigned DO')
    city = fields.Char(related='branch_id.city',string='City', store=True)
    street2 = fields.Char()

    # @api.depends('street2','code')
    # def _get_name(self):
    #     try:
    #         for rec in self:
    #             rec.name = '%s - %s' % (rec.code,rec.street2)
    #     except Exception as e:
    #         raise UserError(_(str(e)))

    # @api.multi
    # def write(self, values):
    #     values['name'] = '%s - %s' % (values['code'], self.street2)
    #     return super(ResArea, self).write(values)

    @api.model
    def create(self, values):
        values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
        values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
        values['name'] = '%s-%s' % (values['code'], values['street2'])
        return super(ResArea, self).create(values)

    #TODO: SET DO CODE
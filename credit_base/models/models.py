# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.tools.misc import ustr

from odoo.exceptions import ValidationError, UserError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from ast import literal_eval

import logging
import secrets

_logger = logging.getLogger(__name__)


#
# [loan.financing]>O---<HAS>----|-[res.branch]-|---<HAS>---O<[res.area]
#
default_company = 'CARE Foundation Inc.'
class LoanFinancing(models.Model):
    _name = 'credit.loan.financing'
    _description = 'Loan Microfinancing'
    _order = 'write_date desc'

    name = fields.Char(readonly=True, compute='get_name')
    code = fields.Char(readonly=True)
    state = fields.Boolean(default=False)
    status = fields.Selection([('archive','Archived'),('active','Active'),('blacklist', 'Blacklisted')], default='archive')
    date_created = fields.Datetime(default=fields.Datetime.now(), readonly=True, required=True)
    member_id = fields.Many2one('res.partner','Client', required=True)
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True, store=True)
    company_id = fields.Many2one('res.company', related='branch_id.company_id')
    area_id = fields.Many2one('res.area', 'Area', readonly=True, store=True)
    savings_ids = fields.One2many('credit.loan.savings','financing_id','Savings Account', required=True)

    @api.depends('code', 'member_id')
    def get_name(self):
        try:
            for rec in self:
                rec.name = '%s - %s' % (rec.code, rec.member_id.name)
        except Exception as e:
            raise UserError(_(str(e)))

    @api.model
    def create(self, values):
        try:
            member_id = self.env['res.partner'].search([('id','=', values.get('member_id'))], limit=1)
            values['branch_id'] = values.get('branch_id', member_id.branch_id.id)
            values['area_id'] = values.get('area_id', member_id.area_id.id)
            values['index'] = int(self.search([('branch_id.id','=',values['branch_id'])], order='index desc', limit=1).index) + 1
            print('LOAN ACCOUNT CREATED', values)
            values['code'] = '%s %s-%s' % ('[TEMP]' if not bool(values.get('state')) else None,
                                               self.env['res.branch'].search([('id', '=', values['branch_id'])]).code,
                                               "{0:0=2d}".format(values.get('index')))
            financing= super(LoanFinancing, self).create(values)
            self.env['credit.loan.savings'].sudo().create({
                'member_id':member_id.id,
                'financing_id':financing.id,
                'branch_id':values['branch_id'],
                'area_id':values['area_id']
            })
            return financing
        except Exception as e:
            raise UserError(_('HERE'+ str(e)))

    @api.multi
    def activate_account(self):
        if self.status != 'active':
            self.status = 'active'
        else: raise UserError(_('Loan account is already active.'))

#SAVINGS ACCOUNT
class LoanSavings(models.Model):
    _name = 'credit.loan.savings'
    _description = 'Savings Microfinancing'
    _order = 'write_date desc'

    name = fields.Char(readonly=True, compute='get_name')
    code = fields.Char(readonly=True)
    status = fields.Selection([('archive', 'Archived'), ('active', 'Active'), ('blacklist', 'Blacklisted')], default='archive')
    date_created = fields.Datetime(default=fields.Datetime.now(), readonly=True, required=True)
    financing_id = fields.Many2one('credit.loan.financing','Loan Account')
    member_id = fields.Many2one('res.partner', 'Client')
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch', 'Branch', store=True)
    company_id = fields.Many2one('res.company', related='branch_id.company_id')
    area_id = fields.Many2one('res.area', 'Area', store=True)

    @api.multi
    def action_active(self):
        if self.status == 'archive':
            self.status = 'active'

    @api.multi
    def action_archive(self):
        if self.status == 'active':
            self.status = 'archive'

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
            values['index'] = int(self.search([('branch_id.id','=',member_id.branch_id.id)], order='index desc', limit=1).index) + 1
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
    branch_id = fields.Many2one('res.branch','Default Branch', required_if_type=['member','bm','aa','as','ao','ds','do'], compute='_compute_branch_area', store=True, readonly=True)
    area_ids = fields.Many2many('res.area','partner_area_rel', string='Area')
    area_id = fields.Many2one('res.area','Default Area', compute='_compute_branch_area',store=True)
    area = fields.Char(related='area_id.name', string='Area')
    supervisor_id = fields.Many2one('res.partner','Supervisor', domain=[('type','in',['ds','as','aa','bm','gm'])], readonly=True)
    email = fields.Char(required=True)
    phone = fields.Char(required=True)
    mobile = fields.Char(required=True)
    employees = fields.One2many('res.partner', 'parent_id', 'Employees',default=lambda self:self.child_ids, domain=[('type','!=','member')])
    members = fields.One2many('res.partner', 'parent_id', 'Members', default=lambda self:self.child_ids, domain=[('type','=','member')])
    employee = fields.Boolean(default=bool(lambda r:r.type != 'member'), help="Check this box if this contact is an Employee.")
    # token = fields.Char(required=True)

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

    @api.multi
    def write(self, values):
        print('UPDATE:', values)
        try:
            if 'is_company' in values and not values['is_company']:
                print('STEP 1')
                print(values)
                try:
                    company = self.env['res.company'].search([('id','=',values['company_id'])], limit=1)
                except:
                    print('NO COMPANY_ID')
                    pass

                if ('type' in values and values['type'] == 'gm') and ('employee' in values and values['employee']):
                    print('GM WRITE')
                    index = int(self.env['res.partner'].sudo().search([('type', '=', 'gm')], order='index desc',limit=1).index) + 1
                    values['code'] = '%s' % ("{0:0=2d}".format(index))
                    values['short_code'] = '%s' % ("{0:0=2d}".format(index))
                    values['parent_id'] = company.partner_id.id
                    values['index'] = index

                elif 'type' in values and values['type'] == 'do':
                    print('DO WRITE NO AREA')
                    index = (self.env['res.partner'].sudo().search([('type', '=', 'do')], order='index desc', limit=1).index) + 1
                    values['code'] = '[NO AREA ASSIGNED]-%s' % ("{0:0=2d}".format(index))
                    values['short_code'] = '%s' % ("{0:0=2d}".format(index))
                    values['parent_id'] = company.partner_id.id
                    values['index'] = index

                elif ('type' in values and values['type'] not in ['gm','do','member'] and not False) and ('employee' in values and values['employee']):
                    print('OTHER WRITE')
                    index = int(self.env['res.partner'].sudo().search([('type', 'not in', ['gm','do'])], order='index desc',limit=1).index) + 1
                    branch = self.env['res.branch'].search([('id','=',values['branch_id'])])
                    values['code'] = '%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(index))
                    values['short_code'] = '%s' % ("{0:0=2d}".format(index))
                    values['parent_id'] = company.partner_id.id
                    values['index'] = index

            # MEMBER

                elif ('customer' in values and values['customer']) or ('type' in values and values['type'] == 'member'):
                    print('MEMBER WRITE')
                    index = int(self.env['res.partner'].sudo().search([('type', '=', values['type'])], order='index desc',
                                            limit=1).index) + 1
                    if 'city' in values:
                        branch = self.env['res.branch'].search(['|',('id', '=', values['branch_id']),('city','=',values['city'])], limit=1)
                        values.update({
                            'code':'%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(index)),
                            'short_code': '%s' % ("{0:0=2d}".format(index)),
                            'parent_id': branch.related_partner.id,
                            'branch_id': branch.id,
                            'company_id': branch.company_id.id
                        })
                        self.env['res.users'].sudo().search([('login', '=', values['email'])]).write({
                            'company_id':branch.company_id.id,
                            'company_ids':[(4, branch.company_id.id)],
                        })

                        print(self.display_name)
                        print([rec.name for rec in self.env['credit.loan.financing'].sudo().search([])])
                        if self.display_name not in [rec.name for rec in
                                                     self.env['credit.loan.financing'].sudo().search([])]:
                            self.env['credit.loan.financing'].sudo().create({
                                'member_id': self.id,
                                'branch_id': branch.id
                            })
                    values.update({'index':index})


                print(values)

            elif self.type == 'do' and not any(key in values for key in ['vat','credit_limit','property_product_pricelist','debit_limit','property_account_payable_id','property_account_receivable_id','property_account_position_id','property_payment_term_id','property_supplier_payment_term_id','last_time_entries_checked']):
                print('STEP 2')
                print(values)

                company = self.env['res.company'].search([('partner_id.id', '=', self.parent_id.id)], limit=1)

                if 'type' not in values and self.type == 'do':
                    print('DO WRITE')
                    try:
                        area = values['area_ids']
                        print(area)
                        area_id = area[0][2]
                    except:
                        area_id = False
                    print(area_id)
                    if area_id:
                        print('DO WRITE WITH AREA')
                        try:
                            self.code.index('[NO AREA ASSIGNED]')
                        except ValueError:
                            pass
                        else:
                            area = self.area_ids.search(['|',('id', '=', area_id),('id', 'in', area_id)], order='index asc', limit=1)
                            values['code'] = '%s-%s' % ("{0:0=2d}".format(area.index), "{0:0=2d}".format(self.index))
                            values['short_code'] = '%s' % ("{0:0=2d}".format(self.index))
                            values['parent_id'] = company.partner_id.id
                            values['index'] = self.index

                    elif not area_id or 'area_ids' not in values:
                        print('DO WRITE NO AREA')
                        y = self.index
                        z = self.env['res.partner'].sudo().search([('type', '=', 'do'), ('id', '!=', self.id)],
                                                                  order='index desc', limit=1).index
                        print(y)
                        print(z)
                        index = ((z + 1) * (1 - (bool(y)))) + y
                        values['code'] = '[NO AREA ASSIGNED]-%s' % ("{0:0=2d}".format(index))
                        values['short_code'] = '%s' % ("{0:0=2d}".format(index))
                        values['parent_id'] = company.partner_id.id
                        values['index'] = index
            else:
                try:
                    print('MEMBER WRITE')
                    type = values.get('type', self.type)
                    index = int(
                        self.env['res.partner'].sudo().search([('type', '=', type)], order='index desc',
                                                              limit=1).index) + 1
                    if 'city' in values:
                        branch = self.env['res.branch'].search([('city', '=', values['city'])], limit=1)
                        values.update({
                            'code': '%s-%s' % ("{0:0=2d}".format(branch.index), "{0:0=2d}".format(index)),
                            'short_code': '%s' % ("{0:0=2d}".format(index)),
                            'parent_id': branch.related_partner.id,
                            'branch_id': branch.id,
                            'company_id': branch.company_id.id
                        })
                        self.env['res.users'].sudo().search([('login', '=', values['email'])]).write({
                            'company_id': branch.company_id.id,
                            'company_ids': [(4, branch.company_id.id)],
                        })

                        print(self.display_name)
                        print([rec.name for rec in self.env['credit.loan.financing'].sudo().search([])])
                        if self.display_name not in [rec.name for rec in
                                                     self.env['credit.loan.financing'].sudo().search([])]:
                            self.env['credit.loan.financing'].sudo().create({
                                'member_id': self.id,
                                'branch_id':branch.id
                            })

                    values.update({'index': index})
                except Exception as e:
                    print(str(e))
                    pass

        except Exception as e:
            print(str(e))
            pass
        print(values)
        return super(LoanClient, self).write(values)

class ResUser(models.Model):
    _inherit = 'res.users'

    mobile = fields.Char(required=True)

    @api.model
    def create(self, values):
        try:
            print('CREATING USER...')
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
                'mobile':values.get('mobile'),
                'phone':values.get('mobile'),
                'parent_id':company_partner.id,
                'company_id':company.id,
                'branch_id':self.env['res.branch'].search([('related_partner', '=', company_partner.id)], limit=1).id if type != 'gm' else False,
                'supervisor_id':supervisor.id,
                'type':type,
                'function':group.name,
                'is_company':False,
                'employee':True,
                'customer':False
            }
            except UserError as e:
                raise UserError(_(str(e)))
            except:
                print('User is member')
                updates = {
                    'name': values.get('name'),
                    'email': values.get('email'),
                    'mobile':values.get('mobile'),
                    'phone':values.get('mobile'),
                    # 'company_id':self.env['res.company'].sudo().search('name','=',default_company).id,
                    'type': 'member',
                    'function':'Member',
                    'is_company': False,
                    'employee': False,
                    'customer': True
                }
                # print(values[str(type_field)])
                # values[str(type_field)] = self.env['res.groups'].search([('name', '=', 'Portal')]).id
            print(updates)
            print(updates['is_company'])
            partner.sudo().write(updates)
            print('WRITTEN!')

            return user

        except Exception as e:
            raise UserError(_("ERROR: 'create' "+str(e)))

    @api.model
    def signup(self, values, token=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                if not partner_user.login_date:
                    partner_user._notify_inviter()
                return (self.env.cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                partner_user = self._signup_create_user(values)
                partner_user._notify_inviter()
        else:
            # no token, sign up an external user
            values['email'] = values.get('email') or values.get('login')
            values['mobile'] = values.get('mobile')
            self._signup_create_user(values)

        return (self.env.cr.dbname, values.get('login'), values.get('password'))


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

            try:
                for account in self.env['account.account'].sudo().search([('company_id.id','=',parent.id)]):
                    self.env['account.account'].sudo().create({
                        'code':account.code,
                        'name':account.name,
                        'user_type_id':account.user_type_id.id,
                        'company_id':company.id,
                        'reconcile':True
                    })

                try:
                    company.partner_id.property_account_receivable_id = self.env['account.account'].sudo().search(
                        [('internal_type', '=', 'receivable'), ('deprecated', '=', False),
                         ('company_id.id', '=', company.id), ('code', '=', '11710')])
                    company.partner_id.property_account_payable_id = self.env['account.account'].sudo().search(
                        [('internal_type', '=', 'payable'), ('deprecated', '=', False),
                         ('company_id.id', '=', company.id), ('code', '=', '00000')])
                except:
                    raise UserError(_('Set accounting entries for main company first.'))

            except Exception as e:
                raise ValidationError(_("A problem was encountered while migrating chart of accounts. Please contact site administrator immediately. ERROR: 'create' : "+str(e)))

            try:
                for term in self.env['account.payment.term'].sudo().search([('company_id.id','=',parent.id)]):
                    self.env['account.payment.term'].sudo().create({
                        'name':term.name,
                        'note':term.note,
                        'line_ids':term.line_ids,
                        'company_id':company.id
                    })
            except Exception as e:
                raise ValidationError(_("A problem was encountered while migrating payment terms. Please contact site administrator immediately. ERROR: 'create' : "+str(e)))

            try:
                # UNPAID PURCHASE | PAYMENT ON CREDIT | DEBIT:OTHER ASSETS(EQUIPMENT), CREDIT:LIABILITIES(PAYABLE)
                purchase_credit = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Purchase Credit Journal',
                    'type': 'purchase',
                    'code': 'LBT',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(purchase_credit.name + ' created for company ' + company.name)

                # PAID PURCHASE | PAYMENT ON CASH | LOAN DISBURSEMENT | CASH OUTFLOW | DEBIT:EXPENSE|ASSETS(EQUIPMENT/RECEIVABLES)|LIABILITIES(PAYABLE), CREDIT: ASSET(CASH/BANK)
                cash_payment = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cash Payment Journal',
                    'type': 'purchase',
                    'code': 'EXP',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(cash_payment.name + ' created for company ' + company.name)

                # FOR UNPAID LOANS | RECEIPT ON CREDIT | LOAN COLLECTION | CASH INFLOW | DEBIT:ASSET(RECEIVABLE), CREDIT:REVENUE
                receipt_credit = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Receivable Journal',
                    'type': 'sale',
                    'code': 'RCV',
                    'company_id': company.id,
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(receipt_credit.name + ' created for company ' + company.name)

                # FOR PAID LOANS | RECEIPT ON CASH | LOAN COLLECTION | CASH INFLOW | DEBIT:ASSET(CASH/BANK), CREDIT:ASSET(RECEIVABLE)
                bank_loan_collection = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cheque Receipt Journal',
                    'type': 'bank',
                    'code': 'BNK',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(bank_loan_collection.name + ' created for company ' + company.name)
                cash_loan_collection = self.env['account.journal'].sudo().create({
                    'name': company.name + ' Cash Receipt Journal',
                    'type': 'cash',
                    'code': 'CSH',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(cash_loan_collection.name+' created for company '+company.name)

                general_journal = self.env['account.journal'].sudo().create({
                    'name': 'General Journal',
                    'type': 'general',
                    'code': 'GJ',
                    'company_id': company.id
                    # 'default_debit_account_id':
                    # 'default_credit_account_id':
                })
                print(general_journal.name + ' created for company ' + company.name)
            except Exception as e:
                raise ValidationError(_("A problem was encountered while migrating account journals. Please contact site administrator immediately. ERROR: 'create' : "+str(e)))

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

class ResArea(models.Model):
    _name = 'res.area'

    name = fields.Char(readonly=True)
    code = fields.Char(readonly=True)
    index = fields.Integer()
    branch_id = fields.Many2one('res.branch','Branch', store=True)
    group_ids = fields.One2many('credit.loan.group','area_id','Groups')
    officer_ids = fields.Many2many('res.partner','partner_area_rel', string='Assigned Officer', domain=[('type','=','do')], required=True)
    officer = fields.Char(related='officer_ids.name', string='Assigned Officer')
    city = fields.Char(related='branch_id.city',string='City', store=True)
    street2 = fields.Char()

    @api.multi
    def write(self, values):
        area = super(ResArea, self).write(values)
        for officer in self.officer_ids:
            officer.sudo().write({'area_ids': [[6, False, [self.id]]]})
        return area

    @api.model
    def create(self, values):
        values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
        values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
        values['name'] = '%s-%s' % (values['code'], values['street2'])
        return super(ResArea, self).create(values)

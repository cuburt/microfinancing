# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

def _get_bmi_state(bmi):
    bmi_state = None
    if bmi < 18.5:
        bmi_state = 'under'
    elif bmi >= 18.5 and bmi <= 24.9:
        bmi_state = 'normal'
    elif bmi >= 20 and bmi <= 29.9:
        bmi_state = 'over'
    elif bmi >= 40:
        bmi_state = 'obese'

    return bmi_state

def compute_height_cm(ft, inc):
    height = 0.0
    if ft:
        height = ft * 12
    if inc:
        height = height + inc
    if height > 0:
        height = height * 2.54

    return height

class ConfigName(models.Model):
    _name = 'config.names'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    _mail_post_access = 'read'

    _sql_constraints = [('unique_name', 'unique(name)', 'Name Already exists.')]
    name = fields.Char(string="Name", required=True, index=True)

    def init(self):
        self._cr.execute("""
        insert into config_names (name)select name from (
            select name from (
                select distinct name from (
                select replace(replace(replace(replace(replace(replace(last_name,', Jr.',''),' Jr.',''),' Jr',''),'Iii',''),'Ii',''),'Vii','') as name
                from hr_employee
                union all
                select replace(replace(replace(replace(replace(replace(first_name,', Jr.',''),' Jr.',''),' Jr',''),'Iii',''),'Ii',''),'Vii','') as name
                from hr_employee
                union all
                select replace(replace(middle_name,', Jr.',''),'Jr.','') as name
                from hr_employee) x
                where length(name) > 1
                order by 1) y where lower(right(name,3)) != 'xxx'
                and lower(right(name,2)) != 'xx'
                and lower(right(name,2)) != ' x') a
                where name not in
                (select name from config_names)
                group by 1
        """)
        self._cr.commit()

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

class LoanOfficer(models.Model):
    _name = 'micro.loan.officer'

    partner_id = fields.Many2one('res.partner', string='Employee')
    partner_type = fields.Many2one('res.partner.type', 'Client Type', required=True, domain="[('active','=',True)]",
                                   default='Employee')
    # employee_type =
class LoanClient(models.Model):
    _name = 'micro.loan.client'

    @api.one
    @api.depends('client_id')
    def _compute_client_id(self):
        self.name_related = self.client_id.name

        pass

    @api.one
    @api.depends('birthdate')
    def _compute_age(self):
        if self.birthdate:
            bday = datetime.strptime(self.birthdate, '%Y-%m-%d').date()
            if bday < date.today():
                self.age = relativedelta(date.today(), bday).years

    @api.one
    @api.depends('height_ft', 'height_in')
    def _get_height_cm(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        if self.height_ft or self.height_in:
            self.height = compute_height_cm(self.height_ft, self.height_in)

        pass

    @api.model
    def _default_image(self):
        image_path = get_module_resource('loan_base', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    partner_id = fields.Many2one('res.partner', string='Customer')
    name_related = fields.Char(related='partner_id.name', string="Partner Name", readonly=True, store=True)
    lastname = fields.Many2one(comodel_name="config.names", string="Last Name", required=False,
                               track_visibilty='onchange')
    firstname = fields.Many2one(comodel_name="config.names", string="First Name", required=False,
                                track_visibilty='onchange')
    middlename = fields.Many2one(comodel_name="config.names", string="Middle Name", required=False,
                                 track_visibilty='onchange')
    suffix = fields.Many2one(comodel_name="res.partner.suffix", string="Suffix", required=False,
                             track_visibilty='onchange')
    partner_type = fields.Many2one('res.partner.type', 'Client Type', required=True, domain="[('active','=',True)]",
                                   default='Customer')
    image = fields.Binary("Photo", default=_default_image, attachment=True,
                          help="This field holds the image used as photo for the Customer, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
                                 help="Medium-sized photo of the employee. It is automatically "
                                      "resized as a 128x128px image, with aspect ratio preserved. "
                                      "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
                                help="Small-sized photo of the employee. It is automatically "
                                     "resized as a 64x64px image, with aspect ratio preserved. "
                                     "Use this field anywhere a small image is required.")
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True,
                                 default=lambda self: self.env.user.company_id)
    loan_id = fields.Many2one("micro.loan.financing", "Loans", required=False)
    user_id = fields.Many2one('res.users', string='User',
                              help='Related user name for the resource to manage its access.',
                              track_visibilty='onchange')
    login = fields.Char(related='user_id.login', readonly=True)
    last_login = fields.Datetime(related='user_id.login_date', string='Latest Connection', readonly=True)
    birthdate = fields.Date(string="Date of Birth", required=False)
    age = fields.Integer(string="Age", required=False, compute=_compute_age, readonly=True, store=True)
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'),
                                                          ('female', 'Female'),
                                                          ('other', 'Other'), ], required=False)
    place_of_birth = fields.Char(string="Place of Birth", required=False, )
    marital = fields.Selection(string="Marital Status", selection=[('single', 'Single'),
                                                                   ('married', 'Married'),
                                                                   ('widower', 'Widower'),
                                                                   ('singleparent', 'Single Parent'),
                                                                   ('separated', 'Separated'), ], required=False,
                                                                    track_visibilty='onchange')
    children = fields.Integer(string="Children", required=False)
    height = fields.Float(string="Height(cm)", required=False, compute=_get_height_cm, store=True, default=None)
    height_ft = fields.Integer(string="Height(Ft)", required=False, default=None)
    height_in = fields.Integer(string="Height(inch)", required=False, default=None)
    weight = fields.Float(string="Weight(kg)", required=False)
    bmi = fields.Float(string="BMI", required=False, compute='_compute_bmi')
    bmi_state = fields.Selection(string="State", selection=[('under', 'Underweight'),
                                                            ('normal', 'Normal'),
                                                            ('over', 'Overweight'),
                                                            ('obese', 'Obese'), ], compute='_compute_bmi')
    religion_id = fields.Many2one(comodel_name="hr.religion", string="Religion", required=False)
    tribe_id = fields.Many2one(comodel_name="res.partner.tribe", string="Tribe", required=False)
    st_address = fields.Char(string="Street", required=False)
    st_address2 = fields.Char(string="Street2", required=False)
    barangay_id = fields.Many2one(comodel_name="config.barangay", string="Barangay", required=True)
    prev_address = fields.Char(string="Previous Address", required=False, compute='_compute_previous_address')
    prev_address_ids = fields.One2many(comodel_name="loan.client.address.history", inverse_name="client_id",
                                       string="Previous Address", required=False)
    municipality_id = fields.Many2one(comodel_name="config.municipality", string="Municipality/City", required=False,
                                      related='barangay_id.municipality_id', readonly=True)
    province_id = fields.Many2one(comodel_name="config.province", string="Province", required=False,
                                  related='municipality_id.province_id', readonly=True)
    region_id = fields.Many2one(comodel_name="config.region", string="Province", required=False,
                                related='province_id.region_id', readonly=True)
    zipcode_id = fields.Many2one(comodel_name="config.zipcode", string="Zip Code", required=False,
                                 related='municipality_id.zipcode_id', readonly=True)
    citizenship_id = fields.Many2one(comodel_name="res.country", string="Citizenship", required=False,
                                     default=lambda self: self.env.user.partner_id.country_id)
    spouse_id = fields.Many2one(comodel_name="loan.client", string="Spouse", required=False, track_visibilty='onchange')
    marital_spouse_readonly = fields.Boolean()
    parent_id = fields.Many2one(comodel_name="loan.client", string="Parent Record", required=False)
    child_ids = fields.One2many(comodel_name="loan.client", inverse_name="parent_id", string="Child Record",
                                required=False)
    fb_me = fields.Char(string="Facebook", required=False)
    tw_me = fields.Char(string="Twitter", required=False)
    ig_me = fields.Char(string="Instagram", required=False)

    @api.multi
    def update_loan_client(self):
        self.init()
        self._cr.execute("""insert into micro_loan_client (partner_id, user_id)
                select id, user_id from res_partner
                where user_id > 1 and id not in (select partner_id from loan_client)
            """)
        self._cr.commit()

    @api.multi
    def create_user(self):
        if self.user_id:
            raise ValidationError(_("User already exists."))
        else:
            found = self.env['res.users'].sudo().search([['name', '=ilike', self.name]])
            if found:
                self.user_id = found.id
            elif not found:
                series = '0001'
                if self.company_id.parent_id:
                    company = [(4, self.company_id.id), (4, self.company_id.parent_id.id)]
                else:
                    company = [(4, self.company_id.id)]
                login = fields.Date.today()[2:7]
                res = self.env['res.users'].sudo().search([['login', 'ilike', login]], order='login desc', limit=1)
                if res:
                    series = str(int(res.login[4:]) + 1).zfill(4)
                login = '%s%s' % (login, series)
                user_id = self.env['res.users'].sudo().create({'name': self.name,
                                                               'login': login,
                                                               'password': login,
                                                               'company_ids': company,
                                                               'company_id': self.company_id.id})
                self.user_id = user_id.id

        # @api.onchange('company_type')
        # def _onchange_company_type(self):
        #     if self.company_type == 'company':
        #         self.lastname = None
        #         self.firstname = None
        #         self.middlename = None
        #         self.prefix = None
        #         self.title = None

        pass

    @api.onchange('lastname', 'firstname', 'middlename', 'suffix', 'prefix')
    def _onchange_names(self):
        name = None
        if self.lastname:
            name = self.lastname.name
        if self.firstname and name:
            name = '%s, %s' % (name, self.firstname.name)
        if self.firstname and not name:
            name = '%s' % (self.firstname.name)
        if self.middlename and name:
            name = '%s %s' % (name, self.middlename.name)
        if self.middlename and not name:
            name = '%s' % (self.middlename.name)
        if self.suffix and name:
            name = '%s %s' % (name, self.suffix.shortcut)
        if self.suffix and not name:
            name = '%s' % (self.suffix.name)

        if name:
            self.name = name.title()

        is_duplicate = False

        found = self.search([('name', '=', name)], order='id asc', limit=1)
        if found:
            is_duplicate = True
        self.is_duplicate = is_duplicate

        pass

    @api.model
    def create(self, values):
        values['marital_spouse_readonly'] = False
        if values.get('type'):
            if values['type'] == 'contact':
                name = None
                res = self.env['config.names']
                if 'lastname' in values:
                    res_name = res.browse(values['lastname'])
                    if res_name:
                        name = res_name.name

                if 'firstname' in values:
                    res_name = res.browse(values['firstname'])
                    if res_name:
                        if name:
                            name = '%s, %s' % (name, res_name.name)
                        elif not name:
                            name = '%s' % (res_name.name)

                if 'middlename' in values:
                    res_name = res.browse(values['middlename'])
                    if res_name:
                        if name:
                            name = '%s %s' % (name, res_name.name)
                        elif not name:
                            name = '%s' % (res_name.name)

                if 'suffix' in values:
                    res = self.env['res.partner.suffix'].browse(values['suffix'])
                    if res:
                        if name:
                            name = '%s %s' % (name, res.shortcut)
                        elif not name:
                            name = '%s' % (self.res.name)

                if name:
                    values['name'] = name.title()

                    # error = self.search([['name', '=ilike', name]])
                    # if error:
                    #     raise ValidationError(_("Name already exists."))

        return super(LoanClient, self).create(values)

    @api.multi
    def write(self, values):
        type = values['type'] if 'type' in values else self.type
        if type == 'contact':
            name = None
            res = self.env['config.names']
            lastname = values['lastname'] if 'lastname' in values else self.lastname.id
            res_name = res.browse(lastname)
            if res_name:
                name = res_name.name

            firstname = values['firstname'] if 'firstname' in values else self.firstname.id
            res_name = res.browse(firstname)
            if res_name:
                if name:
                    name = '%s, %s' % (name, res_name.name)
                elif not name:
                    name = '%s' % (res_name.name)

            middlename = values['middlename'] if 'middlename' in values else self.middlename.id
            res_name = res.browse(middlename)
            if res_name:
                if name:
                    name = '%s %s' % (name, res_name.name)
                elif not name:
                    name = '%s' % (res_name.name)

            suffix = values['suffix'] if 'suffix' in values else self.suffix.id
            res_suffix = res.browse(suffix)
            if res_suffix:
                if name:
                    name = '%s %s' % (name, res_suffix.shortcut)
                elif not name:
                    name = '%s' % (res_suffix.name)

            if name:
                values['name'] = name.title()

                # error = self.search([['name', '=ilike', name], ['id', '!=', self.id]])
                # if error:
                #     raise ValidationError(_("Name already exists."))

            address = ''
            if 'st_address' in values or 'st_address2' in values or 'barangay_id' in values:
                if self.st_address:
                    address = '%s, ' % self.st_address
                if self.st_address2:
                    address = '%s%s, ' % (address, self.st_address2)
                if self.barangay_id:
                    address = '%s%s' % (address, self.barangay_id.name_get()[0][1])

            if address:
                values['prev_address_ids'] = [
                    (0, 0, {'client_id': self.id,
                            'address': address})]

        return super(LoanClient, self).write(values)

    @api.constrains('name', 'birthdate', 'gender')
    def _validate_name(self):
        id = self.id
        name = self.name
        birthdate = self.birthdate
        gender = self.gender
        if self.company_type == 'person':
            res = self.search([['name', '=ilike', name], ('birthdate', '=', birthdate), ['id', '!=', id]])
            if res:
                raise ValidationError(_("Name with same birthdate already exists."))

class LoanFinancing(models.Model):
    _name = 'micro.loan.financing'
    _rec_name = 'name'
    _description = 'Loan Microfinancing'
    _order = 'write_date desc, transaction_date desc'

    name = fields.Char(string="Name", required=False, store=True, default='New Customer',
                       readonly=True, track_visibility='onchange')
    client_ids = fields.One2Many('micro.loan.client', 'Clients', required=True)
    is_lone_borrower = fields.Boolean(default=lambda self:self._is_lone_borrower())
    # loan_applications = fields.One2many(comodel_name="micro.loan.application", inverse_name="financing_id", string="Source", required=False)
    transaction_date = fields.Datetime(default=fields.Datetime.now())

    @api.model
    def _is_lone_borrower(self):
        if len([i for i in self.client_ids]) > 1:
            return False
        else: return False

class CapacityAssesssment(models.Model):
    _name = 'micro.capacity.assessment'


class CreditTicket(models.Model):
    _name = 'micro.credit.ticket'


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'




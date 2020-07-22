# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api
# from dateutil.relativedelta import relativedelta
# from datetime import date, datetime
# from odoo.modules.module import get_module_resource
# from odoo import tools, _
#
# def _get_bmi_state(bmi):
#     bmi_state = None
#     if bmi < 18.5:
#         bmi_state = 'under'
#     elif bmi >= 18.5 and bmi <= 24.9:
#         bmi_state = 'normal'
#     elif bmi >= 20 and bmi <= 29.9:
#         bmi_state = 'over'
#     elif bmi >= 40:
#         bmi_state = 'obese'
#
#     return bmi_state
#
# def compute_height_cm(ft, inc):
#     height = 0.0
#     if ft:
#         height = ft * 12
#     if inc:
#         height = height + inc
#     if height > 0:
#         height = height * 2.54
#
#     return height
#
# class LoanClient(models.Model):
#     _inherit = 'credit.loan.client'
#
#     @api.one
#     @api.depends('height_ft', 'height_in')
#     def _get_height_cm(self):
#         """
#         @api.depends() should contain all fields that will be used in the calculations.
#         """
#         if self.height_ft or self.height_in:
#             self.height = compute_height_cm(self.height_ft, self.height_in)
#
#         pass
#
#     @api.one
#     @api.depends('birthdate')
#     def _compute_age(self):
#         if self.birthdate:
#             bday = datetime.strptime(self.birthdate, '%Y-%m-%d').date()
#             if bday < date.today():
#                 self.age = relativedelta(date.today(), bday).years
#
#     @api.model
#     def _default_image(self):
#         image_path = get_module_resource('loan_base', 'static/src/img', 'default_image.png')
#         return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))
#
#     def compute_height_cm(ft, inc):
#         height = 0.0
#         if ft:
#             height = ft * 12
#         if inc:
#             height = height + inc
#         if height > 0:
#             height = height * 2.54
#
#         return height
#
#     partner_type = fields.Many2one('res.partner.type', 'Client Type', required=True, domain="[('active','=',True)]",
#                                    default='Customer')
#     image = fields.Binary("Photo", default=_default_image, attachment=True,
#                           help="This field holds the image used as photo for the Customer, limited to 1024x1024px.")
#     image_medium = fields.Binary("Medium-sized photo", attachment=True,
#                                  help="Medium-sized photo of the employee. It is automatically "
#                                       "resized as a 128x128px image, with aspect ratio preserved. "
#                                       "Use this field in form views or some kanban views.")
#     image_small = fields.Binary("Small-sized photo", attachment=True,
#                                 help="Small-sized photo of the employee. It is automatically "
#                                      "resized as a 64x64px image, with aspect ratio preserved. "
#                                      "Use this field anywhere a small image is required.")
#     company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True,
#                                  default=lambda self: self.env.user.company_id)
#     loan_ids = fields.One2many("credit.loan.financing", 'client_id', "Loans", required=False)
#     user_id = fields.Many2one('res.users', string='User',
#                               help='Related user name for the resource to manage its access.',
#                               track_visibilty='onchange')
#     login = fields.Char(related='user_id.login', readonly=True)
#     last_login = fields.Datetime(related='user_id.login_date', string='Latest Connection', readonly=True)
#     birthdate = fields.Date(string="Date of Birth", required=False)
#     age = fields.Integer(string="Age", required=False, compute=_compute_age, readonly=True, store=True)
#     gender = fields.Selection(string="Gender", selection=[('male', 'Male'),
#                                                           ('female', 'Female'),
#                                                           ('other', 'Other'), ], required=False)
#     place_of_birth = fields.Char(string="Place of Birth", required=False, )
#     marital = fields.Selection(string="Marital Status", selection=[('single', 'Single'),
#                                                                    ('married', 'Married'),
#                                                                    ('widower', 'Widower'),
#                                                                    ('singleparent', 'Single Parent'),
#                                                                    ('separated', 'Separated'), ], required=False,
#                                track_visibilty='onchange')
#     children = fields.Integer(string="Children", required=False)
#     height = fields.Float(string="Height(cm)", required=False, compute=_get_height_cm, store=True, default=None)
#     height_ft = fields.Integer(string="Height(Ft)", required=False, default=None)
#     height_in = fields.Integer(string="Height(inch)", required=False, default=None)
#     weight = fields.Float(string="Weight(kg)", required=False)
#     bmi = fields.Float(string="BMI", required=False, compute='_compute_bmi')
#     bmi_state = fields.Selection(string="State", selection=[('under', 'Underweight'),
#                                                             ('normal', 'Normal'),
#                                                             ('over', 'Overweight'),
#                                                             ('obese', 'Obese'), ], compute='_compute_bmi')
#     religion_id = fields.Many2one(comodel_name="hr.religion", string="Religion", required=False)
#     tribe_id = fields.Many2one(comodel_name="res.partner.tribe", string="Tribe", required=False)
#     st_address = fields.Char(string="Street", required=False)
#     st_address2 = fields.Char(string="Street2", required=False)
#     barangay_id = fields.Many2one(comodel_name="config.barangay", string="Barangay", required=True)
#     prev_address = fields.Char(string="Previous Address", required=False, compute='_compute_previous_address')
#     prev_address_ids = fields.One2many(comodel_name="loan.client.address.history", inverse_name="client_id",
#                                        string="Previous Address", required=False)
#     municipality_id = fields.Many2one(comodel_name="config.municipality", string="Municipality/City", required=False,
#                                       related='barangay_id.municipality_id', readonly=True)
#     province_id = fields.Many2one(comodel_name="config.province", string="Province", required=False,
#                                   related='municipality_id.province_id', readonly=True)
#     region_id = fields.Many2one(comodel_name="config.region", string="Province", required=False,
#                                 related='province_id.region_id', readonly=True)
#     zipcode_id = fields.Many2one(comodel_name="config.zipcode", string="Zip Code", required=False,
#                                  related='municipality_id.zipcode_id', readonly=True)
#     citizenship_id = fields.Many2one(comodel_name="res.country", string="Citizenship", required=False,
#                                      default=lambda self: self.env.user.partner_id.country_id)
#     spouse_id = fields.Many2one(comodel_name="loan.client", string="Spouse", required=False, track_visibilty='onchange')
#     marital_spouse_readonly = fields.Boolean()
#     parent_id = fields.Many2one(comodel_name="loan.client", string="Parent Record", required=False)
#     child_ids = fields.One2many(comodel_name="loan.client", inverse_name="parent_id", string="Child Record",
#                                 required=False)
#     fb_me = fields.Char(string="Facebook", required=False)
#     tw_me = fields.Char(string="Twitter", required=False)
#     ig_me = fields.Char(string="Instagram", required=False)
#
#     @api.model
#     def create(self, values):
#         values['marital_spouse_readonly'] = False
#         if values.get('type'):
#             if values['type'] == 'contact':
#                 name = None
#                 res = self.env['config.names']
#                 if 'lastname' in values:
#                     res_name = res.browse(values['lastname'])
#                     if res_name:
#                         name = res_name.name
#
#                 if 'firstname' in values:
#                     res_name = res.browse(values['firstname'])
#                     if res_name:
#                         if name:
#                             name = '%s, %s' % (name, res_name.name)
#                         elif not name:
#                             name = '%s' % (res_name.name)
#
#                 if 'middlename' in values:
#                     res_name = res.browse(values['middlename'])
#                     if res_name:
#                         if name:
#                             name = '%s %s' % (name, res_name.name)
#                         elif not name:
#                             name = '%s' % (res_name.name)
#
#                 if 'suffix' in values:
#                     res = self.env['res.partner.suffix'].browse(values['suffix'])
#                     if res:
#                         if name:
#                             name = '%s %s' % (name, res.shortcut)
#                         elif not name:
#                             name = '%s' % (self.res.name)
#
#                 if name:
#                     values['name'] = name.title()
#
#                     # error = self.search([['name', '=ilike', name]])
#                     # if error:
#                     #     raise ValidationError(_("Name already exists."))
#
#         return super(LoanClient, self).create(values)
# #person responsible: Client & Development Officer
# class LoanFinancing(models.Model):
#     _inherit = 'credit.loan.financing'
#
#     group_id = fields.Many2one('loan.client.group','Group', required_if_type='group')
#
# class LoanGroup(models.Model):
#     _name = 'credit.loan.group'
#
#     state = fields.Selection([('draft','Draft'),('approve','Approved')])
#     members = fields.One2many('credit.loan.financing','group_id','Members', required_if_state='approve')
#
# class LoanRecommendation(models.Model):
#     _inherit = 'credit.loan.application'
#
#     state = fields.Selection(string="Status", selection_add=[('recommend', 'Recommendation')],
#                              track_visibility='onchange')
#     recommend_date = fields.Datetime('Recommendation Date', default=fields.Datetime.now(), required_if_state='recommend')
#     # RECOMMENDATION FORM
#     # CI/BI FORM
#     # COSIGNER PROFILE
#     # PROOF OF PAYMENTS
#     # ETC
#
# class LoanEndorsement(models.Model):
#     _inherit = 'credit.loan.application'
#
#     state = fields.Selection(string="Status", selection_add=[('endorse', 'Endorsement')],
#                              track_visibility='onchange')
#     endorsement_date = fields.Datetime('Endorsement Date', default=fields.Datetime.now(), required_if_state='endorse')
#     # CREDIT MEMO/CC
#     # SIGNATURE CARDS
#     # PROMISORRY NOTE
#     # COSIGNER STATEMENT
#     # DISCLOSURE STATEMENT
#     # DEED OF ASSIGN. OF DEP.
#     # SECURITY AGREEMENT
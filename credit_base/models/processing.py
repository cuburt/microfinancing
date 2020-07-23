# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
#
# class LoanClient(models.Model):
#     _inherit = 'credit.loan.client'
#
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
#     civil_status = fields.Selection(string="Marital Status", selection=[('single', 'Single'),
#                                                                    ('married', 'Married'),
#                                                                    ('widower', 'Widower'),
#                                                                    ('singleparent', 'Single Parent'),
#                                                                    ('separated', 'Separated'), ], required=False,
#                                track_visibilty='onchange')
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
#
#     active = fields.Boolean(string="Active", readonly=True, default=True, track_visibility='onchange')
#     phone = fields.Char('Landline Number', track_visibilty='onchange')
#     fax = fields.Char('FAX', track_visibilty='onchange')
#
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
#
# #person responsible: Client & Development Officer
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

    name = fields.Char(default = lambda self:self.env.user)
    state = fields.Selection([('draft','Draft'),('approve','Approved')])
    loan_account = fields.One2many('credit.loan.financing','group_id','Loan Account', required_if_state='approve')
    members = fields.One2many('res.partner','group_id','Members', domain=[('type','=','member')])
    creator = fields.Char(default = lambda self:self.env.user)

# # class LoanRecommendation(models.Model):
# #     _inherit = 'credit.loan.application'
# #
# #     state = fields.Selection(string="Status", selection_add=[('recommend', 'Recommendation')],
# #                              track_visibility='onchange')
# #     recommend_date = fields.Datetime('Recommendation Date', default=fields.Datetime.now(), required_if_state='recommend')
# #     # RECOMMENDATION FORM
# #     # CI/BI FORM
# #     # COSIGNER PROFILE
# #     # PROOF OF PAYMENTS
# #     # ETC
# #
# # class LoanEndorsement(models.Model):
# #     _inherit = 'credit.loan.application'
# #
# #     state = fields.Selection(string="Status", selection_add=[('endorse', 'Endorsement')],
# #                              track_visibility='onchange')
# #     endorsement_date = fields.Datetime('Endorsement Date', default=fields.Datetime.now(), required_if_state='endorse')
# #     # CREDIT MEMO/CC
# #     # SIGNATURE CARDS
# #     # PROMISORRY NOTE
# #     # COSIGNER STATEMENT
# #     # DISCLOSURE STATEMENT
# #     # DEED OF ASSIGN. OF DEP.
# #     # SECURITY AGREEMENT
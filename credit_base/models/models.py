# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

# class LoanServices(models.Model):
#     _inherit = 'product.product'
#
#     name = fields.Char()
#     description = fields.Text()
#     #TODO: add insurance, service fee, description, requirements

# class ConfigName(models.Model):
#     _name = 'config.names'
#     _rec_name = 'name'
#     _inherit = ['mail.thread']
#
#     _mail_post_access = 'read'
#
#     _sql_constraints = [('unique_name', 'unique(name)', 'Name Already exists.')]
#     name = fields.Char(string="Name", required=True, index=True)
#
#     def init(self):
#         self._cr.execute("""
#         insert into config_names (name)select name from (
#             select name from (
#                 select distinct name from (
#                 select replace(replace(replace(replace(replace(replace(last_name,', Jr.',''),' Jr.',''),' Jr',''),'Iii',''),'Ii',''),'Vii','') as name
#                 from hr_employee
#                 union all
#                 select replace(replace(replace(replace(replace(replace(first_name,', Jr.',''),' Jr.',''),' Jr',''),'Iii',''),'Ii',''),'Vii','') as name
#                 from hr_employee
#                 union all
#                 select replace(replace(middle_name,', Jr.',''),'Jr.','') as name
#                 from hr_employee) x
#                 where length(name) > 1
#                 order by 1) y where lower(right(name,3)) != 'xxx'
#                 and lower(right(name,2)) != 'xx'
#                 and lower(right(name,2)) != ' x') a
#                 where name not in
#                 (select name from config_names)
#                 group by 1
#         """)
#         self._cr.commit()
#
# class ResPartnerSuffix(models.Model):
#     _name = 'res.partner.suffix'
#     _rec_name = 'name'
#     _inherit = ['mail.thread']
#
#     _mail_post_access = 'read'
#
#     _sql_constraints = [('unique_name', 'unique(name)', 'Suffix Already exists.')]
#     name = fields.Char(string="Suffix", required=True, index=True)
#     shortcut = fields.Char(string="Abbreviation", required=True)
#
#     @api.constrains('name')
#     def _validate_name(self):
#         id = self.id
#         name = self.name
#         res = self.search([['name', '=ilike', name], ['id', '!=', id]])
#         if res:
#             raise ValidationError(_("Suffix Name already exists."))
#
#     @api.constrains('shortcut')
#     def _validate_name(self):
#         id = self.id
#         shortcut = self.shortcut
#         res = self.search([['shortcut', '=ilike', shortcut], ['id', '!=', id]])
#         if res:
#             raise ValidationError(_("Suffix Abbreviation already exists."))
# #
# # class LoanOfficer(models.Model):
# #     _name = 'credit.loan.officer'
# #
# #     partner_id = fields.Many2one('res.partner', string='Employee')
# #     partner_type = fields.Many2one('res.partner.type', 'Client Type', required=True, domain="[('active','=',True)]",
# #                                    default='Employee')
# #     # employee_type =
class LoanClient(models.Model):
    _name = 'credit.loan.client'

    @api.one
    @api.depends('client_id')
    def _compute_client_id(self):
        self.name_related = self.client_id.name

        pass

    code = fields.Char()
    partner_id = fields.Many2one('res.partner', string='Client')
    name_related = fields.Char(related='partner_id.name', string="Client Name", readonly=True, store=True)
    lastname = fields.Many2one(comodel_name="config.names", string="Last Name", required=False,
                               track_visibilty='onchange')
    firstname = fields.Many2one(comodel_name="config.names", string="First Name", required=False,
                                track_visibilty='onchange')
    middlename = fields.Many2one(comodel_name="config.names", string="Middle Name", required=False,
                                 track_visibilty='onchange')
    suffix = fields.Many2one(comodel_name="res.partner.suffix", string="Suffix", required=False,
                             track_visibilty='onchange')
    active = fields.Boolean(string="Active", readonly=True, default=True, track_visibility='onchange')
    email = fields.Char('Emailing Address',track_visibilty='onchange')
    phone = fields.Char('Landline Number',track_visibilty='onchange')
    fax = fields.Char('FAX',track_visibilty='onchange')
    mobile = fields.Char('Mobile Number', required=True,track_visibilty='onchange')

    @api.model
    def hash_code(self, code):
        return str(base64.b64encode(str(code).encode('UTF-8')), 'UTF-8')

    @api.model
    def create(self, values):
        values['code'] = self.hash_code(int(self.search([], order='code asc', limit=1).code or 0)+1)
        return super(LoanClient, self).create(values)

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

# class LoanFinancing(models.Model):
#     _name = 'credit.loan.financing'
#     _rec_name = 'name'
#     _description = 'Loan Microfinancing'
#     _order = 'write_date desc, transaction_date desc'
#
#     name = fields.Char(string="Name", required=False, store=True, default='New Customer',
#                        readonly=True, track_visibility='onchange')
#     client_id = fields.Many2one('credit.loan.client', 'Client', required=True)
#     type = fields.Many2one([('group','Group/Selda Loan')])
#     creation_date = fields.Datetime(default=fields.Datetime.now())
#     cosigner_id = fields.Many2one('credit.loan.client', 'Cosigner', required=True)


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




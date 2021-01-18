# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
import logging

_logger = logging.getLogger(__name__)

#
# [product.template]>O---<HAS>---|-[product.template]-|----<HAS>----|<[crm.lead]
#
class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    company_id = fields.Many2one('res.company', string='Company', required=True)

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def product_domain(self):
        try:
            return ['|',('company_id.id','=',self.env.user.company_id.id),('company_id.id','=',self.env.user.company_id.parent_id.id)]
        except Exception as e:
            raise UserError(_("ERROR: 'product_domain' "+str(e)))

    product_id = fields.Many2one('product.template', 'Applied Product', required=True, default=lambda self:self.env['product.template'].search(['&',('company_id.id','=',self.env.user.company_id.id),('categ_id.id','=',self.env['product.category'].search([('name','=','Loan Products')],limit=1).id)],limit=1), domain=product_domain)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    loanclass = fields.Selection(related='product_id.loanclass', default='individual')
    loan_amount = fields.Monetary('Loan Amount', required_if_loanclass='individual')

class productTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def term_domain(self):
        try:
            return ['|',('company_id.id','=',self.env.user.company_id.id),('company_id.id','=',self.env.user.company_id.parent_id.id)]
        except Exception as e:
            raise UserError(_("ERROR: 'term_domain' "+str(e)))

    sale_line_warn = fields.Selection(WARNING_MESSAGE, 'Sales Order Line', help=WARNING_HELP, required=False, default="no-message")
    package_id = fields.Many2one('product.template', 'Package')
    loanclass = fields.Selection([('group','Group Loan'),('individual','Individual Loan')], default=lambda self:self.package_id.loanclass)
    child_ids = fields.One2many('product.template','package_id', 'Products')
    _class = fields.Char('Classification')
    payment_schedule_type = fields.Selection([('manual','Manual'),('automatic','Automatic')], string='Payment Schedule Type')
    min = fields.Monetary('Minimum Amount')
    max = fields.Monetary('Maximum Amount')
    grace_period_principal = fields.Monetary('Grace Period - Principal')
    grace_period_interest = fields.Monetary('Grace Period - Interest')
    aging_method = fields.Selection([('microfinance','Microfinance')], 'Aging Method')
    has_collateral = fields.Boolean('Collateral', default=False)
    payment_term = fields.Many2one('account.payment.term', 'Payment Term', required_if_payment_schedule_type='automatic', domain=term_domain)
    interest_id = fields.Many2one('credit.loan.interest', 'Interest Rate', default=lambda self:self.env['credit.loan.interest'].search([], limit=1, order='date_created desc'))
    interest = fields.Float(related='interest_id.rate')

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    product_id = fields.Many2one('product.template', related='application_id.product_id')
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    loanclass = fields.Selection(related='product_id.loanclass', default='individual')
    loan_amount = fields.Monetary('Loan Amount', required_if_loanclass='group')

    @api.onchange('application_id')
    def set_members(self):
        try:
            if self.application_id:
                officer_ids = self.area_id.officer_id
                self.application_ids = self.env['crm.lead'].search(['&','&','&',('product_id.loanclass','=','group'),('product_id.id','=',self.product_id.id),('branch_id.id','=',self.branch_id.id),('area_id.id','=',self.area_id.id)])
                self.do = officer_ids[len(officer_ids) - 1]
        except Exception as e:
            raise UserError(_("Error 'set_members' @onchange "+str(e)))

    @api.model
    def create(self, values):
        print(values)
        try:
            applications = values.get('application_ids')

            #only the first list item is taken, given all member availed similar product
            application = self.env['crm.lead'].search([('id','=',applications[1][1])])
            try:
                officer_id = self.env['res.partner'].search([('id','=',values['do'])])
            except:
                officer_id = self.env['res.partner'].search([('id', '=', application.do.id)], limit=1)
            # application_ids is a 3-dimensional list. 0-2 or even-indexed list items are disregarded,
            # [[1]] or y is the index of each id in application_ids. the x is the iteration of odd-indexed
            # list items in the application_ids
            print(application)
            print(officer_id)
            if any([self.search([('application_id.id', '=', applications[x][1]),('product_id.id', '=',application.product_id.id)]) for x in range(len(applications)) if x%2!=0 and x!=0]):
                raise UserError(_('Applicant already in a group!'))
            else:
                values['index'] = int(self.search([], order='index desc',limit=1).index)+1
                values['code'] = '%s-%s%s' % (officer_id.code, str(officer_id.index),"{0:0=2d}".format(values['index']))
                values['name'] = values['code']
                group = super(LoanGroup, self).create(values)
                for application_set in values.get('application_ids'):
                    if application_set[0] == 1:
                        self.env['crm.lead'].search([('id', '=', application_set[1])]).write({'group_id': group.id})
                return group
        except Exception as e:
            raise UserError(_("ERROR: 'create' "+str(e)))

# class ProductPrice(models.Model):
#     _name = 'credit.product.price'
#
#     name = fields.Char(compute='get_name')
#     product_product_id = fields.Many2one('product.product', 'Variant')
#     product_id = fields.Many2one('product.template', 'Product', related='product_product_id.product_tmpl_id')
#     currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
#     amount = fields.Monetary('Loan Amount')
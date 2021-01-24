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



class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    product_id = fields.Many2one('product.template', related='application_id.product_id')
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    loanclass = fields.Selection(related='product_id.loanclass')
    loan_amount = fields.Monetary('Loan Amount', required_if_loanclass='group')

    @api.model
    def create(self, values):
        application = self.env['crm.lead'].sudo().search([('id','=',values['application_id'])])
        product = self.env['product.template'].sudo().search([('id','=',application.product_id.id)])
        values['product_id'] = product.id
        values['currency_id'] = product.currency_id.id
        values['loanclass'] = product.loanclass
        print('GROUP CREATE IN PRODUCT:', values)
        return super(LoanGroup, self).create(values)


# class ProductPrice(models.Model):
#     _name = 'credit.product.price'
#
#     name = fields.Char(compute='get_name')
#     product_product_id = fields.Many2one('product.product', 'Variant')
#     product_id = fields.Many2one('product.template', 'Product', related='product_product_id.product_tmpl_id')
#     currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
#     amount = fields.Monetary('Loan Amount')
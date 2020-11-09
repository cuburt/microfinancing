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
class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def product_domain(self):
        try:
            return [('company_id.id','=',self.env.user.company_id.id)]
        except Exception as e:
            raise UserError(_("ERROR: 'product_domain' "+str(e)))

    product_id = fields.Many2one('product.template', 'Applied Product', default=lambda self:self.env['product.template'].search([('company_id.id','=',self.env.user.company_id.id)],limit=1), domain=product_domain)

class productTemplate(models.Model):
    _inherit = 'product.template'

    sale_line_warn = fields.Selection(WARNING_MESSAGE, 'Sales Order Line', help=WARNING_HELP, required=False, default="no-message")
    package_id = fields.Many2one('product.template', 'Package')
    loanclass = fields.Selection([('group','Group Loan'),('individual','Individual Loan')], default=lambda self:self.package_id.loanclass)
    child_ids = fields.One2many('product.template','package_id', 'Products')

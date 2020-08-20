# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
import logging

_logger = logging.getLogger(__name__)
class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    product_id = fields.Many2one('product.product', 'Product', default=lambda self:self.env['product.product'].search([],limit=1))

class Product(models.Model):
    _inherit = 'product.product'

    availed_ids = fields.One2many('credit.loan.financing', 'product_id', 'Client Accounts')

class productTemplate(models.Model):
    _inherit = 'product.template'

    sale_line_warn = fields.Selection(WARNING_MESSAGE, 'Sales Order Line', help=WARNING_HELP, required=False, default="no-message")

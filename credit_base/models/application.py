# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

#FOR GROUPS
class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    financing_ids = fields.One2many('credit.loan.financing', 'group_id', 'Loan Account', required_if_state='approve')

class LoanClient(models.Model):
    _inherit = 'res.partner'

    financing_ids = fields.One2many('credit.loan.financing', 'member_id', 'Loan Account', required_if_state='approve')

class Lead(models.Model):
    _inherit = 'crm.lead'

    # group_id = fields.Many2one('credit.loan.group', 'Group', index=True)
    application_id = fields.Many2one('credit.loan.application','Application')
    service_applied = fields.Char(related='application_id.applied_service',string='Applied Service')

# class ProductProduct(models.Model):


#ACCOUNT FOR QUALIFIED MEMBERS
class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    loan_applications = fields.One2many(comodel_name="credit.loan.application", inverse_name="financing_id", string="Source", required=False)
    member_id = fields.Many2one('res.partner','Client')

class LoanApplication(models.Model):
    _name = 'credit.loan.application'

    # APPLICATION FORM
    financing_id = fields.Many2one('credit.loan.financing', 'Source', required=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch','Branch')
    application_date = fields.Date('Application Date', default=fields.Datetime.now(), required_if_state='confirm')
    service = fields.Many2one('product.product','Service')
    applied_service = fields.Char(related='service.name',string='Applied Service')



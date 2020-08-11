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
    product_id = fields.Many2one('product.product', related='application_id.product_id',string='Applied Service')
    financing_id = fields.Many2one('credit.loan.financing', related='application_id.financing_id')
    partner_id = fields.Many2one('res.partner', related='financing_id.member_id')

# class ProductProduct(models.Model):


#ACCOUNT FOR QUALIFIED MEMBERS/ FOR INDIVIDUAL
class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    loan_applications = fields.One2many(comodel_name="credit.loan.application", inverse_name="financing_id", string="Source", required=False)
    member_id = fields.Many2one('res.partner','Client')

class LoanApplication(models.Model):
    _name = 'credit.loan.application'

    # APPLICATION FORM
    name = fields.Char(related='financing_id.name')
    financing_id = fields.Many2one('credit.loan.financing', 'Source', required=True)
    #TODO: CONNECT TO INVOICE WHEN STATUS IS CONFIRM
    status = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch','Branch', related='financing_id.branch_id')
    application_date = fields.Datetime('Application Date', default=fields.Datetime.now(), required_if_state='confirm')
    product_id = fields.Many2one('product.product', related='financing_id.product_id')
    group_id = fields.Many2one('credit.loan.group', related='financing_id.group_id')
    # applicant_ids = fields.Many2many('res.partner', related='group_id.members')

    @api.model
    def create(self, values):
        application = super(LoanApplication, self).create(values)
        self.env['crm.lead'].create({
            'name':application.financing_id.member_id.name,
            'application_id':application.id
        })
        return application

class Invoice(models.Model):
    _inherit = 'account.invoice'

    loan_application = fields.Many2one('credit.loan.application', 'Source Document')

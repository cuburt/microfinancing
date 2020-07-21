# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    loan_applications = fields.One2many(comodel_name="micro.loan.application", inverse_name="financing_id", string="Source", required=False)

class LoanApplication(models.Model):
    _name = 'micro.loan.application'

    # APPLICATION FORM
    financing_id = fields.Many2one('micro.loan.financing', 'Source', required=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch','Branch')
    application_date = fields.Date('Application Date', default=fields.Datetime.now(), required_if_state='confirm')




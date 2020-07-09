# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanApplication(models.Model):
    _name = 'micro.loan.application'

    # APPLICATION FORM
    financing_id = fields.Many2one('micro.loan.financing', 'Source', required=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch','Branch')
    application_date = fields.Date('Application Date', default=fields.Datetime.now(), required_if_state='confirm')




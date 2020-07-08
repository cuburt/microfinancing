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

class LoanRecommendation(models.Model):
    _inherit = 'micro.loan.application'

    state = fields.Selection(string="Status", selection_add=[('recommend', 'Recommendation')],
                             track_visibility='onchange')
    recommend_date = fields.Datetime('Recommendation Date', default=fields.Datetime.now(), required_if_state='recommend')
    # RECOMMENDATION FORM
    # CI/BI FORM
    # COSIGNER PROFILE
    # PROOF OF PAYMENTS
    # ETC

class LoanEndorsement(models.Model):
    _inherit = 'micro.loan.application'

    state = fields.Selection(string="Status", selection_add=[('endorse', 'Endorsement')],
                             track_visibility='onchange')
    endorsement_date = fields.Datetime('Endorsement Date', default=fields.Datetime.now(), required_if_state='endorse')
    # CREDIT MEMO/CC
    # SIGNATURE CARDS
    # PROMISORRY NOTE
    # COSIGNER STATEMENT
    # DISCLOSURE STATEMENT
    # DEED OF ASSIGN. OF DEP.
    # SECURITY AGREEMENT

# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    loantype = fields.Selection(selection_add=[('sme','SME Loan')])
    business_id = fields.Many2one(required_if_loantype='sme')

class LoanRecommendation(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string="Status", selection_add=[('recommend', 'Recommendation')],
                             track_visibility='onchange')
    recommend_date = fields.Datetime('Recommendation Date', default=fields.Datetime.now(), required_if_status='recommend')
    # RECOMMENDATION FORM
    # CI/BI FORM
    # COSIGNER PROFILE
    # PROOF OF PAYMENTS
    # ETC

class LoanEndorsement(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string="Status", selection_add=[('endorse', 'Endorsement')],
                             track_visibility='onchange')
    endorsement_date = fields.Datetime('Endorsement Date', default=fields.Datetime.now(), required_if_status='endorse')
    # CREDIT MEMO/CC
    # SIGNATURE CARDS
    # PROMISORRY NOTE
    # COSIGNER STATEMENT
    # DISCLOSURE STATEMENT
    # DEED OF ASSIGN. OF DEP.
    # SECURITY AGREEMENT
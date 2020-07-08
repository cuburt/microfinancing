# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanOfficer(models.Model):
    _inherit = 'res.partner'

class LoanClient(models.Model):
    _inherit = 'res.partner'

class LoanFinancing(models.Model):
    _name = 'micro.loan.financing'

    is_lone_creditor = fields.Boolean()

class RepaymentCapacity(models.Model):
    _name = 'micro.repayment.capacity'

class LoanApplication(models.Model):
    _name = 'micro.loan.application'

class ClientInvestigation(models.Model):
    _name = 'micro.client.investigation'

class CIQuestionnaire(models.Model):
    _name = 'micro.client.investigation.questionnaire'

class CIScore(models.Model):
    _name = 'micro.client.investigation.score'

class LoanRecommendation(models.Model):
    _inherit = 'micro.loan.application'

class LoanEndorsement(models.Model):
    _inherit = 'micro.loan.endorsement'

class CreditTicket(models.Model):
    _name = 'micro.credit.ticket'

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'




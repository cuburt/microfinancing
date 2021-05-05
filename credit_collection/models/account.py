from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    application_id = fields.Many2one('crm.lead', 'Vouchers')


class AccountDetail(models.Model):
    _name = 'credit.loan.account.detail'

    name = fields.Char()

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    currency_id = fields.Many2one(related='company_id.currency_id')
    # account_1 = fields.Monetary(compute='_get_total_amount_for_account_1')
    # account_2 = fields.Monetary(compute='_get_total_amount_for_account_2')
    # account_3 = fields.Monetary(compute='_get_total_amount_for_account_3')
    account_total = fields.Monetary(compute='_get_loan_total')
    savings_total = fields.Monetary(compute='_get_cbu_total')


    @api.depends('loan_applications')
    def _get_loan_total(self):
        for rec in self:
            for application in rec.loan_applications:
                print("APPLICATION", application)

    @api.depends('loan_applications')
    def _get_cbu_total(self):
        for rec in self:
            for application in rec.loan_applications:
                print("APPLICATION", application)
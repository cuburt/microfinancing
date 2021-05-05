# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanProduct(models.Model):
    _inherit = 'product.template'

    surcharge_id = fields.Many2one('credit.loan.surcharge')
    penalty_id = fields.Many2one('credit.loan.penalty')
    collateral_id = fields.Many2one('credit.loan.collateral', 'Collateral')
    interest_id = fields.Many2one('credit.loan.interest', 'Interest Rate')
    fund_id = fields.Many2one('credit.loan.fund')

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.multi
    def allow_update(self):
        for journal in self:
            print(journal)
            journal.write({'update_posted':1})

class CheckingAccountTemplate(models.Model):
    _name = 'credit.check.account.template'

    name = fields.Char()

class CheckingAccount(models.Model):
    _name = 'credit.check.account'

    partnerbank_id = fields.Many2one('res.partner.bank', 'Bank Account')
    bank_id = fields.Many2one('res.bank', 'Bank', related='partnerbank_id.bank_id')
    name = fields.Char(string='Bank Name', related='bank_id.name')
    code = fields.Char(string='Checking Account', related='bank_id.bic')
    status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active')
    account_id = fields.Many2one('account.account', 'Asset Account', required=True)
    account = fields.Char(related='account_id.code', string='Account Code')
    account_title = fields.Char(related='account_id.name', string='Account Title')
    template_id = fields.Many2one('credit.check.account.template', 'Check Template')

class ProductSurcharge(models.Model):
    _name = 'credit.loan.surcharge'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','surcharge_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary('Amount', help='Leave blank if using rate.')
    surcharge_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Payable Account",
                                                 domain=[('deprecated', '=', False)],
                                                 help="This account will be used when validating a customer invoice.")

class ProductPenalty(models.Model):
    _name = 'credit.loan.penalty'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','penalty_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')
    penalty_account_income_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Income Account",
                                                 domain=[('deprecated', '=', False)],
                                                 help="This account will be used when validating a customer invoice.")

class LoanCollateral(models.Model):
    _name = 'credit.loan.collateral'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template', 'collateral_id','Applied Products')
    collateral_line_ids = fields.One2many('credit.loan.collateral.line','collateral_id','Collaterals')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now(), readonly=True)
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')

class LoanCollateralLines(models.Model):
    _name = 'credit.loan.collateral.line'

    name = fields.Char()
    code = fields.Char()
    collateral_id = fields.Many2one('credit.loan.collateral','Collateral Type')
    status = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('paid','Paid'),('cancel','Cancelled')], default='draft')
    date_created = fields.Datetime('Date created', default=fields.Datetime.now(), readonly=True)
    application_id = fields.Many2one('crm.lead','Applicant')
    currency_id = fields.Many2one('res.currency', related='collateral_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.', default=lambda self:self.collateral_id.rate)
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.', default=lambda self:self.collateral_id.amount)

class LoanInterest(models.Model):
    _name = 'credit.loan.interest'

    name = fields.Char(readonly=True)
    code = fields.Char()
    index = fields.Integer()
    description = fields.Text()
    date_created = fields.Datetime(default=fields.Datetime.now(), string='Date Created', readonly=True)
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')
    product_ids = fields.One2many('product.template', 'interest_id', 'Applied Products')
    is_active = fields.Boolean(default=True)
    interest_account_income_id = fields.Many2one('account.account', company_dependent=True,
        string="Income Account",
        domain=[('deprecated', '=', False)],
        help="This account will be used when validating a customer invoice.")
    # interest_account_expense_id = fields.Many2one('account.account', company_dependent=True,
    #     string="Payable Account",
    #     domain=[('deprecated', '=', False)],
    #     help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")

    @api.model
    def create(self, values):
        values['code'] = 'INT'
        values['index'] = int(self.search([], order='index desc', limit=1).index) + 1
        values['name'] = '%s-%s' %(values['code'],values['index'])
        return super(LoanInterest, self).create(values)

class LoanFund(models.Model):
    _name = 'credit.loan.fund'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_ids = fields.One2many('product.template','fund_id', 'Applied Products')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_ids.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')


# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class PaymentTerm(models.Model):
#     _inherit = 'account.payment.term'
#
#     #TODO: Add payment terms here
#
#     name = fields.Char()
class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.multi
    def allow_update(self):
        for journal in self:
            print(journal)
            journal.write({'update_posted':1})


class ProductSurcharge(models.Model):
    _name = 'credit.loan.surcharge'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_id = fields.Many2one('product.template', 'Applied Product')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary('Amount', help='Leave blank if using rate.')


class ProductPenalty(models.Model):
    _name = 'credit.loan.penalty'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_id = fields.Many2one('product.template', 'Applied Product')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')

class LoanCollateral(models.Model):
    _name = 'credit.loan.collateral'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_id = fields.Many2one('product.template', 'Applied Product')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')

class LoanInterest(models.Model):
    _name = 'credit.loan.interest'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text()
    date_created = fields.Datetime(default=fields.Datetime.now(), string='Date Created')
    rate = fields.Float()

class LoanFund(models.Model):
    _name = 'credit.loan.fund'

    name = fields.Char()
    code = fields.Char()
    description = fields.Text('Description')
    product_id = fields.Many2one('product.template', 'Applied Product')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    is_active = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    rate = fields.Float('Rate', help='Leave blank if using fixed amount.')
    amount = fields.Monetary(string='Amount', help='Leave blank if using rate.')
# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class CreditPayment(models.Model):
#     _name = 'credit.loan.payment'


# class CreditCollection(models.Model):
#     _name = 'credit.loan.collection'
#
#     name = fields.Char()
#     collection_line = fields.One2many('credit.loan.collection', 'amortization_id', 'Collections')
#     application_id = fields.Many2one('crm.lead', 'Application Seq.')


class CreditCollection(models.Model):
    _name = 'credit.loan.collection'

    name = fields.Char()
    product_id = fields.Many2one('product.template', related='application_id.product_id', string='Applied Product')
    term_id = fields.Many2one('account.payment.term',related='product_id.payment_term')
    # collection_id = fields.Many2one('credit.loan.amortization', 'Amortization')
    application_id = fields.Many2one('crm.lead', 'Application Seq.')
    status = fields.Selection([('draft', 'Draft'),
                               ('pending', 'Pending'),
                               ('paid', 'Paid')])
    date = fields.Date()
    amount = fields.Float('Amount', compute='_compute_amount')
    interest_id = fields.Many2one('credit.loan.interest', related='application_id.interest_id')
    interest = fields.Float(related='interest_id.rate')

    @api.depends('product_id', 'application_id', 'term_id', 'interest')
    def _compute_amount(self):
        for rec in self:
            if rec.product_id.loanclass == 'group':
                #TODO: complete computations
                rec.amount = (rec.application_id.group_id.loan_amount / rec.application_id.member_count)

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    collection_ids = fields.One2many('credit.loan.collection', 'application_id', 'Loan Collection')
    interest_id = fields.Many2one('credit.loan.interest', related='product_id.interest_id')
    interest = fields.Float(related='interest_id.rate')

class Holidays(models.Model):
    _name = 'credit.loan.collection.holiday'

    name = fields.Char(string='Holiday', required=True)
    description = fields.Text(string='Description')
    type = fields.Selection([('regular', 'Regular Holiday'),
                             ('special_nw', 'Special Non-working Holiday'),
                             ('special_w', 'Special Working Holiday')], string='Holiday Type', required=True)
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], string='Month', required=True)
    day = fields.Selection([(str(i), str(i).zfill(2)) for i in range(1, 32)], string='Day', required=True)

# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Amortization(models.Model):
    _name = 'credit.loan.amortization'

    name = fields.Char()
    date = fields.Date()
    amount = fields.Float()
    collection_line = fields.One2many('credit.loan.collection', 'amortization_id', 'Collections')

class CreditCollection(models.Model):
    _name = 'credit.loan.collection'

    status = fields.Selection([('draft','Draft'),
                               ('pending','Pending'),
                               ('done','Done')])
    term_id = fields.Many2one('account.payment.term','Term')
    amortization_id = fields.Many2one('credit.loan.amortization', 'Amortization')



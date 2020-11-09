# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    #TODO: Add payment terms here

    name = fields.Char()

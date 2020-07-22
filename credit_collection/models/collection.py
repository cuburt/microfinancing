# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CreditCollection(models.Model):
    _name = 'credit.loan.collection'

    status = fields.Selection([('draft','Draft'),
                               ('pending','Pending'),
                               ('done','Done')])
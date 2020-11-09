# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanDisbursement(models.Model):
    _inherit = 'crm.lead'


status = fields.Selection(string="Status", selection_add=[('disburse', 'Disbursement')], required=True,
                         track_visibility='onchange')
release_date = fields.Datetime('Release Date', default=fields.Datetime.now(),
                                     required_if_status='disburse')
credit_ticket = fields.Char('Credit Ticket',required_if_status='disburse')
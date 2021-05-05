# -*- coding: utf-8 -*-

from odoo import models, fields, api

class twilio(models.Model):
    _name = 'twilio.twilio'

    account_sid = fields.Char()
    auth_token = fields.Char()
    messaging_service_sid = fields.Char()
    template_id = fields.Many2one('twilio.template','SMS Template')

class TwilioTemplate(models.Model):
    _name = 'twilio.template'

    name = fields.Char()
    message = fields.Text()
    send_pool = fields.Many2many('res.partner')
    is_otp = fields.Boolean(default=True)

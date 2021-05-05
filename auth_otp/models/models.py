# -*- coding: utf-8 -*-

from odoo import models, fields, api

class auth_otp(models.Model):
    _name = 'res.users'

    mobile = fields.Char()

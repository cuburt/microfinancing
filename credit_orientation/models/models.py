# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CreditOrientation(models.Model):
    _inherit = 'event.event'


class AttendeeOrientation(models.Model):
    _inherit = 'event.registration'



# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    event_registration_id = fields.Many2one('event.registration','Membership Education')

# class EventType(models.Model):
#     _inherit = 'event.type'
#
#     type = fields.Selection(selection_add=[('leader','Information Meeting'),
#                                            ('member','Members Education')])
#

class LoanEvent(models.Model):
    _inherit = 'event.event'



class EventRegistration(models.Model):
    _inherit = 'event.registration'

    group_ids = fields.One2many('credit.loan.group','event_registration_id','Groups')


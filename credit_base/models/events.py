# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api
# from odoo import tools, _
# from odoo.modules.module import get_module_resource
# from odoo.exceptions import ValidationError
# from dateutil.relativedelta import relativedelta
# from datetime import date, datetime
#
#
# class EventType(models.Model):
#     _inherit = 'event.type'
#
#     service = fields.Selection([('group','Group/Selda Loan')])
#     type = fields.Selection(selection_add=[('leader','Information Meeting'),
#                                            ('members','Members Education')],
#                             required_if_service='group')
#
#
# class LoanEvent(models.Model):
#     _inherit = 'event.event'
#
#
# class EventRegistration(models.Model):
#     _inherit = 'event.registration'
#
#     #where client leader registers
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)
#
# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     @api.model
#     def partner_account(self):
#         return {'domain':{
#             'property_account_receivable_id':[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('company_id.id','=',self.company_id.id)],
#             'property_account_payable_id':[('internal_type', '=', 'payable'), ('deprecated', '=', False), ('company_id.id','=',self.company_id.id)]}}

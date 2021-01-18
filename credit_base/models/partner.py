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
#     def create(self, values):
#         partner = super(ResPartner, self).create(values)
#         self.env['res.users'].create({
#             'name':values['name'],
#             'login':values['email'],
#             'sel_groups_1_9_10':9,
#             'company_id':self.env['res.branch'].search(['id','=',values['branch_id']],limit=1).company_id.id
#         })
#         return partner
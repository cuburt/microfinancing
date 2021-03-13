# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError

# class WizardClientInvestigation(models.TransientModel):
#     _name = 'wizard.client.investigation'
#
#     stage = fields.Selection([('begin','Begin'),
#                               ('character','Character'),
#                               ('capacity','Capacity'),
#                               ('capital','Capital'),
#                               ('condition','Condition'),
#                               ('collateral','Collateral'),
#                               ('end','End')])
#     application_id = fields.Many2one('crm.lead', 'Loan Application', default=lambda self:self.env.context.get('default_application_id'))
#     partner_id = fields.Many2one('res.partner', related='application_id.partner_id', string='Applicant')
#     ci_id = fields.Many2one('credit.client.investigation', 'CI/BI Form', default=lambda self:self.env.context.get('default_investigation_id'))
#     character = fields.One2many(related='ci_id.character')
#     capacity = fields.One2many(related='ci_id.capacity')
#     capital = fields.One2many(related='ci_id.capital')
#     condition = fields.One2many(related='ci_id.condition')
#     collateral = fields.One2many(related='ci_id.collateral')
#     character_remarks = fields.Text('Remarks')
#     capacity_remarks = fields.Text('Remarks')
#     capital_remarks = fields.Text('Remarks')
#     condition_remarks = fields.Text('Remarks')
#     collateral_remarks = fields.Text('Remarks')

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

#FOR GROUPS
class LoanGroup(models.Model):
    _inherit = 'credit.loan.group'

    financing_ids = fields.One2many('credit.loan.financing', 'group_id', 'Loan Account', required_if_state='approve')

class Lead(models.Model):
    _inherit = 'crm.lead'

    stage_id = fields.Many2one('crm.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               index=True, copy=False,
                               domain="['|',('team_id', '=', False), ('team_id', '=', team_id), ('is_active','=', True)]",
                               group_expand='_read_group_stage_ids', default=lambda self: self._default_stage_id())
    group_id = fields.Many2one('credit.loan.group', 'Group', index=True)

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    loan_applications = fields.One2many(comodel_name="credit.loan.application", inverse_name="financing_id", string="Source", required=False)

class LoanApplication(models.Model):
    _name = 'credit.loan.application'

    # APPLICATION FORM
    financing_id = fields.Many2one('credit.loan.financing', 'Source', required=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch','Branch')
    application_date = fields.Date('Application Date', default=fields.Datetime.now(), required_if_state='confirm')



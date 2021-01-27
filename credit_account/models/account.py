# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    journal_entry_ids = fields.One2many('account.move', 'application_id', 'Journal Entry')

    @api.multi
    def action_disburse(self):
        #TODO: update account move
        return True

class AccountMove(models.Model):
    _inherit = 'account.move'

    application_id = fields.Many2one('crm.lead', 'Application')



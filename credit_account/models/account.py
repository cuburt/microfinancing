# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    account_id = fields.Many2one('account.move', 'Journal Entry')

class LoanSavings(models.Model):
    _inherit = 'credit.loan.savings'

    account_id = fields.Many2one('account.move', 'Journal Entry')

class AccountMove(models.Model):
    _inherit = 'account.move'

    financing_id = fields.One2many('credit.loan.financing', 'account_id', 'Loan Account')
    savings_id = fields.One2many('credit.loan.savings', 'account_id', 'Savings Account')
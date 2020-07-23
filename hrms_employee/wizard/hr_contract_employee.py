from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError


class HrContractEmployee(models.TransientModel):
    _name = 'hr.contract.employee'

    @api.multi
    def action_open(self):
        contract_ids = self.env['hr.contract'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state == 'draft':
                if self.env.user.has_group('hrms_employee.group_hr_contract_payroll'):
                    contract.action_open()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))

    @api.multi
    def action_expired(self):
        contract_ids = self.env['hr.contract'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state == 'open':
                if self.env.user.has_group('hrms_employee.group_hr_contract_payroll'):
                    contract.action_expired()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))

    @api.multi
    def action_pending(self):
        contract_ids = self.env['hr.contract'].browse(self._context.get('active_ids'))
        for contract in contract_ids:
            if contract.state == 'open':
                if self.env.user.has_group('hrms_employee.group_hr_contract_payroll'):
                    contract.action_pending()
                else:
                    raise UserError(_('Only allowed user(s) can refuse the requests.'))
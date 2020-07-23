from odoo import api, fields, models

class HrHolidayPolicy(models.Model):
    _name = 'hr.holiday.policy'

    name = fields.Char('Name')
    date = fields.Date('Effective Date')
    line_ids = fields.One2many('hr.holiday.line.policy', 'policy_id', 'Policy Lines')


class HrHolidayLinePolicy(models.Model):
    _name = 'hr.holiday.line.policy'

    name = fields.Char('Name')
    code = fields.Char('Code', required=True, help="Use this code in the salary rules.")
    holiday_id = fields.Many2one('hr.holidays.public.type', 'Holiday')
    policy_id = fields.Many2one('hr.holiday.policy', 'Policy')
    type = fields.Selection([('paid', 'Paid'),
                             ('unpaid', 'Unpaid'),
                             ('dock', 'Dock')],
                            'Type',
                            required=True,
                            help="Determines how the absence will be treated in payroll. "
                                 "The 'Dock Salary' type will deduct money (useful for "
                                 "salaried employees).", )
    rate = fields.Float('Rate', required=True, help='Multiplier of employee wage.')

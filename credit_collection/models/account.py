from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    application_id = fields.Many2one('crm.lead', 'Vouchers')
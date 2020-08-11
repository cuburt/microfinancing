#-*- coding: utf-8 -*-

from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    # property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
    #                                               string="Account Payable", oldname="property_account_payable",
    #                                               domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
    #                                               help="This account will be used instead of the default one as the payable account for the current partner",
    #                                               required=True, related='parent_id.property_account_payable_id')
    # property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
    #                                                  string="Account Receivable", oldname="property_account_receivable",
    #                                                  domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
    #                                                  help="This account will be used instead of the default one as the receivable account for the current partner",
    #                                                  required=True, related='parent_id.property_account_receivable_id')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        company = self.env['res.company']
        if self.company_id:
            company = self.company_id
        else:
            company = self.env.user.company_id
        return {'domain': {'property_account_position_id': [('company_id', 'in', [company.id, False])]},
                'value': {
                    'property_account_payable_id': self.env['account.account'].search([('company_id.id','=',company.id),('internal_type','=','payable')],limit=1),
                    'property_account_receivable_id': self.env['account.account'].search([('company_id.id','=',company.id),('internal_type','=','receivable')],limit=1)
                }}

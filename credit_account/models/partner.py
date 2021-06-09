#-*- coding: utf-8 -*-

from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

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

    # @api.model
    # def config_company_accounting(self,partner):
    #     partner = self.sudo().search([('id','=',partner)])
    #     print(partner)
    #     print(self.env['account.account'].sudo().search([('company_id.id','=',partner.company_id.id),('internal_type','=','receivable'),('deprecated','=',False),('code','=','11710')],limit=1).id)
    #     partner.sudo().write({
    #         'property_account_receivable_id':self.env['account.account'].sudo().search([('company_id.id','=',partner.company_id.id),('internal_type','=','receivable'),('deprecated','=',False),('code','=','11710')],limit=1).id,
    #         'property_account_payable_id':self.env['account.account'].sudo().search([('company_id.id','=',partner.company_id.id),('internal_type','=','payable'),('deprecated','=',False),('code','=','00000')],limit=1).id
    #     })
    #     return True
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError

# #FOR GROUPS
# class LoanGroup(models.Model):
#     _inherit = 'credit.loan.group'
#
#     financing_ids = fields.One2many('credit.loan.financing', 'group_id', 'Loan Account', required_if_state='approve')


# [loan.financing]-|----<HAS>----O<[crm.lead]>O----<HAS>----O-[loan.group]

class LoanFinancing(models.Model):
    _inherit = 'credit.loan.financing'

    loan_applications = fields.One2many(comodel_name="crm.lead", inverse_name="financing_id", string="Loan Application", required=False)

class LoanClient(models.Model):
    _inherit = 'res.partner'

    financing_ids = fields.One2many('credit.loan.financing', 'member_id', 'Loan Account', required_if_state='approve')

#TODO: CONNECT TO INVOICE WHEN STATUS IS CONFIRM
#combined loan.application and crm.lead because they have one to one relationship
class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    name = fields.Char(readonly=True, required=False)
    index = fields.Integer()
    code = fields.Char(readonly=True)
    application_date = fields.Datetime('Application Date', default=fields.Datetime.now(), required_if_state='confirm', readonly=True)
    financing_id = fields.Many2one('credit.loan.financing', 'Loan Account', required=True)
    cosigner_id = fields.Many2one(comodel_name='res.partner', string='Cosigner')
    status = fields.Selection(string="Status", selection=[('draft', 'Draft')], required=True,
                             default='draft', track_visibility='onchange')
    state = fields.Boolean(default=False)
    #RELATED FIELDS
    partner_id = fields.Many2one('res.partner', related='financing_id.member_id')
    area_id = fields.Many2one('res.area', 'Area', index=True, readonly=True, required=True, store=True)
    branch_id = fields.Many2one('res.branch','Branch', index=True, readonly=True, required=True, store=True)
    do = fields.Many2one('res.partner','Assigned DO', readonly=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, store=True)

    @api.onchange('financing_id')
    def set_account(self):
        try:
            if self.financing_id:
                self.partner_id = self.financing_id.member_id.id
                self.company_id = self.env['res.users'].sudo().search([('partner_id.id','=',self.partner_id.id)], limit=1).company_id.id
                self.branch_id = self.financing_id.branch_id.id
                self.area_id = self.financing_id.area_id.id
                self.do = self.area_id.officer_id.search([('type','=','do'),('area_id.id','=',self.area_id.id)], limit=1).id

        except Exception as e:
            raise UserError(_("ERROR: 'set_account' "+str(e)))
    # @api.multi
    # def default_branch(self):
    #     try:
    #         return self.financing_id.branch_id.id
    #     except Exception as e:
    #         raise UserError(_(str(e)))
    @api.one
    def draft_form(self):
        try:
            self.state = False
            self.status = 'draft'
        except Exception as e:
            raise UserError(_("ERROR: 'draft_form' "+str(e)))
    # @api.model
    # def create(self, values):
    #     application = super(LoanApplication, self).create(values)
    #     print(application.product_id)
    #     self.env['crm.lead'].create({
    #         'name': application.financing_id.member_id.name,
    #         'application_id': application.id,
    #         'partner_id': application.partner_id.id,
    #     })
    #
    #     return application

    @api.model
    def create(self, values):
        financing = self.env['credit.loan.financing'].sudo().search([('id','=', values['financing_id'])])
        values['branch_id'] = financing.branch_id.id
        values['area_id'] = financing.area_id.id
        values['do'] = self.env['res.area'].sudo().search([('id','=',values['area_id'])]).officer_id.search([('type', '=', 'do'), ('area_id.id', '=', values['area_id'])],limit=1).id
        print(values)
        return super(LoanApplication, self).create(values)
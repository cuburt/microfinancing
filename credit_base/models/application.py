# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _

from odoo.exceptions import ValidationError, UserError
import random
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
    financing_id = fields.Many2one('credit.loan.financing', 'Loan Account', required=True, domain="[('status','not in',['archive','blacklist'])]")
    savings_id = fields.Many2one('credit.loan.savings', 'Savings Account', required=True)
    cosigner_id = fields.Many2one(comodel_name='res.partner', string='Cosigner')
    status = fields.Selection(string="Status", selection=[('draft', 'Draft'),('confirm', 'Confirmed')], required=True,
                             default='draft', track_visibility='onchange')
    state = fields.Boolean(default=False)
    #RELATED FIELDS
    partner_id = fields.Many2one('res.partner', related='financing_id.member_id')
    area_id = fields.Many2one('res.area', 'Area', index=True, required=True, store=True)
    branch_id = fields.Many2one('res.branch','Branch', index=True, required=True, store=True)
    officer_id = fields.Many2one('res.partner','Assigned Officer', required=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, store=True)
    attachment_ids = fields.Many2many('ir.attachment', 'crm_lead_ir_attachment_relation', string='Attachments')

    @api.onchange('financing_id')
    def set_account(self):
        try:
            if self.financing_id:
                self.partner_id = self.financing_id.member_id.id
                self.branch_id = self.financing_id.branch_id.id
                # self.company_id = self.env['res.users'].sudo().search([('partner_id.id','=',self.partner_id.id)], limit=1).company_id.id
                self.company_id = self.branch_id.company_id.id
                self.area_id = self.financing_id.area_id.id
                if self.product_id.loanclass == 'individual':
                    domain = [('type', '=', 'ao'), ('branch_id.id', '=', self.branch_id.id)]
                else: domain = [('type', '=', 'do'), ('area_id.id', '=', self.area_id.id)]
                self.officer_id = self.area_id.officer_ids.search(domain, limit=1).id
        except Exception as e:
            raise UserError(_("ERROR: 'set_account' "+str(e)))
        return {'domain':{'savings_id':[('status','not in',['archive','blacklist']), ('financing_id.id','=',self.financing_id.id)]}}

    @api.onchange('officer_id')
    def officer_id_onchange(self):
        return {'domain':{'officer_id':[('type', '=', 'ao'), ('branch_id.id', '=', self.branch_id.id)]}}

    @api.onchange('branch_id')
    def area_domain(self):
        self.area_id = self.branch_id.area_ids.sudo().search([],limit=1).id or False
        return {'domain': {'area_id': [('id', 'in', [rec.id for rec in self.branch_id.area_ids])]}}

    @api.onchange('area_id')
    def do_domain(self):
        self.officer_id = self.area_id.officer_ids.sudo().search(['&',('type','=','do'),('area_ids.id','=',self.area_id.id)],limit=1).id or False
        return {'domain': {'officer_id': [('id', 'in', [rec.id for rec in self.area_id.officer_ids])]}}

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

        blacklist_item = self.env['credit.loan.blacklist'].sudo().search([('financing_id.id','=',values.get('financing_id'))], limit=1)
        print(blacklist_item)
        if blacklist_item:
            print("Cannot create blacklisted applicant.")

        return super(LoanApplication, self).create(values)


class Blacklist(models.Model):
    _name = 'credit.loan.blacklist'

    name = fields.Char()
    application_id = fields.Many2one('crm.lead')
    financing_id = fields.Many2one('credit.loan.financing', related='application_id.financing_id')
    remarks = fields.Text()

class Reapplication (models.Model):
    _name = 'credit.loan.reapplication'

    name = fields.Char()
    application_id = fields.Many2one('crm.lead')
    financing_id = fields.Many2one('credit.loan.financing', related='application_id.financing_id')
    remarks = fields.Text()

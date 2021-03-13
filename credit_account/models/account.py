# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from time import struct_time
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def open_invoice(self):
        date_now = fields.Datetime.now()
        if self.date_invoice == date_now.date():
            self.sudo().write({
                'status':'open'
            })
        return True

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    journal_entry_ids = fields.One2many('account.move', 'application_id', 'Journal Entry')

    @api.multi
    def release_loan(self):
        if self.stage_id.id != self.env['crm.stage'].sudo().search([('name', '=', 'Approved')]).id:
            raise UserError(_("The application must be approved first!"))
        self.generate_collection_line()
        try:
            #branchless group: current application is skipped when group loan
            print('GROUP:', [application.partner_id.display_name for application in self.group_id.application_ids])
            for application in self.group_id.application_ids:
                if application.id != self.id:
                    application.generate_collection_line()
        except:pass
        return True

    @api.multi
    def create_journal(self):
        # branchless loan_amount
        # if individual, the multiplier = 1 else 0: first addend
        # elif group, the multiplier = 1 else 0: second addend
        loan_amount = (self.loan_amount*(self.product_id.loanclass == 'individual'))+(self.group_id.loan_amount*(self.product_id.loanclass == 'group'))
        print('CREATING CHECK VOUCHER...')
        try:
            journal = self.env['account.journal'].sudo().search([('code', '=', 'CP'),('company_id.id','=',self.branch_id.company_id.id)])
            loan_account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_receivable_categ_id or self.env['account.account'].sudo().search([('internal_type','=','receivable'),('deprecated','=',False),('company_id.id','=',self.branch_id.company_id.id),('code','=','11710')], limit=1)
            cash_account = self.env['credit.check.account'].sudo().search([], limit=1).account_id
            print({'debit':loan_amount, 'account_id':loan_account.id, 'name':loan_account.name,})
            print({'credit': loan_amount, 'account_id': cash_account.id, 'name': cash_account.name,})
            check_voucher = self.env['account.move'].sudo().create({
                'application_id': self.id,
                'journal_id': journal.id,
                'ref': 'CV-%s-%s' % ('21', str(len(journal) + 1)),
                'date':fields.Datetime.now(),
                'line_ids':[(0,0, {'debit':loan_amount, 'account_id':loan_account.id, 'name':loan_account.name,}),
                            (0,0, {'credit': loan_amount, 'account_id': cash_account.id, 'name': cash_account.name,})]

            })
            print('CHECK VOUCHER CREATED:', check_voucher)
        except Exception as e:
            raise ValidationError(_("ERROR: 'journal'"+ str(e)))

        try:
            self.write({
                'stage_id': self.env['crm.stage'].search([('name', '=', 'Collection')]).id,
                'status': 'collection'
            })
            print('DISBURSED APPLICATION:', self.partner_id.display_name)
        except Exception as e:
            raise UserError(_("ERROR: 'release_loan' state update", str(e)))
        return True



    @api.multi
    def generate_collection_line(self):
        print('CREATING JOURNAL ENTRIES FOR:', self.partner_id.display_name)
        date_released = fields.Datetime.now()
        self.date_released = date_released
        order = self.env['sale.order'].sudo().search([('opportunity_id.id', '=', self.id)])
        print('DATE RELEASED:', date_released)
        for i, line in enumerate(self.collection_line_ids):
            print('UPDATING COLLECTION LINE...', line.id)
            print('MONTH INDEX:', i)
            try:
                date_invoice = date_released + relativedelta(months=i)
                date_due = date_released + relativedelta(months=i + 1)
                context = {
                    "date_invoice": date_invoice.date(),
                    "date_due": date_due.date(),
                    "amount": line.amortization,
                }

                print('CREATING INVOICE...')
                invoice = line.order_id._create_invoice(context)

                print('UPDATING COLLECTION LINES...')
                line.write({
                    'invoice_id': invoice.id,
                    'date': date_released + relativedelta(months=i+1),
                    'status': 'active',
                })

                # print('UPDATING INVOICE...')
                # invoice.action_invoice_open()
            except Exception as e:
                print(str(e))
                raise UserError(_('ERROR: Please contact your administrator immediately. '+str(e)))
        order.sudo().write({
            'invoice_status':'invoiced'
        })
        return self.create_journal()

class AccountMove(models.Model):
    _inherit = 'account.move'

    application_id = fields.Many2one('crm.lead', 'Application')

# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     @api.onchange('partner_id', 'company_id')
#     def _onchange_partner_id(self):
#         account_id = False
#         payment_term_id = False
#         fiscal_position = False
#         bank_id = False
#         warning = {}
#         domain = {}
#         company_id = self.company_id.id
#         p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
#         type = self.type or self.env.context.get('type', 'out_invoice')
#         if p:
#             rec_account = p.property_account_receivable_id
#             pay_account = p.property_account_payable_id
#             if not rec_account and not pay_account:
#                 action = self.env.ref('account.action_account_config')
#                 msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
#                 raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
#
#             if type in ('in_invoice', 'in_refund'):
#                 account_id = pay_account.id
#                 payment_term_id = p.property_supplier_payment_term_id.id
#             else:
#                 account_id = rec_account.id
#                 payment_term_id = p.property_payment_term_id.id
#
#             delivery_partner_id = self.get_delivery_partner_id()
#             fiscal_position = p.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)
#
#             # If partner has no warning, check its company
#             if p.invoice_warn == 'no-message' and p.parent_id:
#                 p = p.parent_id
#             if p.invoice_warn and p.invoice_warn != 'no-message':
#                 # Block if partner only has warning but parent company is blocked
#                 if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
#                     p = p.parent_id
#                 warning = {
#                     'title': _("Warning for %s") % p.name,
#                     'message': p.invoice_warn_msg
#                     }
#                 if p.invoice_warn == 'block':
#                     self.partner_id = False
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
# class CreditPayment(models.Model):
#     _name = 'credit.loan.payment'


# class CreditCollection(models.Model):
#     _name = 'credit.loan.collection'
#
#     name = fields.Char()
#     collection_line = fields.One2many('credit.loan.collection', 'amortization_id', 'Collections')
#     application_id = fields.Many2one('crm.lead', 'Application Seq.')


class CreditCollectionLine(models.Model):
    _name = 'credit.loan.collection.line'

    name = fields.Char()
    collection_id = fields.Many2one('credit.loan.collection', 'Collection')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    currency_id = fields.Many2one('res.currency', related='collection_id.currency_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('pending', 'Pending'),
                               ('paid', 'Paid')])
    date = fields.Date()
    principal = fields.Monetary('Principal')
    amortization = fields.Monetary('Amortization')
    interest = fields.Monetary('Interest')
    surcharge = fields.Monetary('Surcharge')
    penalty = fields.Monetary('Penalty')

class CreditCollection(models.Model):
    _name = 'credit.loan.collection'

    name = fields.Char()
    application_id = fields.Many2one('crm.lead', 'Application Seq.')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    collection_line_ids = fields.One2many('credit.loan.collection.line','collection_id','Collection Line')
    product_id = fields.Many2one('product.template', related='application_id.product_id', string='Applied Product')
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')
    term_id = fields.Many2one('account.payment.term', related='product_id.payment_term')
    interest_id = fields.Many2one('credit.loan.interest', related='product_id.interest_id')
    interest = fields.Monetary(compute='_compute_amortization')
    surcharge_id = fields.Many2one('credit.loan.surcharge', related='product_id.surcharge_id')
    surcharge = fields.Monetary(compute='_compute_amortization')
    penalty_id = fields.Many2one('credit.loan.penalty', related='product_id.penalty_id')
    penalty = fields.Monetary(compute='_compute_amortization')
    collateral_id = fields.Many2one('credit.loan.collateral', related='product_id.collateral_id')
    fund_id = fields.Many2one('credit.loan.fund', related='product_id.fund_id')
    principal = fields.Monetary(compute='_compute_amortization')
    amortization = fields.Monetary(compute='_compute_amortization')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('complete', 'Complete')])

    @api.depends('interest_id','surcharge_id','penalty_id', 'application_id', 'product_id')
    def _compute_amortization(self):
        for rec in self:
            term = rec.product_id.payment_term.duration
            if rec.product_id.loanclass == 'individual':
                loan_amount = rec.application_id.loan_amount
                principal = loan_amount/term
            elif rec.product_id.loanclass == 'group':
                loan_amount = rec.application_id.group_id.loan_amount
                principal = (loan_amount/term)/rec.application_id.member_count
            rec.interest = (principal * rec.interest_id.rate) + rec.interest_id.amount
            rec.surcharge = (principal * rec.surcharge_id.rate) + rec.surcharge_id.amount
            rec.penalty = (principal * rec.penalty_id.rate) + rec.penalty_id.amount
            rec.principal = principal
            rec.amortization = (principal+rec.interest) - rec.surcharge

    @api.model
    def create(self, values):
        application = self.env['crm.lead'].sudo().search([('id','=',values['application_id'])])
        collection = super(CreditCollection, self).create(values)
        for line in range(1,application.product_id.payment_term.duration):
            print('CREATING COLLECTION LINES...', line)
            self.env['credit.loan.collection.line'].sudo().create({
                'collection_id':collection.id,
                'status':'draft',
                'principal':collection.principal,
                'amortization':collection.amortization,
                'interest':collection.interest,
                'surcharge':collection.surcharge,
                'penalty':collection.penalty
            })
        print('COLLECTION DONE!')
        return collection

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string='Status', selection_add=[('disburse', 'Disbursement')], required=True, track_visibility='onchange')
    collection_ids = fields.One2many('credit.loan.collection', 'application_id', 'Loan Collection')
    collection_line_ids = fields.One2many('credit.loan.collection.line', related='collection_ids.collection_line_ids')
    date_approved = fields.Datetime('Date Approved')

    @api.multi
    def approve_application(self):
        date_approved = fields.Datetime.now()
        print('DATE APPROVED:', date_approved)
        # TODO: set collection to confirm
        if self.stage_id.id != self.env['crm.stage'].sudo().search([('name','=','Proposition')]).id:
            raise UserError(_("The application must be endorsed first!"))
        if self.product_id.loanclass == 'individual':
            for line in self.collection_line_ids:
                # print('MONTH INDEX:', i)
                line.write({
                    # 'date': date_approved + relativedelta(months=+i),
                    'status': 'pending',
                })
                print('UPDATING COLLECTION LINE...', line.id)
            print('CREATING CHECK VOUCHER...')
            # journal_entry = self.env['account.move'].sudo().create({
            #     'application_id':self.id,
            # })
            journal = self.env['account.journal'].sudo().search([('code','=','CV')])
            check_voucher = self.env['account.move'].sudo().create({
                'application_id':self.id,
                'journal_id':journal.id,
                'ref':'CV-%s-%s'%('21',str(len(journal)+1)),

            })

            try:
                cash_account = self.env['credit.check.account'].sudo().search([],limit=1).account_id
                self.env['account.move.line'].sudo().create({
                    'move_id': check_voucher.id,
                    'credit': self.loan_amount,
                    'account_id': cash_account.id,
                    'name': cash_account.name,
                })
                print('CREDIT LINE CREATED!')
            except Exception as e:
                raise ValidationError(_("ERROR: 'approve_application'", str(e)))
            try:
                loan_account = self.product_id.property_account_expense_id
                if not loan_account:
                    loan_account = self.product_id.categ_id.property_account_receivable_categ_id.id

                self.env['account.move.line'].sudo().create({
                    'move_id': check_voucher.id,
                    'credit': self.loan_amount,
                    'account_id': loan_account.id,
                    'name': loan_account.name,
                })
                print('DEBIT LINE CREATED!')
            except Exception as e:
                raise ValidationError(_("ERROR: 'approve_application'", str(e)))

            self.write({
                'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                'status': 'disburse'
            })
            print('APPROVED APPLICATION:', self.partner_id.display_name)

        elif self.product_id.loanclass == 'group':

            for application in self.group_id.application_ids:
                index = 1
                for line in application.collection_line_ids:
                    print('MONTH INDEX:', index)
                    line.write({
                        # 'date': date_approved + relativedelta(months=+index),
                        'status': 'pending',
                    })
                    print('UPDATING COLLECTION LINE...', line.id)
                    index+=1

                print('CREATING CHECK VOUCHER...')
                # journal_entry = self.env['account.move'].sudo().create({
                #     'application_id':self.id,
                # })
                journal = self.env['account.journal'].sudo().search([('code', '=', 'CP')])
                print(journal.code)
                check_voucher = self.env['account.move'].sudo().create({
                    'application_id': application.id,
                    'journal_id': journal.id,
                    'ref': 'CV-%s-%s' % ('21', str(len(journal) + 1)),

                })

                try:
                    cash_account = self.env['credit.check.account'].sudo().search([], limit=1).account_id
                    self.env['account.move.line'].sudo().create({
                        'move_id': check_voucher.id,
                        'credit': application.loan_amount,
                        'account_id': cash_account.id,
                        'name': cash_account.name,
                    })
                    print('CREDIT LINE CREATED!')
                except Exception as e:
                    raise ValidationError(_("ERROR: 'approve_application'", str(e)))
                try:
                    loan_account = application.product_id.property_account_expense_id
                    if not loan_account:
                        loan_account = application.product_id.categ_id.property_account_receivable_categ_id.id

                    self.env['account.move.line'].sudo().create({
                        'move_id': check_voucher.id,
                        'credit': application.loan_amount,
                        'account_id': loan_account.id,
                        'name': loan_account.name,
                    })
                    print('DEBIT LINE CREATED!')
                except Exception as e:
                    raise ValidationError(_("ERROR: 'approve_application'", str(e)))
                application.write({
                    'stage_id': self.env['crm.stage'].search([('name', '=', 'Approved')]).id,
                    'status': 'disburse'
                })
                print('APPROVED APPLICATION:', application.partner_id.display_name)
        self.date_approved = date_approved
        return True

class Holidays(models.Model):
    _name = 'credit.loan.collection.holiday'

    name = fields.Char(string='Holiday', required=True)
    description = fields.Text(string='Description')
    type = fields.Selection([('regular', 'Regular Holiday'),
                             ('special_nw', 'Special Non-working Holiday'),
                             ('special_w', 'Special Working Holiday')], string='Holiday Type', required=True)
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], string='Month', required=True)
    day = fields.Selection([(str(i), str(i).zfill(2)) for i in range(1, 32)], string='Day', required=True)

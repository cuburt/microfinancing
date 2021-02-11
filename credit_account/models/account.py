# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import UserError, ValidationError

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
            journal = self.env['account.journal'].sudo().search([('code', '=', 'CP')])
            loan_account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_receivable_categ_id
            cash_account = self.env['credit.check.account'].sudo().search([], limit=1).account_id
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
            raise ValidationError(_("ERROR: 'journal'", str(e)))

        # print('CREATING CHECK VOUCHER LINES...')
        # try:
        #     print('CREATING DEBIT LINE...')
        #     loan_account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_receivable_categ_id
        #     print('LOAN ACCOUNT:', loan_account)
        #     debit_line = self.env['account.move.line'].sudo().create({
        #         'move_id': check_voucher.id,
        #         'debit': loan_amount,
        #         'account_id': loan_account.id,
        #         'name': loan_account.name,
        #     })
        #     print('DEBIT LINE CREATED!', debit_line.name)
        #     print('CREATING CREDIT LINE...')
        #     cash_account = self.env['credit.check.account'].sudo().search([], limit=1).account_id
        #     print('CASH ACCOUNT:', cash_account)
        #     credit_line = self.env['account.move.line'].sudo().create({
        #         'move_id': check_voucher.id,
        #         'credit': loan_amount,
        #         'account_id': cash_account.id,
        #         'name': cash_account.name,
        #     })
        #     print('CREDIT LINE CREATED!', credit_line.name)
        # except Exception as e:
        #     raise ValidationError(_("ERROR: 'release_loan' check voucher line", str(e)))
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
        print('DATE RELEASED:', date_released)
        for i, line in enumerate(self.collection_line_ids):
            print('UPDATING COLLECTION LINE...', line.id)
            print('MONTH INDEX:', i)
            line.write({
                'date': date_released + relativedelta(months=i),
                'status': 'active',
            })
        return self.create_journal()

class AccountMove(models.Model):
    _inherit = 'account.move'

    application_id = fields.Many2one('crm.lead', 'Application')



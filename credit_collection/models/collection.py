# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import time

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    #TODO: THIS IS WHERE YOU LEFT OFF
    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()
        res = self.update_collection(res)#UPDATE COLLECTION UPON PAYMENT REGISTRATION
        # self.mapped('payment_transaction_id').filtered(lambda x: x.state == 'done' and not x.is_processed)._post_process_after_done()
        return res

    def update_collection(self, invoice):
        print("UPDATE COLLECTION", invoice)
        #TODO: DO SHIT HERE
        return invoice


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    date_validate = fields.Date()
    collection_id = fields.Many2one('credit.loan.collection', 'Collection')

    @api.multi
    def open_invoice(self):
        date_now = fields.Datetime.now()
        invoices = self.sudo().search([('date_validate','=',date_now), ('state','=','draft')])
        for invoice in invoices:
            print(invoice)
            invoice.action_invoice_open()
        print(invoices)
        print("checking invoice validity...")
        return True

    # @api.onchange('partner_id', 'company_id')
    # def _onchange_partner_id(self):
    #     account_id = False
    #     payment_term_id = False
    #     fiscal_position = False
    #     bank_id = False
    #     warning = {}
    #     domain = {}
    #     company_id = self.company_id.id
    #     print(company_id)
    #     p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
    #     type = self.type or self.env.context.get('type', 'out_invoice')
    #     if p:
    #         print(p)
    #         rec_account = p.company_id.parent_id.par.property_account_receivable_id
    #         pay_account = p.property_account_payable_id
    #         print(rec_account, pay_account)
    #         if not rec_account and not pay_account:
    #             action = self.env.ref('account.action_account_config')
    #             msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
    #             raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
    #
    #         if type in ('in_invoice', 'in_refund'):
    #             account_id = pay_account.id
    #             payment_term_id = p.property_supplier_payment_term_id.id
    #         else:
    #             account_id = rec_account.id
    #             payment_term_id = p.property_payment_term_id.id
    #
    #         delivery_partner_id = self.get_delivery_partner_id()
    #         fiscal_position = p.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)
    #
    #         # If partner has no warning, check its company
    #         if p.invoice_warn == 'no-message' and p.parent_id:
    #             p = p.parent_id
    #         if p.invoice_warn and p.invoice_warn != 'no-message':
    #             # Block if partner only has warning but parent company is blocked
    #             if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
    #                 p = p.parent_id
    #             warning = {
    #                 'title': _("Warning for %s") % p.name,
    #                 'message': p.invoice_warn_msg
    #                 }
    #             if p.invoice_warn == 'block':
    #                 self.partner_id = False
    #
    #     self.account_id = account_id
    #     if payment_term_id:
    #         self.payment_term_id = payment_term_id
    #     self.date_due = False
    #     self.fiscal_position_id = fiscal_position
    #
    #     if type in ('in_invoice', 'out_refund'):
    #         bank_ids = p.commercial_partner_id.bank_ids
    #         bank_id = bank_ids[0].id if bank_ids else False
    #         self.partner_bank_id = bank_id
    #         domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}
    #     elif type == 'out_invoice':
    #         domain = {'partner_bank_id': [('partner_id.ref_company_ids', 'in', [self.company_id.id])]}
    #
    #     res = {}
    #     if warning:
    #         res['warning'] = warning
    #     if domain:
    #         res['domain'] = domain
    #     return res

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    # #THIS IS AN INHERITED FUNCTION FROM SALE.ORDER MODEL/TABLE/CLASS

    @api.multi
    def _create_invoice(self, context):
        print('CREATING INVOICE...')
        # date_invoice = context['date_invoice']
        # date_invoice = date_invoice
        # date_due = context['date_due']
        # date_due = date_due
        collection = self.env['credit.loan.collection'].sudo().search([('id','=',context.get('collection'))])
        type = context['type'] #in_invoice | out_invoice | in_refund | out_refund
        # amount = context['amount']
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.opportunity_id.product_id.id:
            account_id = self.fiscal_position_id.map_account(
                self.opportunity_id.product_id.property_account_income_id or self.opportunity_id.product_id.categ_id.property_account_income_categ_id).id
            print('THERE IS AN ACCOUNT ID')
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = self.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.opportunity_id.product_id.name,))

        # if self.amount <= 0.00:
        #     raise UserError(_('The value of the down payment amount must be positive.'))
        # context = {'lang': self.partner_id.lang}
        # if self.advance_payment_method == 'percentage':
        #     amount = order.amount_untaxed * self.amount / 100
        #     name = _("Down payment of %s%%") % (self.amount,)
        # else:
        #     amount = self.amount
        name = _('Down Payment')
        # del context
        taxes = self.opportunity_id.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
        if self.fiscal_position_id and taxes:
            tax_ids = self.fiscal_position_id.map_tax(taxes, self.opportunity_id.product_id, self.partner_shipping_id).ids
        else:
            tax_ids = taxes.ids
        print('TAXES PASSED')
        invoice = inv_obj.create({
            'name': self.client_order_ref or self.name,
            'origin': self.name,
            'type': type,
            'reference': False,
            'account_id': collection.application_id.company_id.partner_id.property_account_receivable_id.id,
            'partner_id': collection.partner_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'invoice_line_ids': context['invoice_line_ids'],
            'payment_term_id': self.payment_term_id.id,
            #TODO: SET FISCAL POSITION HERE
            # 'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'company_id': collection.partner_id.company_id.id,
            'comment': self.note,
            'collection_id':collection.id,
            'currency_id': collection.partner_id.company_id.currency_id.id,
            # 'date_validate':date_invoice
        })
        print('INVOICE CREATED')
        invoice.compute_taxes()
        print('TAXES COMPUTED')
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': self},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        print('INVOICE MESSAGE POST')
        return invoice

    name = fields.Char()
    collection_id = fields.Many2one('credit.loan.collection', 'Collection')
    order_id = fields.Many2one('sale.order', 'Sales Order', related='collection_id.order_id')
    # order_line_id = fields.Many2one('sale.order.line', 'Related Document')
    invoice_id = fields.Many2one('account.invoice', 'Related Document')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    currency_id = fields.Many2one('res.currency', related='collection_id.currency_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('paid', 'Paid'),
                               ('cancel','Cancelled')])
    date = fields.Date()
    principal = fields.Monetary('Principal')
    amortization = fields.Monetary('Amortization')
    interest = fields.Monetary('Interest')
    surcharge = fields.Monetary('Surcharge')
    penalty = fields.Monetary('Penalty')

class CollectionLine(models.Model):
    _name = 'credit.loan.collection.line'

    name = fields.Char()
    collection_id = fields.Many2one('credit.loan.collection', 'Collection')
    application_id = fields.Many2one('crm.lead', related='collection_id.application_id')
    order_id = fields.Many2one('sale.order', 'Sales Order', related='collection_id.order_id')
    # order_line_id = fields.Many2one('sale.order.line', 'Related Document')
    invoice_id = fields.Many2one('account.invoice', 'Related Document')
    date_created = fields.Datetime('Date Created', default=fields.Datetime.now())
    currency_id = fields.Many2one('res.currency', related='collection_id.currency_id')
    status = fields.Selection([('draft', 'Draft'),
                               ('active', 'Active'),
                               ('paid', 'Paid'),
                               ('cancel','Cancelled')])
    date = fields.Date()
    principal = fields.Monetary('Principal')
    amortization = fields.Monetary('Amortization')
    interest = fields.Monetary('Interest')
    surcharge = fields.Monetary('Surcharge')
    penalty = fields.Monetary('Penalty')

class Collection(models.Model):
    _inherit = 'credit.loan.collection'

    loan_amount = fields.Monetary(compute='_get_loan_amount')
    interest = fields.Monetary(compute='_compute_amortization')
    surcharge = fields.Monetary(compute='_compute_amortization')
    penalty = fields.Monetary(compute='_compute_amortization')
    principal = fields.Monetary(compute='_compute_amortization')
    amortization = fields.Monetary(compute='_compute_amortization')
    order_id = fields.Many2one('sale.order', 'Sales Order')
    invoice_ids = fields.One2many('account.invoice', 'collection_id')
    collection_line_ids = fields.One2many('credit.loan.collection.line','collection_id','Collection Line')

    @api.depends('application_id')
    def _get_loan_amount(self):
        if self.product_id.loanclass == 'individual':
            self.loan_amount = self.application_id.loan_amount
        elif self.product_id.loanclass == 'group':
            self.loan_amount = self.application_id.group_id.loan_amount

    @api.depends('interest_id', 'surcharge_id', 'penalty_id', 'application_id', 'product_id')
    def _compute_amortization(self):
        for rec in self:
            principal = 0
            term = len(rec.application_id.product_id.payment_term.line_ids) - 1
            print(term)
            if rec.product_id.loanclass == 'individual':
                loan_amount = rec.application_id.loan_amount
                principal = loan_amount / term
            elif rec.product_id.loanclass == 'group':
                loan_amount = rec.application_id.group_id.loan_amount
                principal = (loan_amount / term) / rec.application_id.member_count
            rec.interest = (principal * rec.interest_id.rate) + rec.interest_id.amount
            rec.surcharge = (principal * rec.surcharge_id.rate) + rec.surcharge_id.amount
            rec.penalty = (principal * rec.penalty_id.rate) + rec.penalty_id.amount
            rec.principal = principal
            rec.amortization = (principal + rec.interest) - rec.surcharge

    @api.model
    def create(self, values):
        application = self.env['crm.lead'].sudo().search([('id', '=', values['application_id'])])
        if not application.product_id.payment_term:
            raise UserError(_('Configure Payment Term for ' + application.product_id.name))
        collection = super(Collection, self).create(values)
        existing_collection = self.env['credit.loan.collection'].sudo().search([('status','=','active'),('id','=',collection.id)])
        if existing_collection:
            existing_collection.write(values)
            return True

        # THIS LOOPS THROUGH THE CALCULATED NUMBER OF MONTHS
        for line in range(0, len(application.product_id.payment_term.line_ids) - 1):
            try:
                # #THIS LOOP CREATES LIST ITEMS FOR SALE.ORDER AND COLLECTION MODELS/TABLE
                # self.env['sale.order.line'].sudo().create({
                #     'order_id': order.id,
                #     'name': order.opportunity_id.product_id.name,
                #     'product_id': order.opportunity_id.product_id.id,
                #     'price_unit': collection.amortization
                # })

                print('CREATING COLLECTION LINES...', line)

                self.env['credit.loan.collection.line'].sudo().create({
                    'collection_id': collection.id,
                    'status': 'draft',
                    'principal': collection.principal,
                    'amortization': collection.amortization,
                    'interest': collection.interest,
                    'surcharge': collection.surcharge,
                    'penalty': collection.penalty
                })

                print('COLLECTION DONE!')
            except Exception as e:
                raise UserError(_(str(e)))

        # collection.order_id = order
        # THIS CALLS ACTION_CONFIRM() FUNCTION IN SALE.ORDER MODEL/TABLE/CLASS
        # order.action_confirm()
        # CREATE INVOICE
        # self.env['sale.advance.payment.inv'].sudo().create_invoices(order.id)
        # UPON RETURN, THE COLLECTION IS CREATED.
        return collection

class LoanApplication(models.Model):
    _inherit = 'crm.lead'

    status = fields.Selection(string='Status', selection_add=[('disburse', 'Disbursement'), ('collection', 'Collection')], required=True, track_visibility='onchange')
    # collection_ids = fields.One2many('credit.loan.collection', 'application_id', 'Loan Collection')
    collection_line_ids = fields.One2many('credit.loan.collection.line', 'application_id')
    date_approved = fields.Datetime('Date Approved')
    date_released = fields.Datetime('Date Released')

    interest = fields.Monetary(compute="summary_footer")
    surcharge = fields.Monetary(compute="summary_footer")
    penalty = fields.Monetary(compute="summary_footer")
    principal = fields.Monetary(compute="summary_footer")
    amortization = fields.Monetary(compute="summary_footer",  string="Total Amortization")

    #PRODUCT DETAILS

    loanclass = fields.Selection(related='product_id.loanclass')
    min = fields.Monetary(related='product_id.min')
    max = fields.Monetary(related='product_id.max')
    grace_period_principal = fields.Monetary(related='product_id.grace_period_principal')
    grace_period_interest = fields.Monetary(related='product_id.grace_period_interest')
    payment_term = fields.Many2one('account.payment.term', related='product_id.payment_term')

    @api.depends('collection_line_ids')
    def summary_footer(self):
        interest = []
        surcharge = []
        penalty = []
        principal = []
        amortization = []
        for rec in self:
            for col in rec.collection_line_ids:
                interest.append(col.interest)
                surcharge.append(col.surcharge)
                penalty.append(col.penalty)
                principal.append(col.principal)
                amortization.append(col.amortization)
            rec.interest = sum(interest)
            rec.surcharge = sum(surcharge)
            rec.penalty = sum(penalty)
            rec.principal = sum(principal)
            rec.amortization = sum(amortization)

    @api.multi
    def release_loan(self):
        if self.stage_id.id != self.env['crm.stage'].sudo().search([('name', '=', 'Approved')]).id:
            raise UserError(_("The application must be approved first!"))
        self.generate_collection_line()
        try:
            # branchless group: current application is skipped when group loan
            print('GROUP:', [application.partner_id.display_name for application in self.group_id.application_ids])
            for application in self.group_id.application_ids:
                if application.id != self.id:
                    application.generate_collection_line()
        except:
            pass
        return True

    @api.multi
    def generate_collection_line(self):
        print('GENERATING COLLECTION DETAILS FOR:', self.partner_id.display_name)
        date_released = fields.Datetime.now()
        self.date_released = date_released
        order = self.env['sale.order'].sudo().search([('opportunity_id.id', '=', self.id)])
        print('DATE RELEASED:', date_released)
        for i, line in enumerate(self.collection_line_ids):
            print('UPDATING COLLECTION LINE...', line.id)
            print('MONTH INDEX:', i)
            # try:
                # date_invoice = date_released + relativedelta(months=i)
                # date_due = date_released + relativedelta(months=i + 1)
                # context = {
                #     "payment_term_id": order.payment_term_id.id,
                #     "date_invoice": date_invoice.date(),
                #     "date_due": date_due.date(),
                #     "amount": line.amortization,
                # }

                # print('CREATING INVOICE...')
                # invoice = line.order_id._create_invoice(context)
                #
                # print('UPDATING COLLECTION LINES...')
                # line.write({
                #     'invoice_id': invoice.id,
                #     'date': date_released + relativedelta(months=i + 1),
                #     'status': 'active',
                # })

                # TODO: CHRON THIS
                # print('UPDATING INVOICE...')
                # invoice.action_invoice_open()
            # except Exception as e:
            #     print(str(e))
            #     raise UserError(_('ERROR: Please contact your administrator immediately. ' + str(e)))
        order.sudo().write({
            'invoice_status': 'invoiced'
        })
        return self.create_journal()

    @api.multi
    def generate_loan_proceed(self):
        #CHANGE LOAN DETAILS TO LOAN PROCEED: NOT EDITABLE
        try:
            order = self.order_ids.search([('opportunity_id', '=', self.id)], limit=1)
            collection = self.env['credit.loan.collection'].sudo().search([('application_id.id', '=', self.id)])
            if not order:
                # TODO: if first SO: add processing fee
                # WELL IT DEPENDS, IF THE CLIENT DECIDES TO NTEGRATE NON-COLLECTION PAYMENT TO THE SAME INVOICE./n
                # OTHERWISE, ADD ANOTHER FUNCTION FOR A SEPARATE INVOICE/COLLECTION.
                # THIS LINE CALLS THE CREATE FUNCTION FOR SALE.ORDER MODEL/TABLE
                order = self.env['sale.order'].sudo().create({
                    'opportunity_id': self.id,
                    'partner_id': self.partner_id.id,
                    'partner_invoice_id': self.partner_id.id,
                    'partner_shipping_id': self.partner_id.id,
                    'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
                    'company_id': self.branch_id.company_id.id,
                    'payment_term_id': self.product_id.payment_term.id
                })
                # SALE.ORDER.LINE
                loan_line = self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'name': self.product_id.name,
                    'product_id': self.product_id.id,
                    'price_unit': self.loan_amount
                })
                fee_line = self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'name': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).name,
                    'product_id': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).id,
                    'price_unit': (self.env['product.template'].sudo().search(
                        [('name', '=', 'Processing Fee')]).standard_price) * (
                                          len(self.product_id.payment_term.line_ids) - 1)
                })
                interest_line = self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'name': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).name,
                    'product_id': self.env['product.template'].sudo().search([('name', '=', 'Processing Fee')]).id,
                    'price_unit': (self.product_id.interest_id.rate * 100) * (
                            len(self.product_id.payment_term.line_ids) - 1)
                })
                # date_invoice = date_released + relativedelta(months=i)
                # date_due = date_released + relativedelta(months=i + 1)
                cash_payment_context = {
                    # "payment_term_id": order.payment_term_id.id,
                    # "date_invoice": date_invoice.date(),
                    # "date_due": date_due.date(),
                    # "amount": line.amortization,
                    'invoice_line_ids': [(0, 0, {
                        'name': _('Loan Disbursement'),
                        'origin': order.name,
                        'account_id': loan_line.product_id.categ_id.property_account_receivable_categ_id.id,
                        'price_unit': loan_line.price_unit,
                        'quantity': 1.0,
                        'discount': 0.0,
                        'uom_id': loan_line.product_id.uom_id.id,
                        'product_id': loan_line.product_id.id,
                        # 'sale_line_ids': [(6, 0, [so_line.id])],
                        # 'invoice_line_tax_ids': [(6, 0, tax_ids)],
                        # 'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                        # 'account_analytic_id': self.analytic_account_id.id or False,
                    })],
                    'type': 'in_invoice',
                    'collection': collection.id
                }
                receivable_context = {
                    # "payment_term_id": order.payment_term_id.id,
                    # "date_invoice": date_invoice.date(),
                    # "date_due": date_due.date(),
                    # "amount": line.amortization,
                    'invoice_line_ids': [(0, 0, {
                        'name': _('Interest'),
                        'origin': order.name,
                        'account_id': loan_line.product_id.categ_id.property_account_income_categ_id.id,
                        'price_unit': interest_line.price_unit,
                        'quantity': 1.0,
                        'discount': 0.0,
                        'uom_id': interest_line.product_id.uom_id.id,
                        'product_id': interest_line.product_id.id,
                        # 'sale_line_ids': [(6, 0, [so_line.id])],
                        # 'invoice_line_tax_ids': [(6, 0, tax_ids)],
                        # 'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                        # 'account_analytic_id': self.analytic_account_id.id or False,
                    }), (0, 0, {
                        'name': _('Processing Fee'),
                        'origin': order.name,
                        'account_id': loan_line.product_id.categ_id.property_account_receivable_categ_id.id,
                        'price_unit': fee_line.price_unit,
                        'quantity': 1.0,
                        'discount': 0.0,
                        'uom_id': fee_line.product_id.uom_id.id,
                        'product_id': fee_line.product_id.id,
                        # 'sale_line_ids': [(6, 0, [so_line.id])],
                        # 'invoice_line_tax_ids': [(6, 0, tax_ids)],
                        # 'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                        # 'account_analytic_id': self.analytic_account_id.id or False,
                    })],
                    'type': 'out_invoice',
                    # 'journal_id': self.env['account.journal'].sudo().search([('company_id','=',self.company_id.id),('type','=','sale')]).id,
                    'collection': collection.id
                }

                order._create_invoice(cash_payment_context)
                order._create_invoice(receivable_context)

                self.sudo().write({
                    'stage_id': self.env['crm.stage'].sudo().search([('name', '=', 'Loan Collection')], limit=1).id
                })

                if self.status == 'passed':
                    self.status = 'disburse'

        except Exception as e:
            print('LOAN DETAILS UNSUCCESSFULLY APPROVED', str(e))
            pass

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

class ChequeDetail(models.Model):
    _name = 'credit.loan.cheque.detail'

    name = fields.Char()